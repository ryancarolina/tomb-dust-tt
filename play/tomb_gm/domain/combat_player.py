"""Player character integration with combat: HP, downed/dying, death, Fortune."""

from __future__ import annotations

import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from tomb_gm.domain.character import ability_modifier

DYING = "Dying"
DOWNED = "Downed"
STABLE = "Stable"
CONSCIOUSNESS_DC = 12


def _load_sheet_row(conn: sqlite3.Connection, campaign: str, character_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT sheet_json, slot, alive FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign),
    ).fetchone()
    if not row:
        raise ValueError(f"Character not found: {character_id}")
    return row


def save_sheet(conn: sqlite3.Connection, campaign: str, character_id: str, sheet: dict[str, Any]) -> None:
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), character_id, campaign),
    )
    conn.commit()


def spawn_roster_combatants(
    conn: sqlite3.Connection,
    campaign_slug: str,
    *,
    rng,
    content_root=None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from tomb_gm.rules.bridge import initiative_total, roll_d20
    from tomb_gm.domain.combat_sheet import sheet_ac
    from pathlib import Path

    root = Path(content_root) if content_root else None
    rows = conn.execute(
        "SELECT id, sheet_json FROM characters "
        "WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 ORDER BY slot",
        (campaign_slug,),
    ).fetchall()
    combatants: list[dict[str, Any]] = []
    initiative: list[dict[str, Any]] = []
    for row in rows:
        sheet = json.loads(row["sheet_json"])
        from tomb_gm.domain.inventory import ensure_normalized

        ensure_normalized(sheet)
        cid = row["id"]
        attrs = sheet.get("attributes", {})
        agi_mod = ability_modifier(int(attrs.get("AGI", 10)))
        hp = sheet.get("hp", {})
        ac = sheet_ac(sheet, content_root=root) if root else int(sheet.get("ac", 10))
        combatants.append(
            {
                "id": cid,
                "kind": "pc",
                "characterId": cid,
                "slot": sheet.get("slot"),
                "displayName": sheet.get("displayName", cid),
                "hp": int(hp.get("current", 0)),
                "maxHp": int(hp.get("max", 1)),
                "ac": ac,
                "conditions": list(sheet.get("conditions") or []),
            }
        )
        nat = roll_d20(rng)
        init = initiative_total(natural=nat, agi_mod=agi_mod)
        initiative.append(
            {
                "id": cid,
                "name": sheet.get("displayName", cid),
                "natural": nat,
                "initiative": init,
            }
        )
    initiative.sort(key=lambda r: r["initiative"], reverse=True)
    return combatants, initiative


def _mark_pc_dead(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    sheet: dict[str, Any],
    reason: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    conditions = [c for c in (sheet.get("conditions") or []) if c not in (DYING, DOWNED, STABLE)]
    sheet["conditions"] = conditions
    sheet["hp"]["current"] = 0
    save_sheet(conn, campaign_slug, character_id, sheet)
    conn.execute(
        "UPDATE characters SET alive = 0, slot = NULL WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    )
    conn.commit()
    if session_id:
        _sync_combatant_hp(conn, session_id, character_id, 0, conditions)
    return {
        "ok": True,
        "character_id": character_id,
        "hp": 0,
        "conditions": conditions,
        "died": True,
        "reason": reason,
    }


def apply_zero_hp_consciousness(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    session_id: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Apply STA save at 0 HP when no Downed/Dying state exists yet."""
    row = _load_sheet_row(conn, campaign_slug, character_id)
    if not row["alive"]:
        return {"ok": False, "error": "character already dead", "character_id": character_id}

    sheet = json.loads(row["sheet_json"])
    hp = sheet.setdefault("hp", {"current": 0, "max": 1})
    hp["current"] = 0
    conditions = list(sheet.get("conditions") or [])
    conditions = [c for c in conditions if c not in (DYING, DOWNED, STABLE)]

    from tomb_gm.rules.bridge import roll_d20

    rng = random.Random(seed) if seed is not None else random.Random()
    sta_mod = ability_modifier(int(sheet.get("attributes", {}).get("STA", 10)))
    natural = roll_d20(rng)
    save_total = natural + sta_mod
    conscious = save_total >= CONSCIOUSNESS_DC
    if conscious:
        conditions.append(DOWNED)
    else:
        conditions.append(DYING)
    sheet["conditions"] = conditions
    save_sheet(conn, campaign_slug, character_id, sheet)
    if session_id:
        _sync_combatant_hp(conn, session_id, character_id, 0, conditions)

    return {
        "ok": True,
        "character_id": character_id,
        "hp": 0,
        "conditions": conditions,
        "downed": conscious,
        "dying": not conscious,
        "consciousness_roll": {
            "natural": natural,
            "sta_mod": sta_mod,
            "total": save_total,
            "dc": CONSCIOUSNESS_DC,
            "success": conscious,
        },
    }


def resolve_pc_damage(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    damage: int,
    session_id: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Apply damage to a PC with massive trauma, 0 HP consciousness, and death rules."""
    row = _load_sheet_row(conn, campaign_slug, character_id)
    if not row["alive"]:
        return {"ok": False, "error": "character already dead", "character_id": character_id}

    sheet = json.loads(row["sheet_json"])
    conditions = list(sheet.get("conditions") or [])
    hp = sheet.setdefault("hp", {"current": 0, "max": 1})
    current = int(hp.get("current", 0))
    rng = random.Random(seed) if seed is not None else random.Random()

    if current > 0 and damage >= 3 * current:
        return _mark_pc_dead(
            conn,
            campaign_slug=campaign_slug,
            character_id=character_id,
            sheet=sheet,
            reason="massive_trauma",
            session_id=session_id,
        )

    if current <= 0 and damage > 0 and (DYING in conditions or DOWNED in conditions):
        return _mark_pc_dead(
            conn,
            campaign_slug=campaign_slug,
            character_id=character_id,
            sheet=sheet,
            reason="damage_at_zero_hp",
            session_id=session_id,
        )

    new_hp = max(0, current - damage)
    hp["current"] = new_hp

    if new_hp > 0:
        conditions = [c for c in conditions if c not in (DYING, DOWNED, STABLE)]
        sheet["conditions"] = conditions
        save_sheet(conn, campaign_slug, character_id, sheet)
        if session_id:
            _sync_combatant_hp(conn, session_id, character_id, new_hp, conditions)
        return {
            "ok": True,
            "character_id": character_id,
            "hp": new_hp,
            "max_hp": int(hp.get("max", 1)),
            "conditions": conditions,
            "died": False,
        }

    zero_result = apply_zero_hp_consciousness(
        conn,
        campaign_slug=campaign_slug,
        character_id=character_id,
        session_id=session_id,
        seed=seed,
    )
    zero_result["max_hp"] = int(hp.get("max", 1))
    zero_result["died"] = False
    return zero_result


def apply_damage_to_character(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    damage: int,
    session_id: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    return resolve_pc_damage(
        conn,
        campaign_slug=campaign_slug,
        character_id=character_id,
        damage=damage,
        session_id=session_id,
        seed=seed,
    )


def stabilize_character(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    row = _load_sheet_row(conn, campaign_slug, character_id)
    sheet = json.loads(row["sheet_json"])
    conditions = [c for c in (sheet.get("conditions") or []) if c != DYING]
    if STABLE not in conditions:
        conditions.append(STABLE)
    sheet["conditions"] = conditions
    hp = sheet.setdefault("hp", {"current": 0, "max": 1})
    hp["current"] = 0
    save_sheet(conn, campaign_slug, character_id, sheet)
    if session_id:
        _sync_combatant_hp(conn, session_id, character_id, 0, conditions)
    return {"ok": True, "character_id": character_id, "stable": True, "hp": 0}


def spend_fortune(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    amount: int = 1,
) -> dict[str, Any]:
    if amount < 1:
        raise ValueError("amount must be >= 1")
    row = _load_sheet_row(conn, campaign_slug, character_id)
    sheet = json.loads(row["sheet_json"])
    fortune = sheet.setdefault("fortune", {"current": 0, "max": 1})
    current = int(fortune.get("current", 0))
    if current < amount:
        raise ValueError(f"Insufficient Fortune: have {current}, need {amount}")
    fortune["current"] = current - amount
    save_sheet(conn, campaign_slug, character_id, sheet)
    return {
        "ok": True,
        "character_id": character_id,
        "spent": amount,
        "fortune": fortune,
    }


def apply_condition(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    condition: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    row = _load_sheet_row(conn, campaign_slug, character_id)
    sheet = json.loads(row["sheet_json"])
    conditions = list(sheet.get("conditions") or [])
    if condition not in conditions:
        conditions.append(condition)
    sheet["conditions"] = conditions
    save_sheet(conn, campaign_slug, character_id, sheet)
    if session_id:
        _sync_combatant_hp(
            conn,
            session_id,
            character_id,
            int(sheet.get("hp", {}).get("current", 0)),
            conditions,
        )
    return {"ok": True, "character_id": character_id, "conditions": conditions}


def is_pc_combat_active(combatant: dict[str, Any]) -> bool:
    """PC can still act in combat (standing or conscious Downed)."""
    if combatant.get("kind") != "pc":
        return int(combatant.get("hp", 0)) > 0
    conditions = list(combatant.get("conditions") or [])
    if DOWNED in conditions:
        return True
    return int(combatant.get("hp", 0)) > 0


def is_pc_party_down(combatant: dict[str, Any]) -> bool:
    """PC counts as down for party defeat (dead, Dying, or Stable at 0)."""
    if combatant.get("kind") != "pc":
        return False
    conditions = list(combatant.get("conditions") or [])
    if DOWNED in conditions:
        return False
    return int(combatant.get("hp", 0)) <= 0


def _sync_combatant_hp(
    conn: sqlite3.Connection,
    session_id: str,
    character_id: str,
    hp: int,
    conditions: list[str],
) -> None:
    row = conn.execute(
        "SELECT combatants_json FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return
    combatants = json.loads(row["combatants_json"] or "[]")
    for c in combatants:
        if c.get("id") == character_id:
            c["hp"] = hp
            c["conditions"] = conditions
            break
    conn.execute(
        "UPDATE combat_state SET combatants_json = ? WHERE session_id = ?",
        (json.dumps(combatants), session_id),
    )
    conn.commit()


def set_character_hp_from_combat(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    hp: int,
    conditions: list[str] | None = None,
) -> dict[str, Any]:
    row = _load_sheet_row(conn, campaign_slug, character_id)
    sheet = json.loads(row["sheet_json"])
    hp_block = sheet.setdefault("hp", {"current": 0, "max": 1})
    hp_block["current"] = max(0, hp)
    if conditions is not None:
        merged = list(conditions)
        if hp <= 0 and DYING not in merged and DOWNED not in merged and STABLE not in merged:
            merged.append(DYING)
        sheet["conditions"] = merged
    elif hp <= 0:
        conds = list(sheet.get("conditions") or [])
        if DYING not in conds and DOWNED not in conds and STABLE not in conds:
            conds.append(DYING)
        sheet["conditions"] = conds
    save_sheet(conn, campaign_slug, character_id, sheet)
    return {
        "ok": True,
        "character_id": character_id,
        "hp": hp_block["current"],
        "conditions": sheet.get("conditions", []),
    }


def sync_combatant_to_sheet(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
) -> None:
    """After combat, write combatant HP/conditions back to character sheet."""
    row = conn.execute(
        "SELECT combatants_json FROM combat_state cs "
        "JOIN sessions s ON s.id = cs.session_id "
        "WHERE s.campaign_slug = ? AND cs.active = 1",
        (campaign_slug,),
    ).fetchone()
    if not row:
        return
    combatants = json.loads(row["combatants_json"] or "[]")
    for c in combatants:
        if c.get("id") != character_id or c.get("kind") != "pc":
            continue
        sheet_row = _load_sheet_row(conn, campaign_slug, character_id)
        sheet = json.loads(sheet_row["sheet_json"])
        sheet["hp"]["current"] = int(c.get("hp", 0))
        sheet["conditions"] = list(c.get("conditions") or [])
        save_sheet(conn, campaign_slug, character_id, sheet)
        break
