"""Integration test: full character creation FSM through finalize (APP-057)."""

# Module-level constant only — NO Orchestrator import (R1 / APP-049)

FIXED_ROLL: dict = {
    "ok": True,
    "race": "human",
    "racial_adjustments": {"STR": 1, "INT": 1},
    "base_rolls": {"STR": 9, "AGI": 9, "STA": 9, "INT": 11, "SPI": 9},
    "genetic_factors": {
        a: {"roll": 2, "mod": 0}
        for a in ("STR", "AGI", "STA", "INT", "SPI")
    },
    "life_event": {"roll": 20, "name": "Unremarkable Youth", "mods": {}},
    "final_attributes": {"STR": 10, "AGI": 10, "STA": 10, "INT": 12, "SPI": 10, "LUC": 10},
    "eligible_classes": [
        "peasant",
        "laborer",
        "urchin",
        "apprentice",
        "militia",
        "novice",
    ],
}

INPUTS = [
    ("new game", "NAME"),
    ("Dumpy", "RACE"),
    ("human", "CLASS"),
    ("apprentice", "SKILLS"),
    ("Lore, Spellcasting, Arcana", "SPELL_SCHOOLS"),
    ("pyromancy, ether", "SPELLS"),
    ("ember-touch, static-lash", "EQUIPMENT_GOLD"),
    ("yes", "WORLD_INTRO"),
]


def test_full_creation_apprentice_caster(orchestrator, monkeypatch):
    drift_events: list[dict] = []
    monkeypatch.setattr(
        "gm.orchestrator.log_creation_drift",
        lambda data: drift_events.append(data),
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )

    last = ""
    for text, expected_step in INPUTS:
        last = orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step, (
            f"After {text!r}: step={orchestrator.creation.step}, expected {expected_step}"
        )
        if text == "new game":
            assert orchestrator.creation.active is True
        if text == "Dumpy":
            assert "Pick **one race**" in last
            assert "| Race | Adjustments | Description |" in last
            assert "Awaiting: RACE_INPUT" in last
            assert last.strip() != "The clerk waits."
            assert orchestrator.creation.races_table_shown is True
        if text == "human":
            assert orchestrator.creation.classes_table_shown is True
            assert "Attr | Base | Genetic | Life Evt | Racial | Final" in last
            assert "Life event: Unremarkable Youth" in last
            for attr, final in FIXED_ROLL["final_attributes"].items():
                if attr == "LUC":
                    continue
                assert f"| {attr} |" in last
                assert f"| {final} |" in last
            assert "| LUC |" in last
            assert "| 10 |" in last
            assert "**HP:** 60" in last
            assert "(10 + STA 10 × 5)" in last
            assert last.count("Pick **one tier-1 class**") == 1
            assert "**Final attributes:**" not in last
            assert "Test narration." in last
        if text == "apprentice":
            assert "Pick **3 skills**" in last
            assert "| Category | Skill |" in last
            assert "Awaiting: SKILLS_INPUT" in last
            assert "| School | Tradition |" not in last
            assert "**Registry kit:**" not in last
            assert "Pick **one race**" not in last
            assert orchestrator.creation.skills_table_shown is True
        if text == "Lore, Spellcasting, Arcana":
            assert "| School | Tradition | Themes |" in last
            assert "Awaiting: SPELL_SCHOOLS_INPUT" in last
            assert "| Category | Skill |" not in last
            assert "**Registry kit:**" not in last
            assert "| Spell | School | MP | Effect |" not in last
            assert orchestrator.creation.schools_table_shown is True
        if text == "pyromancy, ether":
            assert "Pick **2 tier-1 spells**" in last
            assert "| Spell | School | MP | Effect |" in last
            assert "Awaiting: SPELLS_INPUT" in last
            assert "| School | Tradition |" not in last
            assert "**Registry kit:**" not in last
            assert orchestrator.creation.spells_table_shown is True
        if text == "ember-touch, static-lash":
            assert "**Registry kit:**" in last
            assert "**Starting gold:**" in last
            assert "**Skills on record:**" in last
            assert "Reply **yes**" in last
            assert "Awaiting: EQUIPMENT_GOLD_CONFIRMATION" in last
            assert "| Spell | School | MP | Effect |" not in last
            assert "| School | Tradition |" not in last

    assert drift_events == [], f"unexpected creation_drift: {drift_events}"

    assert orchestrator.creation.active is False
    assert orchestrator.creation.step == "WORLD_INTRO"

    status = orchestrator.bridge.status()
    assert len(status["roster"]) >= 1
    assert status["awaiting"] == "PLAYER_ACTIONS"
    assert status["roster"][0]["display_name"] == "Dumpy"
    assert status["roster"][0]["base_class"] == "apprentice"

    assert "Awaiting: RECEPTION_CHOICE" in last
    assert "Phase: preparation" in last
    assert "PRE_DELVE" not in last


BAD_PREMATURE_FLAVOR = (
    "You are now a registered Delver. "
    "[Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE]"
)


def test_skills_turn_rejects_premature_completion_flavor(orchestrator, monkeypatch):
    """APP-070: completion leak in flavor is stripped; FSM and roster unchanged."""
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    monkeypatch.setattr(
        orchestrator,
        "_narrate_flavor",
        lambda _msgs: BAD_PREMATURE_FLAVOR,
    )

    for text, expected_step in INPUTS[:4]:
        orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step

    assert orchestrator.creation.step == "SKILLS"

    last = orchestrator.process_turn("Lore, Spellcasting, Arcana")

    assert orchestrator.creation.step == "SPELL_SCHOOLS"
    assert orchestrator.creation.active is True
    assert len(orchestrator.bridge.status()["roster"]) == 0

    last_lower = last.lower()
    assert "pre_delve" not in last_lower
    assert "reception_choice" not in last_lower
    assert "registered delver" not in last_lower
    assert "Awaiting: SPELL_SCHOOLS_INPUT" in last


CONGRATULATORY_FLAVOR_STUB = "Smart choices for a Supa."


def test_skills_error_path_skips_congratulatory_flavor(orchestrator, monkeypatch):
    """APP-075 T2: invalid skills input skips LLM flavor; names unknown token."""
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    monkeypatch.setattr(
        orchestrator,
        "_narrate_flavor",
        lambda _msgs: CONGRATULATORY_FLAVOR_STUB,
    )

    for text, expected_step in INPUTS[:4]:
        orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step

    assert orchestrator.creation.step == "SKILLS"

    last = orchestrator.process_turn("spellcasting, medicine, bogus")

    assert orchestrator.creation.step == "SKILLS"
    assert "**Note:**" in last
    assert "bogus" in last
    assert "Awaiting: SKILLS_INPUT" in last
    last_lower = last.lower()
    assert "smart choices" not in last_lower
    assert "excellent" not in last_lower
    assert "moving on" not in last_lower
    assert CONGRATULATORY_FLAVOR_STUB.lower() not in last_lower


def test_skills_glued_alias_advances_to_schools(orchestrator, monkeypatch):
    """APP-075 T2b: glued skill token parses and advances to spell schools."""
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )

    for text, expected_step in INPUTS[:4]:
        orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step

    last = orchestrator.process_turn("spellcasting, medicine, manacontrol")

    assert orchestrator.creation.step == "SPELL_SCHOOLS"
    assert "Awaiting: SPELL_SCHOOLS_INPUT" in last
    assert "**Note:**" not in last


def test_schools_error_path_skips_congratulatory_flavor(orchestrator, monkeypatch):
    """APP-075 T3: invalid school input skips congratulatory flavor."""
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    monkeypatch.setattr(
        orchestrator,
        "_narrate_flavor",
        lambda _msgs: CONGRATULATORY_FLAVOR_STUB,
    )

    for text, expected_step in INPUTS[:4]:
        orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step

    orchestrator.process_turn("spellcasting, medicine, manacontrol")
    assert orchestrator.creation.step == "SPELL_SCHOOLS"

    last = orchestrator.process_turn("pyromancy")

    assert orchestrator.creation.step == "SPELL_SCHOOLS"
    assert "**Note:**" in last
    last_lower = last.lower()
    assert "smart choices" not in last_lower
    assert "excellent" not in last_lower
    assert "moving on" not in last_lower
    assert CONGRATULATORY_FLAVOR_STUB.lower() not in last_lower
    assert "Awaiting: SPELL_SCHOOLS_INPUT" in last


def test_roll_stats_flavor_reflects_committed_race(orchestrator, monkeypatch):
    """APP-069: contradictory race name in flavor is stripped when race is undead."""
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    monkeypatch.setattr(
        orchestrator,
        "_narrate_flavor",
        lambda _msgs: "Human lineage shows in the ledger.",
    )

    orchestrator.process_turn("new game")
    orchestrator.process_turn("Rick")
    narration = orchestrator.process_turn("undead")

    assert orchestrator.creation.race == "undead"
    assert "Attr | Base | Genetic | Life Evt | Racial | Final" in narration
    assert "Human" not in narration


def test_creation_flavor_messages_committed_class(orchestrator, monkeypatch):
    """APP-069: flavor system prompt includes committed race/class after class pick."""
    captured: list[list] = []

    def _capture_messages(msgs):
        captured.append(msgs)
        return "Test narration."

    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    monkeypatch.setattr(orchestrator, "_call_narration_llm", _capture_messages)

    for text, _ in INPUTS[:4]:
        orchestrator.process_turn(text)

    assert orchestrator.creation.chosen_class == "apprentice"
    assert captured
    system_content = " ".join(
        m["content"] for m in captured[-1] if m.get("role") == "system"
    )
    assert "Committed class: apprentice" in system_content
    assert "Committed race:" in system_content


def test_name_advance_presents_race_table(orchestrator):
    orchestrator.process_turn("new game")
    assert orchestrator.creation.step == "NAME"

    narration = orchestrator.process_turn("Dumpy")

    assert orchestrator.creation.step == "RACE"
    assert orchestrator.creation.races_table_shown is True
    assert "Pick **one race**" in narration
    assert "| Race | Adjustments | Description |" in narration
    assert "Awaiting: RACE_INPUT" in narration
    assert narration.strip() != "The clerk waits."

