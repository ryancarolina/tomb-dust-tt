from __future__ import annotations

from gm.creation import (
    CreationState,
    ensure_equipment_gold,
    format_skills_table,
    format_schools_table,
    format_spells_table,
    is_clarification,
    is_equipment_confirm,
    is_equipment_objection,
    normalize_skill_slug,
    parse_player_skills,
    parse_player_schools,
    parse_player_spells,
    validate_skill_picks,
    validate_school_picks,
    validate_spell_picks,
    needs_spell_picks,
    skip_inapplicable_spell_steps,
)


def test_normalize_skill_slug():
    assert normalize_skill_slug("Sleight of Hand") == "sleight-of-hand"
    assert normalize_skill_slug("shield-use") == "shield-use"
    assert normalize_skill_slug("bogus") is None


def test_parse_player_skills_comma_list():
    skills = parse_player_skills("Stealth, Sleight of Hand, Perception", "urchin")
    assert skills == ["stealth", "sleight-of-hand", "perception"]


def test_parse_player_skills_rejects_clarification():
    assert parse_player_skills("I dont see the skills", "urchin") is None
    assert is_clarification("what are my options?")


def test_validate_urchin_requires_class_skill():
    assert validate_skill_picks("urchin", ["archery", "lore", "medicine"]) is not None
    assert validate_skill_picks("urchin", ["stealth", "lore", "medicine"]) is None


def test_format_skills_table_includes_class_markers():
    table = format_skills_table("urchin")
    assert "Stealth" in table
    assert "★" in table
    assert "Pick **3 skills**" in table


def test_equipment_confirm_and_objection():
    assert is_equipment_confirm("yes, ready to go")
    assert is_equipment_objection("I didnt get to pick my skills")
    assert not is_equipment_confirm("I didnt get to pick my skills")


def test_creation_state_roundtrip():
    state = CreationState(
        active=True,
        step="SKILLS",
        name="Cade",
        race="undead",
        chosen_class="urchin",
        skills_table_shown=True,
        roll_result={"final_attributes": {"STR": 2}},
        gold_roll=4,
    )
    restored = CreationState.from_dict(state.to_dict())
    assert restored.name == "Cade"
    assert restored.step == "SKILLS"
    assert restored.skills_table_shown is True
    assert restored.roll_result["final_attributes"]["STR"] == 2


def test_ensure_equipment_gold_stable():
    state = CreationState(
        active=True,
        step="EQUIPMENT_GOLD",
        chosen_class="urchin",
        roll_result={"life_event": {"name": "Unremarkable Youth"}},
        gold_roll=3,
    )
    ensure_equipment_gold(state)
    first = state.starting_gold
    ensure_equipment_gold(state)
    assert state.starting_gold == first
    assert state.starting_gold == 15  # (5 + 0) * 3


def test_needs_spell_picks():
    state = CreationState(chosen_class="novice", chosen_skills=["medicine", "spellcasting", "lore"])
    assert needs_spell_picks(state) is True
    state.chosen_skills = ["medicine", "lore", "persuasion"]
    assert needs_spell_picks(state) is False


def test_skip_spell_steps_for_non_caster():
    state = CreationState(
        active=True,
        step="SPELL_SCHOOLS",
        chosen_class="militia",
        chosen_skills=["swordsmanship", "perception", "lore"],
    )
    skip_inapplicable_spell_steps(state)
    assert state.step == "EQUIPMENT_GOLD"


def test_parse_novice_schools_and_spells():
    schools = parse_player_schools("divine, ward", "novice")
    assert schools == ["divine", "ward"]
    assert validate_school_picks("novice", schools) is None
    spells = parse_player_spells("mend-light, consecrate-ground", "novice", schools)
    assert spells == ["mend-light", "consecrate-ground"]
    assert validate_spell_picks("novice", schools, spells) is None


def test_format_spell_tables():
    table = format_schools_table("apprentice")
    assert "Pyromancy" in table
    schools = parse_player_schools("pyromancy, ether", "apprentice")
    assert schools
    spell_table = format_spells_table("apprentice", schools)
    assert "Ember Touch" in spell_table
