"""Resolve spell casts from character sheets."""

from __future__ import annotations

import json
import random
import sqlite3
from typing import Any

from tomb_gm.domain.character import ability_modifier
from tomb_gm.domain.combat_sheet import find_combatant, target_ac_from_monster
from tomb_gm.rules.bridge import roll_d20, saving_throw
from tomb_gm.services.content import ContentService
from tomb_gm.services.simulation.rolls import perform_attack_roll


def cast_spell(
    conn: sqlite3.Connection,
    log_event,
    *,
    content_root,
    campaign_slug: str,
    character_id: str,
    spell_id: str,
    session_id: str | None,
    target_id: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found: {character_id}"}

    sheet = json.loads(row["sheet_json"])
    content = ContentService(content_root)
    spell = content.load_spell(spell_id)
    if not spell:
        return {"ok": False, "error": f"Unknown spell: {spell_id}"}

    mp_cost = int(spell.get("mpCost", 1))
    mp = sheet.setdefault("mp", {"current": 0, "max": 0})
    if int(mp.get("current", 0)) < mp_cost:
        return {
            "ok": False,
            "error": "insufficient_mp",
            "need": mp_cost,
            "have": mp.get("current"),
        }

    mp["current"] = int(mp["current"]) - mp_cost
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), character_id, campaign_slug),
    )
    conn.commit()

    rng = random.Random(seed) if seed is not None else random.Random()
    attrs = sheet.get("attributes", {})
    int_mod = ability_modifier(int(attrs.get("INT", 10)))
    spi_mod = ability_modifier(int(attrs.get("SPI", 10)))
    result: dict[str, Any] = {
        "ok": True,
        "spell_id": spell_id,
        "displayName": spell.get("displayName"),
        "mp_spent": mp_cost,
        "mp_remaining": mp["current"],
    }

    attack = spell.get("attack")
    if attack and target_id and session_id:
        combatant = find_combatant(conn, session_id, target_id)
        if not combatant:
            return {"ok": False, "error": f"target not in combat: {target_id}"}
        ac = target_ac_from_monster(content, combatant)
        tier = int(sheet.get("classTier", 1))
        pb = min(4, 2 + max(0, tier - 1))
        roll = perform_attack_roll(
            conn,
            log_event,
            session_id=session_id,
            ability_mod=int_mod,
            pb=pb,
            skill_level=1,
            target_ac=ac,
            weapon_damage=str(attack.get("damage", "1d6")),
            ability_damage_mod=int_mod,
            reason=f"{spell_id} vs {target_id}",
            seed=seed,
        )
        result["attack"] = roll
        return result

    save_block = spell.get("save")
    if save_block:
        dc = int(save_block.get("dc", 12))
        ability_key = str(save_block.get("ability", "STA")).upper()
        mod = ability_modifier(int(attrs.get(ability_key, 10)))
        natural = roll_d20(rng)
        success = saving_throw(
            natural=natural,
            ability_mod=mod,
            pb=0,
            magical_defense_bonus=0,
            dc=dc,
        )
        result["save"] = {
            "natural": natural,
            "total": natural + mod,
            "dc": dc,
            "success": success,
        }

    if spell.get("effect"):
        result["effect"] = spell["effect"]

    log_event(
        conn,
        session_id,
        "spell.cast",
        {
            "character_id": character_id,
            "spell_id": spell_id,
            "target_id": target_id,
            "result": {k: v for k, v in result.items() if k != "ok"},
        },
    )
    return result
