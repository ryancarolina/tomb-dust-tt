"""Delver death: corpse placement and run termination."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tomb_gm.domain.inventory import apply_loot_to_sheet, empty_inventory, ensure_normalized, loot_snapshot


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _corpse_loot_snapshot(sheet: dict[str, Any]) -> dict[str, Any]:
    return loot_snapshot(sheet)


def spawn_world_corpse(
    conn: sqlite3.Connection,
    *,
    sheet: dict[str, Any],
    character_id: str,
    site_address: str | None = None,
    room_id: str | None = None,
    cell_address: str | None = None,
    cause: str = "slain in the delve",
) -> dict[str, Any]:
    name = sheet.get("displayName", character_id)
    corpse_id = f"corpse-{character_id}-{uuid.uuid4().hex[:8]}"
    loot = _corpse_loot_snapshot(sheet)
    description = f"The body of {name}, {cause}. Gear still on the corpse."
    conn.execute(
        """INSERT INTO world_corpses
           (id, site_address, cell_address, room_id, display_name, description, state, loot_json, data_json, died_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            corpse_id,
            site_address,
            cell_address,
            room_id,
            f"{name}'s remains",
            description,
            "pristine",
            json.dumps(loot),
            json.dumps({"character_id": character_id, "cause": cause}),
            _now(),
        ),
    )
    conn.commit()
    return {
        "ok": True,
        "corpse_id": corpse_id,
        "display_name": f"{name}'s remains",
        "site_address": site_address,
        "room_id": room_id,
        "cell_address": cell_address,
        "loot": loot,
    }


def get_corpses_for_room(site_address: str, room_id: str, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM world_corpses WHERE site_address = ? AND room_id = ? AND state != 'destroyed'",
        (site_address, room_id),
    ).fetchall()
    return [dict(r) for r in rows]


def get_corpses_for_cell(cell_address: str, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM world_corpses WHERE cell_address = ? AND state != 'destroyed'",
        (cell_address,),
    ).fetchall()
    return [dict(r) for r in rows]


def corpses_as_features(corpses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for c in corpses:
        features.append(
            {
                "id": c["id"],
                "feature_type": "delver_corpse",
                "display_name": c["display_name"],
                "description": c.get("description") or "A fallen delver.",
                "state": c.get("state", "pristine"),
                "data_json": c.get("data_json", "{}"),
            }
        )
    return features


def process_delver_death(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    session_id: str,
    cause: str = "slain in the delve",
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found: {character_id}"}

    sheet = json.loads(row["sheet_json"])
    ensure_normalized(sheet)
    ps = conn.execute(
        "SELECT address, mode, site_id, dungeon_room_id FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()

    site_address = None
    room_id = None
    cell_address = None
    if ps:
        if ps["mode"] == "dungeon" and ps["site_id"]:
            site_address = ps["site_id"]
            room_id = ps["dungeon_room_id"]
        else:
            cell_address = ps["address"]

    conn.execute(
        "UPDATE characters SET alive = 0, slot = NULL WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    )

    cleared_sheet = {
        **sheet,
        "goldGp": 0,
        "inventory": empty_inventory(),
    }
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(cleared_sheet), character_id, campaign_slug),
    )
    conn.commit()

    corpse = spawn_world_corpse(
        conn,
        sheet=sheet,
        character_id=character_id,
        site_address=site_address,
        room_id=room_id,
        cell_address=cell_address,
        cause=cause,
    )
    return {
        "ok": True,
        "dead_character_id": character_id,
        "corpse": corpse,
        "run_ended": True,
        "new_game_required": True,
    }


def reconcile_save_vitals(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    session_id: str,
    seed: int | None = None,
) -> dict[str, Any]:
    """Fix legacy saves at 0 HP without Downed/Dying; finalize deaths after ended fights."""
    from tomb_gm.domain.combat_player import DOWNED, DYING, STABLE, apply_zero_hp_consciousness

    combat_active = bool(
        conn.execute(
            "SELECT 1 FROM combat_state WHERE session_id = ? AND active = 1",
            (session_id,),
        ).fetchone()
    )

    rows = conn.execute(
        "SELECT id, sheet_json FROM characters "
        "WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1",
        (campaign_slug,),
    ).fetchall()

    deaths: list[str] = []
    updated: list[dict[str, Any]] = []
    death_results: list[dict[str, Any]] = []

    for row in rows:
        sheet = json.loads(row["sheet_json"])
        ensure_normalized(sheet)
        hp = int(sheet.get("hp", {}).get("current", 0))
        conds = list(sheet.get("conditions") or [])
        char_id = row["id"]

        if hp > 0:
            continue
        if any(c in conds for c in (DOWNED, DYING, STABLE)):
            if DYING in conds and not combat_active:
                deaths.append(char_id)
            else:
                updated.append({"character_id": char_id, "conditions": conds, "hp": hp})
            continue

        if combat_active:
            result = apply_zero_hp_consciousness(
                conn,
                campaign_slug=campaign_slug,
                character_id=char_id,
                session_id=session_id,
                seed=seed,
            )
            updated.append(result)
        else:
            deaths.append(char_id)

    for char_id in deaths:
        death_results.append(
            process_delver_death(
                conn,
                campaign_slug=campaign_slug,
                character_id=char_id,
                session_id=session_id,
                cause="bled out after the fight",
            )
        )

    return {
        "ok": True,
        "combat_active": combat_active,
        "deaths": deaths,
        "death_results": death_results,
        "updated": updated,
        "run_ended": bool(deaths),
    }


def process_defeat_deaths(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    session_id: str,
    cause: str = "slain in the delve",
) -> list[dict[str, Any]]:
    """After combat defeat, finalize deaths for PCs at 0 HP who are not Downed."""
    from tomb_gm.domain.combat_player import DOWNED

    rows = conn.execute(
        "SELECT id, sheet_json FROM characters "
        "WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1",
        (campaign_slug,),
    ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        sheet = json.loads(row["sheet_json"])
        ensure_normalized(sheet)
        hp = int(sheet.get("hp", {}).get("current", 0))
        conds = list(sheet.get("conditions") or [])
        if hp <= 0 and DOWNED not in conds:
            results.append(
                process_delver_death(
                    conn,
                    campaign_slug=campaign_slug,
                    character_id=row["id"],
                    session_id=session_id,
                    cause=cause,
                )
            )
    return results


def resolve_corpse_id(conn: sqlite3.Connection, feature_id: str, *, site_address: str | None, room_id: str | None) -> str | None:
    """Resolve corpse feature id — exact match or sole corpse in room."""
    if feature_id.startswith("corpse-"):
        row = conn.execute("SELECT id FROM world_corpses WHERE id = ?", (feature_id,)).fetchone()
        return feature_id if row else None
    if site_address and room_id:
        corpses = get_corpses_for_room(site_address, room_id, conn)
        if len(corpses) == 1:
            return corpses[0]["id"]
        for c in corpses:
            if feature_id.lower() in str(c.get("display_name", "")).lower():
                return c["id"]
    return None


def loot_corpse(
    conn: sqlite3.Connection,
    *,
    corpse_id: str,
    campaign_slug: str,
    character_id: str,
    content_root: Path | None = None,
) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM world_corpses WHERE id = ?", (corpse_id,)).fetchone()
    if not row:
        return {"ok": False, "error": f"Corpse not found: {corpse_id}"}
    if row["state"] == "looted":
        return {"ok": False, "error": "Corpse already looted"}

    loot = json.loads(row["loot_json"] or "{}")
    char_row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ? AND alive = 1",
        (character_id, campaign_slug),
    ).fetchone()
    if not char_row:
        return {"ok": False, "error": f"Living character not found: {character_id}"}

    from tomb_gm.services.content import ContentService

    sheet = json.loads(char_row["sheet_json"])
    if content_root is None:
        from tomb_gm.config import load_config, resolve_workspace

        content_root = load_config(resolve_workspace(None)).content_root
    content = ContentService(content_root)
    lookup = content.items_lookup()
    transferred = apply_loot_to_sheet(sheet, loot, item_lookup=lookup)
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), character_id, campaign_slug),
    )
    conn.execute(
        "UPDATE world_corpses SET state = 'looted', loot_json = ? WHERE id = ?",
        (json.dumps({"goldGp": 0, "pack": [], "looted_by": character_id}), corpse_id),
    )
    conn.commit()
    return {
        "ok": True,
        "corpse_id": corpse_id,
        "looted_by": character_id,
        "transferred": transferred,
        "new_gold_gp": sheet["goldGp"],
    }
