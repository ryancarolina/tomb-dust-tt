from __future__ import annotations

from gm.creation import CreationState
from gm.choice_memory import creation_choice_fact
from tomb_gm.services.memory.choice_facts import mechanical_impact_fact, tool_impact_fact


def test_creation_name_fact():
    state = CreationState(name="Cade", step="RACE")
    fact = creation_choice_fact("NAME", state)
    assert fact is not None
    assert "Cade" in fact
    assert "registered" in fact


def test_creation_skills_fact():
    state = CreationState(
        name="Cade",
        race="undead",
        chosen_class="urchin",
        chosen_skills=["stealth", "sleight-of-hand", "perception"],
        step="EQUIPMENT_GOLD",
    )
    fact = creation_choice_fact("SKILLS", state)
    assert fact is not None
    assert "Stealth" in fact
    assert "Urchin" in fact


def test_mechanical_travel_fact():
    fact = mechanical_impact_fact(
        player_action="travel to 32-C-UG-1",
        mechanical={
            "ok": True,
            "action": "travel",
            "from": "32-C",
            "to": "32-C-UG-1",
            "cell": {"displayName": "Breley undercrypt"},
        },
        address="32-C",
    )
    assert fact is not None
    assert "32-C-UG-1" in fact
    assert "Breley undercrypt" in fact


def test_mechanical_skips_look():
    fact = mechanical_impact_fact(
        player_action="look around",
        mechanical={"ok": True, "action": "look"},
        address="32-C",
    )
    assert fact is None


def test_tool_world_travel_fact():
    fact = tool_impact_fact(
        "world_travel",
        {"to_address": "33-C"},
        {
            "ok": True,
            "from": "32-C",
            "to": "33-C",
            "cell": {"displayName": "King's Road"},
        },
    )
    assert fact is not None
    assert "33-C" in fact


def test_tool_skips_process_beat():
    assert tool_impact_fact("process_beat", {}, {"ok": True}) is None


def test_memories_for_roster_filters_stale_character_facts():
    from tomb_gm.services.memory import _memories_for_roster

    memories = [
        {"fact": "Character registered: Dig, orc militia, 35 HP."},
        {"fact": "Character creation: player registered the delver name 'Sam'."},
        {"fact": "The party bought rations at 32-C."},
    ]
    filtered = _memories_for_roster(memories, [])
    assert all("Dig" not in m["fact"] for m in filtered)
    assert all("Character creation" not in m["fact"] for m in filtered)
    assert any("rations" in m["fact"] for m in filtered)
