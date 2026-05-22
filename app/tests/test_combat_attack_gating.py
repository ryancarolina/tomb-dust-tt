"""APP-026: orchestrator pre-gates PC attacks before bridge dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _combat_status(
    *,
    turn_id: str = "pc1",
    initiative: list[dict] | None = None,
    combatants: list[dict] | None = None,
) -> dict:
    """Return full bridge.status()-shaped dict with combat block."""
    if initiative is None:
        initiative = [{"id": turn_id, "name": "PC", "initiative": 15}]
    if combatants is None:
        combatants = [{"id": turn_id, "displayName": "Aldric", "kind": "pc", "hp": 10}]
    return {
        "combat": {
            "round": 1,
            "turn_index": 0,
            "turn_id": turn_id,
            "turn_kind": "pc",
            "initiative": initiative,
            "combatants": combatants,
        },
        "awaiting": "COMBAT_TURN",
    }


# ─── G1 ───────────────────────────────────────────────────────────────────


def test_execute_tool_combat_attack_gated_no_combat(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: {})
    combat_attack = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator.bridge, "combat_attack", combat_attack)

    result = orchestrator._execute_tool(
        "combat_attack",
        {"attacker_id": "pc1", "target_id": "m1"},
    )

    assert result == {"ok": False, "error": "no active combat for session"}
    combat_attack.assert_not_called()


# ─── G2 ───────────────────────────────────────────────────────────────────


def test_gate_pc_attack_rejects_unknown_attacker(orchestrator, monkeypatch):
    status = _combat_status(
        initiative=[{"id": "pc1"}],
        combatants=[{"id": "pc1", "displayName": "Aldric"}],
    )
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: status)

    result = orchestrator._gate_pc_attack("unknown")

    assert result == {"ok": False, "error": "attacker not in combat: unknown"}


# ─── G3 ───────────────────────────────────────────────────────────────────


def test_gate_pc_attack_resolves_display_name(orchestrator, monkeypatch):
    status = _combat_status(
        initiative=[{"id": "pc1"}],
        combatants=[{"id": "pc1", "displayName": "Aldric"}],
    )
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: status)

    assert orchestrator._gate_pc_attack("Aldric") is None


# ─── G4 ───────────────────────────────────────────────────────────────────


def test_execute_combat_action_attack_no_combat(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: {})
    combat_action = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator.bridge, "combat_action", combat_action)

    result = orchestrator._execute_combat_action(
        "ATTACK",
        actor_id="pc1",
        target_id="m1",
    )

    assert result == {"ok": False, "error": "no active combat for session"}
    combat_action.assert_not_called()


# ─── G5 ───────────────────────────────────────────────────────────────────


def test_execute_combat_action_attack_not_in_initiative(orchestrator, monkeypatch):
    status = _combat_status(
        turn_id="pc1",
        initiative=[{"id": "m1"}],
        combatants=[{"id": "pc1"}, {"id": "m1"}],
    )
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: status)
    combat_action = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator.bridge, "combat_action", combat_action)

    result = orchestrator._execute_combat_action(
        "ATTACK",
        actor_id="pc1",
        target_id="m1",
    )

    assert result == {"ok": False, "error": "attacker not in combat: pc1"}
    combat_action.assert_not_called()


# ─── G6 ───────────────────────────────────────────────────────────────────


def test_execute_tool_combat_attack_passes_gate(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: _combat_status())
    combat_attack = MagicMock(return_value={"ok": True, "hit": True})
    monkeypatch.setattr(orchestrator.bridge, "combat_attack", combat_attack)

    result = orchestrator._execute_tool(
        "combat_attack",
        {"attacker_id": "pc1", "target_id": "m1"},
    )

    assert result == {"ok": True, "hit": True}
    combat_attack.assert_called_once()


# ─── G6b ──────────────────────────────────────────────────────────────────


def test_execute_combat_action_attack_passes_gate(orchestrator, monkeypatch):
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: _combat_status(turn_id="pc1"),
    )
    combat_action = MagicMock(return_value={"ok": True, "hit": True})
    monkeypatch.setattr(orchestrator.bridge, "combat_action", combat_action)

    result = orchestrator._execute_combat_action(
        "ATTACK",
        actor_id="pc1",
        target_id="m1",
    )

    assert result == {"ok": True, "hit": True}
    combat_action.assert_called_once()


# ─── G7 ───────────────────────────────────────────────────────────────────


def test_app028_t4_regression():
    import subprocess
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "app/tests/test_combat_failure_narration.py",
            "-q",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ─── G8 ───────────────────────────────────────────────────────────────────


def test_execute_combat_action_lowercase_attack_not_in_initiative(
    orchestrator, monkeypatch
):
    status = _combat_status(
        turn_id="pc1",
        initiative=[{"id": "m1"}],
        combatants=[{"id": "pc1"}, {"id": "m1"}],
    )
    monkeypatch.setattr(orchestrator.bridge, "status", lambda: status)
    combat_action = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator.bridge, "combat_action", combat_action)

    result = orchestrator._execute_combat_action(
        "attack",
        actor_id="pc1",
        target_id="m1",
    )

    assert result == {"ok": False, "error": "attacker not in combat: pc1"}
    combat_action.assert_not_called()
