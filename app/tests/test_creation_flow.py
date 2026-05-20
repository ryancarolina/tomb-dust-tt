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
