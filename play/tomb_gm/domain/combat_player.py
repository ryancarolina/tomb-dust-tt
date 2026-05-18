"""Player character integration with combat: HP, dying, conditions, Fortune."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from tomb_gm.domain.character import ability_modifier

DYING = "Dying"
STABLE = "Stable"


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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from tomb_gm.rules.bridge import initiative_total, roll_d20

    rows = conn.execute(
        "SELECT id, sheet_json FROM characters "
        "WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 ORDER BY slot",
        (campaign_slug,),
    ).fetchall()
    combatants: list[dict[str, Any]] = []
    initiative: list[dict[str, Any]] = []
    for row in rows:
        sheet = json.loads(row["sheet_json"])
        cid = row["id"]
        attrs = sheet.get("attributes", {})
        agi_mod = ability_modifier(int(attrs.get("AGI", 10)))
        hp = sheet.get("hp", {})
        combatants.append(
            {
                "id": cid,
                "kind": "pc",
                "characterId": cid,
                "slot": sheet.get("slot"),
                "displayName": sheet.get("displayName", cid),
                "hp": int(hp.get("current", 0)),
                "maxHp": int(hp.get("max", 1)),
                "ac": int(sheet.get("ac", 10)),
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


def apply_damage_to_character(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    damage: int,
    session_id: str | None = None,
) -> dict[str, Any]:
    row = _load_sheet_row(conn, campaign_slug, character_id)
    sheet = json.loads(row["sheet_json"])
    conditions = list(sheet.get("conditions") or [])
    hp = sheet.setdefault("hp", {"current": 0, "max": 1})
    current = int(hp.get("current", 0))

    if DYING in conditions and damage > 0:
        sheet["alive"] = False
        save_sheet(conn, campaign_slug, character_id, sheet)
        return {
            "ok": True,
            "character_id": character_id,
            "died": True,
            "reason": "damage_while_dying",
        }

    current = max(0, current - damage)
    hp["current"] = current
    died = False
    if current <= 0 and STABLE not in conditions:
        if DYING not in conditions:
            conditions.append(DYING)
        sheet["conditions"] = conditions
    save_sheet(conn, campaign_slug, character_id, sheet)

    if session_id:
        _sync_combatant_hp(conn, session_id, character_id, current, conditions)

    return {
        "ok": True,
        "character_id": character_id,
        "hp": current,
        "max_hp": int(hp.get("max", 1)),
        "conditions": conditions,
        "dying": DYING in conditions,
        "died": died,
    }


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
        sheet["conditions"] = list(conditions)
    elif hp <= 0 and "Dying" not in (sheet.get("conditions") or []):
        conds = list(sheet.get("conditions") or [])
        if DYING not in conds and STABLE not in conds:
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
