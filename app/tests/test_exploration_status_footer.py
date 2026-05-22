"""APP-077: code-owned exploration/combat status footer."""

from __future__ import annotations

import pytest

from gm.creation import (
    format_exploration_status,
    strip_llm_meta_narration,
    strip_llm_status_tags,
)
from gm.orchestrator import _SITE_ENTRY_REFUSAL_LINE

STATUS_SURFACE = {
    "awaiting": "PLAYER_ACTIONS",
    "party": {
        "address": "32-C",
        "phase": "preparation",
        "gold_in_transit": 0,
    },
    "roster": [
        {"slot": 1, "hp": "12/12", "fortune": "1/1", "gold": 50},
    ],
}

STATUS_DELVE = {
    "awaiting": "PLAYER_ACTIONS",
    "party": {
        "address": "32-C-UG-1",
        "display_address": "32-C-UG-1 / antechamber",
        "phase": "delve",
        "gold_in_transit": 0,
    },
    "roster": [
        {"slot": 1, "hp": "10/12", "fortune": "1/1", "gold": 50},
    ],
}

STATUS_COMBAT = {
    "awaiting": "COMBAT_TURN",
    "party": {
        "address": "32-C-UG-1",
        "display_address": "32-C-UG-1 / antechamber",
        "phase": "delve",
        "gold_in_transit": 0,
    },
    "roster": [
        {"slot": 1, "hp": "10/12", "fortune": "1/1", "gold": 75},
    ],
    "combat": {
        "turn_id": "pc-1",
        "combatants": [{"id": "pc-1", "kind": "pc", "name": "Test"}],
    },
}

STATUS_GP_TRANSIT = {
    "awaiting": "PLAYER_ACTIONS",
    "party": {
        "address": "32-C",
        "phase": "preparation",
        "gold_in_transit": 12,
    },
    "roster": [
        {"slot": 1, "hp": "12/12", "fortune": "1/1", "gold": 61},
    ],
}

STATUS_EMPTY_ROSTER = {
    "awaiting": "PLAYER_ACTIONS",
    "party": {
        "address": "32-C",
        "phase": "preparation",
        "gold_in_transit": 0,
    },
    "roster": [],
}

FOOTER_SURFACE = (
    "[Location: 32-C | Phase: preparation | HP: 12/12 | Fortune: 1/1 | "
    "GP: 50 | Awaiting: PLAYER_ACTIONS]"
)
FOOTER_DELVE = (
    "[Location: 32-C-UG-1 / antechamber | Phase: delve | HP: 10/12 | Fortune: 1/1 | "
    "GP: 50 | Awaiting: PLAYER_ACTIONS]"
)
FOOTER_COMBAT = (
    "[Location: 32-C-UG-1 / antechamber | Phase: delve | HP: 10/12 | Fortune: 1/1 | "
    "GP: 75 | Turn: pc-1 | Awaiting: COMBAT_TURN]"
)
FOOTER_EMPTY_ROSTER = (
    "[Location: 32-C | Phase: preparation | HP: ?/? | Fortune: ?/1 | "
    "GP: 0 | Awaiting: PLAYER_ACTIONS]"
)


def _footer_region(n: str) -> str:
    idx = n.rfind("[Location:")
    return n[idx:] if idx >= 0 else ""


def test_format_exploration_status_golden():
    assert format_exploration_status(STATUS_SURFACE) == FOOTER_SURFACE
    assert format_exploration_status(STATUS_DELVE) == FOOTER_DELVE
    assert format_exploration_status(STATUS_COMBAT) == FOOTER_COMBAT


def test_format_exploration_status_gp_transit():
    footer = format_exploration_status(STATUS_GP_TRANSIT)
    assert "GP: 61 (+12 transit)" in footer


def test_format_exploration_status_empty_roster():
    assert format_exploration_status(STATUS_EMPTY_ROSTER) == FOOTER_EMPTY_ROSTER


def test_strip_llm_status_tags_exploration_bracket():
    prose = (
        "Wind off the salt road.\n\n"
        "[Location: 32-C | Phase: delve | HP: 99/99 | Fortune: 9/9 | GP: 999 | Awaiting: PLAYER_ACTIONS]\n"
        "Awaiting: COMBAT_TURN"
    )
    out = strip_llm_status_tags(prose)
    assert "Wind off the salt road." in out
    assert "[Location:" not in out
    assert "Awaiting:" not in out


def test_strip_llm_meta_narration():
    prose = "The clerk nods.\n\n---\n**Campaign Memory Updated:**"
    out = strip_llm_meta_narration(prose)
    assert out == "The clerk nods."


def test_compose_exploration_single_footer(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: STATUS_SURFACE)
    llm_body = (
        "Salt wind rattles the Registry shutters.\n\n"
        "[Location: 32-C | Phase: preparation | HP: 12/12 | Fortune: 1/1 | GP: 999 | Awaiting: PLAYER_ACTIONS]"
    )
    composed = orchestrator._compose_exploration_narration(llm_body, gate_active=False)
    assert composed.count("[Location:") == 1
    footer = _footer_region(composed)
    assert "GP: 50" in footer
    assert "GP: 999" not in footer


def test_compose_empty_body_still_footer(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: STATUS_SURFACE)
    composed = orchestrator._compose_exploration_narration("   \n\n  ", gate_active=False)
    assert composed.startswith("\n\n") or composed == FOOTER_SURFACE
    assert FOOTER_SURFACE in composed
    assert composed.count("[Location:") == 1


def test_compose_app024_refusal_plus_footer(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: STATUS_SURFACE)
    entry_prose = "You step into the torchlit crypt. Corridors stretch ahead."
    composed = orchestrator._compose_exploration_narration(entry_prose, gate_active=True)
    assert _SITE_ENTRY_REFUSAL_LINE in composed
    assert FOOTER_SURFACE in composed
    assert "torchlit" not in composed.lower()


def test_compose_idempotent_double_call(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: STATUS_SURFACE)
    llm_body = (
        "Registry clerk stamps your permit.\n\n"
        "[Location: 32-C | Phase: preparation | HP: 12/12 | Fortune: 1/1 | GP: 999 | Awaiting: PLAYER_ACTIONS]"
    )
    once = orchestrator._compose_exploration_narration(llm_body, gate_active=False)
    twice = orchestrator._compose_exploration_narration(once, gate_active=False)
    assert twice.count("[Location:") == 1
    footer = _footer_region(twice)
    assert footer.count("GP:") == 1
    assert "GP: 50" in footer


def test_combat_turn_compose_wrong_gp(orchestrator, monkeypatch):
    emitted: list[str] = []

    def _capture(narration: str) -> None:
        emitted.append(narration)

    monkeypatch.setattr(orchestrator, "_emit_narration", _capture)
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: True)
    monkeypatch.setattr(orchestrator, "_sync_combat_from_status", lambda: None)
    monkeypatch.setattr(orchestrator, "_combat_auto_chain", lambda: [])
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: STATUS_COMBAT)
    orchestrator.combat.active = True
    orchestrator.combat.pending_start = False
    orchestrator.combat.order_narrated = True

    bad_bracket = (
        "[Location: 32-C-UG-1 / antechamber | Phase: delve | HP: 10/12 | Fortune: 1/1 | "
        "GP: 999 | Turn: pc-1 | Awaiting: COMBAT_TURN]"
    )
    monkeypatch.setattr(
        orchestrator,
        "_combat_llm_loop",
        lambda player_input, status: f"The ghoul lunges.\n\n{bad_bracket}",
    )

    orchestrator._combat_turn("attack with sword")

    assert len(emitted) == 1
    narration = emitted[0]
    assert narration.count("[Location:") == 1
    footer = _footer_region(narration)
    assert "Turn: pc-1" in footer
    assert "GP: 75" in footer
    assert "GP: 999" not in footer
    assert "The ghoul lunges." in narration
