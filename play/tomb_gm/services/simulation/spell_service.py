"""Spell casting math and resolution (canon 1.1.0)."""

from __future__ import annotations

import random
from typing import Any

from tomb_gm.domain.character import ability_modifier
from tomb_gm.rules.bridge import roll_d20, saving_throw
from tomb_gm.services.content import ContentService

from tomb_gm.rules.bridge import pb_for_tier, roll_dice, skill_bonus


class SpellError(Exception):
    pass


def _skill_level(sheet: dict, skill_id: str) -> int:
    for entry in sheet.get("skills", []):
        if entry.get("skillId") == skill_id:
            return int(entry.get("level", 1))
    return 0


def tradition_for_spell(spell: dict, content: ContentService) -> str:
    if spell.get("tradition"):
        return str(spell["tradition"])
    school_id = spell.get("school", "")
    school = content.load_school(school_id) if hasattr(content, "load_school") else None
    if school:
        return str(school.get("tradition", "arcane"))
    return "divine" if school_id == "divine" else "arcane"


def casting_mod(sheet: dict, tradition: str) -> int:
    attrs = sheet.get("attributes", {})
    key = "SPI" if tradition == "divine" else "INT"
    return ability_modifier(int(attrs.get(key, 10)))


def spellcasting_bonus(sheet: dict) -> int:
    return skill_bonus(_skill_level(sheet, "spellcasting"))


def proficiency_bonus(sheet: dict) -> int:
    tier = int(sheet.get("classTier", 1))
    return pb_for_tier(tier)


def spell_focus_bonus(sheet: dict, spell_school: str) -> int:
    if sheet.get("spellFocusSchool") == spell_school:
        return 1
    return 0


def spell_save_dc(sheet: dict, spell: dict, content: ContentService) -> int:
    trad = tradition_for_spell(spell, content)
    return (
        8
        + casting_mod(sheet, trad)
        + proficiency_bonus(sheet)
        + spellcasting_bonus(sheet)
        + spell_focus_bonus(sheet, spell.get("school", ""))
    )


def spell_attack_bonus(sheet: dict, spell: dict, content: ContentService) -> int:
    trad = tradition_for_spell(spell, content)
    return (
        casting_mod(sheet, trad)
        + proficiency_bonus(sheet)
        + spellcasting_bonus(sheet)
        + spell_focus_bonus(sheet, spell.get("school", ""))
    )


def magical_defense_bonus(sheet: dict) -> int:
    return skill_bonus(_skill_level(sheet, "magical-defense"))


def effective_mp_cost(sheet: dict, spell: dict) -> int:
    base = int(spell.get("mpCost", 1))
    if _skill_level(sheet, "spellcasting") >= 6:
        return max(1, base - 1)
    return base


def default_known_spells(base_class: str) -> list[str]:
    if base_class == "novice":
        return ["mend-light", "consecrate-ground"]
    if base_class == "apprentice":
        return ["ember-touch", "static-lash"]
    return []


def ensure_spell_fields(sheet: dict) -> bool:
    """Backfill spell sheet fields. Returns True if sheet was modified."""
    changed = False
    class_id = sheet.get("classId") or sheet.get("baseClass", "")
    if not sheet.get("knownSpells"):
        defaults = default_known_spells(class_id)
        if defaults:
            sheet["knownSpells"] = defaults
            changed = True
    for key, default in (
        ("spellSchools", []),
        ("spellFocusSchool", None),
        ("concentration", None),
        ("spellsCastTotal", 0),
        ("spellsBySchool", {}),
    ):
        if key not in sheet:
            sheet[key] = default() if callable(default) else default
            changed = True
    return changed


def validate_cast(sheet: dict, spell: dict, spell_id: str) -> None:
    ensure_spell_fields(sheet)
    known = sheet.get("knownSpells") or []
    if spell_id not in known:
        raise SpellError(f"spell not known: {spell_id}")
    tier = int(sheet.get("classTier", 1))
    if int(spell.get("tier", 1)) > tier:
        raise SpellError(f"spell tier {spell['tier']} exceeds class tier {tier}")
    mp = sheet.get("mp", {})
    cost = effective_mp_cost(sheet, spell)
    if int(mp.get("current", 0)) < cost:
        raise SpellError("insufficient_mp")


def apply_heal(sheet: dict, spell: dict, rng: random.Random) -> int:
    heal = spell.get("heal") or {}
    dice = heal.get("dice", "1d4")
    add_key = heal.get("addAbility", "INT")
    trad = spell.get("tradition") or "arcane"
    mod = casting_mod(sheet, trad if add_key == "SPI" else "arcane")
    if add_key == "SPI":
        mod = ability_modifier(int(sheet.get("attributes", {}).get("SPI", 10)))
    elif add_key == "INT":
        mod = ability_modifier(int(sheet.get("attributes", {}).get("INT", 10)))
    else:
        mod = 0
    amount = roll_dice(dice, rng) + mod
    hp = sheet.setdefault("hp", {"current": 0, "max": 0})
    hp["current"] = min(int(hp.get("max", 0)), int(hp.get("current", 0)) + amount)
    return amount


def record_cast(sheet: dict, spell: dict) -> None:
    school = spell.get("school", "unknown")
    sheet["spellsCastTotal"] = int(sheet.get("spellsCastTotal", 0)) + 1
    by_school = sheet.setdefault("spellsBySchool", {})
    by_school[school] = int(by_school.get(school, 0)) + 1
    if spell.get("concentration"):
        sheet["concentration"] = {
            "spellId": spell.get("id"),
            "displayName": spell.get("displayName"),
        }


def resolve_save_vs_caster_dc(
    *,
    defender_sheet: dict | None,
    defender_monster: dict | None,
    dc: int,
    save_ability: str,
    rng: random.Random,
) -> dict[str, Any]:
    natural = roll_d20(rng)
    if defender_sheet:
        attrs = defender_sheet.get("attributes", {})
        spi_mod = ability_modifier(int(attrs.get("SPI", 10)))
        pb = proficiency_bonus(defender_sheet)
        md = magical_defense_bonus(defender_sheet)
        total = natural + spi_mod + pb + md
        return {
            "natural": natural,
            "total": total,
            "dc": dc,
            "success": total >= dc,
            "defender": "character",
        }
    if defender_monster:
        attrs = defender_monster.get("attributes") or {}
        spi = int(attrs.get("SPI", 0))
        pb = int(defender_monster.get("pb", 2))
        total = natural + spi + pb
        return {
            "natural": natural,
            "total": total,
            "dc": dc,
            "success": total >= dc,
            "defender": "monster",
        }
    mod = 0
    total = natural + mod
    return {"natural": natural, "total": total, "dc": dc, "success": total >= dc}


def roll_spell_damage(dice: str, rng: random.Random, *, half: bool = False) -> int:
    amount = roll_dice(dice, rng)
    return amount // 2 if half else amount
