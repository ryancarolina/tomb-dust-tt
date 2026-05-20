"""Integration test: full character creation FSM through finalize (APP-057)."""

# Module-level constant only — NO Orchestrator import (R1 / APP-049)

FIXED_ROLL: dict = {
    "ok": True,
    "race": "human",
    "racial_adjustments": {"STR": 1, "INT": 1},
    "base_rolls": {"STR": 9, "AGI": 9, "STA": 9, "INT": 11, "SPI": 9, "LUC": 9},
    "genetic_factors": {"STR": 0, "AGI": 0, "STA": 0, "INT": 0, "SPI": 0, "LUC": 0},
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
