"""Resolve combat rolls from character sheets."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tomb_gm.domain.character import ability_modifier
from tomb_gm.domain.inventory import compute_ac, ensure_normalized, get_pack, main_weapon_id
from tomb_gm.services.content import ContentService
from tomb_gm.services.simulation.combat import pick_stat_block


def load_character_sheet(
    conn: sqlite3.Connection, campaign_slug: str, character_id: str
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise ValueError(f"Character not found: {character_id}")
    sheet = json.loads(row["sheet_json"])
    ensure_normalized(sheet)
    return sheet


def sheet_ac(sheet: dict[str, Any], *, content_root: Path | None = None, flat_footed: bool = False) -> int:
    lookup: dict[str, Any] = {}
    if content_root:
        lookup = ContentService(content_root).items_lookup()
    return compute_ac(sheet, item_lookup=lookup, flat_footed=flat_footed)


def attack_modifiers_from_sheet(
    sheet: dict[str, Any],
    *,
    weapon_id: str | None = None,
    content_root: Path | None = None,
) -> dict[str, int]:
    ensure_normalized(sheet)
    attrs = sheet.get("attributes", {})
    class_tier = int(sheet.get("classTier", 1))
    pb = min(4, 2 + max(0, class_tier - 1))
    str_mod = ability_modifier(int(attrs.get("STR", 10)))
    agi_mod = ability_modifier(int(attrs.get("AGI", 10)))
    skills = {s["skillId"]: int(s["level"]) for s in sheet.get("skills", [])}
    skill_level = 1

    pack = get_pack(sheet)
    resolved_weapon = weapon_id or main_weapon_id(pack)

    weapon_data: dict[str, Any] | None = None
    if resolved_weapon and content_root:
        weapon_data = ContentService(content_root).load_weapon(resolved_weapon)

    skill_id: str | None = None
    if weapon_data:
        skill_id = weapon_data.get("skillId")
        damage = str(weapon_data.get("damage", "1d8"))
        ability = str(weapon_data.get("ability", "STR")).upper()
        if ability == "AGI":
            ability_mod = agi_mod
        elif ability == "STR":
            ability_mod = str_mod
        else:
            ability_mod = max(str_mod, agi_mod)
    else:
        damage = "1d8"
        ability_mod = max(str_mod, agi_mod)

    if skill_id and skill_id in skills:
        skill_level = skills[skill_id]
    elif resolved_weapon:
        for sid in ("swordsmanship", "archery", "unarmed-combat"):
            if sid in skills:
                skill_level = skills[sid]
                break
    elif any(i.get("kind") == "weapon" for i in pack):
        damage = "1d6"

    return {
        "ability_mod": ability_mod,
        "pb": pb,
        "skill_level": skill_level,
        "skill_id": skill_id,
        "ability_damage_mod": ability_mod,
        "weapon_damage": damage,
        "weapon_id": resolved_weapon,
    }


def find_combatant(
    conn: sqlite3.Connection, session_id: str, combatant_id: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT combatants_json FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return None
    combatants = json.loads(row["combatants_json"] or "[]")
    for c in combatants:
        if c["id"] == combatant_id:
            return c
    return None


def target_ac_from_monster(content: ContentService, combatant: dict[str, Any]) -> int:
    if combatant.get("kind") != "monster":
        return int(combatant.get("ac", 10))
    mid = combatant.get("monsterId")
    data, blocker = content.load_monster(mid)
    if blocker or not data:
        return int(combatant.get("ac", 10))
    block = pick_stat_block(data, combatant.get("tier"))
    return int(block.get("ac", 10))
