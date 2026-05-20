"""Resolve spell casts from character sheets."""

from __future__ import annotations

import json
import random
import sqlite3
from typing import Any

from tomb_gm.domain.combat_sheet import find_combatant, target_ac_from_monster
from tomb_gm.services.content import ContentService
from tomb_gm.services.simulation.rolls import perform_attack_roll
from tomb_gm.services.simulation.combat import apply_damage_to_combatant
from tomb_gm.services.simulation.spell_service import (
    SpellError,
    apply_heal,
    casting_mod,
    effective_mp_cost,
    ensure_spell_fields,
    proficiency_bonus,
    record_cast,
    resolve_save_vs_caster_dc,
    roll_spell_damage,
    spell_attack_bonus,
    spell_save_dc,
    tradition_for_spell,
    validate_cast,
)


def _spellcasting_level(sheet: dict) -> int:
    for entry in sheet.get("skills", []):
        if entry.get("skillId") == "spellcasting":
            return int(entry.get("level", 1))
    return 1


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
    ensure_spell_fields(sheet)
    content = ContentService(content_root)
    spell = content.load_spell(spell_id)
    if not spell:
        return {"ok": False, "error": f"Unknown spell: {spell_id}"}

    try:
        validate_cast(sheet, spell, spell_id)
    except SpellError as exc:
        return {"ok": False, "error": str(exc)}

    mp_cost = effective_mp_cost(sheet, spell)
    mp = sheet.setdefault("mp", {"current": 0, "max": 0})
    mp["current"] = int(mp["current"]) - mp_cost

    rng = random.Random(seed) if seed is not None else random.Random()
    trad = tradition_for_spell(spell, content)
    dc = spell_save_dc(sheet, spell, content)
    cast_mod = casting_mod(sheet, trad)
    result: dict[str, Any] = {
        "ok": True,
        "spell_id": spell_id,
        "displayName": spell.get("displayName"),
        "tradition": trad,
        "spell_save_dc": dc,
        "mp_spent": mp_cost,
        "mp_remaining": mp["current"],
    }

    effect_type = spell.get("effectType", "utility")

    if effect_type == "heal" or spell.get("heal"):
        healed = apply_heal(sheet, spell, rng)
        result["heal"] = {"amount": healed, "hp_current": sheet["hp"]["current"]}

    attack = spell.get("attack")
    if effect_type == "attack" and attack and target_id and session_id:
        combatant = find_combatant(conn, session_id, target_id)
        if not combatant:
            return {"ok": False, "error": f"target not in combat: {target_id}"}
        ac = target_ac_from_monster(content, combatant)
        roll = perform_attack_roll(
            conn,
            log_event,
            session_id=session_id,
            ability_mod=cast_mod,
            pb=proficiency_bonus(sheet),
            skill_level=_spellcasting_level(sheet),
            target_ac=ac,
            weapon_damage=str(attack.get("damage", "1d6")),
            ability_damage_mod=cast_mod,
            reason=f"{spell_id} vs {target_id}",
            seed=seed,
        )
        roll["spell_attack_total_bonus"] = spell_attack_bonus(sheet, spell, content)
        result["attack"] = roll
        if roll.get("hit"):
            dmg_total = int(roll.get("damage") or 0)
            if dmg_total:
                damage_result = apply_damage_to_combatant(
                    conn,
                    session_id,
                    target_id,
                    dmg_total,
                    campaign_slug=campaign_slug,
                )
                result["damage_applied"] = damage_result

    save_block = spell.get("save")
    if save_block and target_id and session_id:
        combatant = find_combatant(conn, session_id, target_id)
        defender_sheet = None
        defender_monster = combatant
        if combatant and combatant.get("kind") == "pc":
            prow = conn.execute(
                "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
                (target_id, campaign_slug),
            ).fetchone()
            if prow:
                defender_sheet = json.loads(prow["sheet_json"])
                ensure_spell_fields(defender_sheet)
                defender_monster = None
        save_result = resolve_save_vs_caster_dc(
            defender_sheet=defender_sheet,
            defender_monster=defender_monster,
            dc=dc,
            save_ability=str(save_block.get("ability", "STA")).upper(),
            rng=rng,
        )
        result["save"] = save_result
        dmg_spec = spell.get("damage")
        if dmg_spec:
            if not save_result.get("success"):
                result["damage"] = roll_spell_damage(str(dmg_spec.get("dice", "1d6")), rng)
            elif dmg_spec.get("halfOnSave"):
                result["damage"] = roll_spell_damage(str(dmg_spec.get("dice", "1d6")), rng, half=True)

    if spell.get("effect"):
        result["effect"] = spell["effect"]

    record_cast(sheet, spell)
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), character_id, campaign_slug),
    )
    conn.commit()

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
