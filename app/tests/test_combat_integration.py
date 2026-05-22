"""APP-030: bridge combat golden path (I1)."""

from __future__ import annotations

import pytest

from gm.combat_fsm import is_pc_turn


def _ensure_combat_roster_session(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("salt-road")
    assert start.get("ok"), start.get("error")
    created = bridge.character_create(name="Sammy", background="militia")
    assert created.get("ok"), created.get("error")
    assert created.get("id")
    assert bridge.status().get("combat") is None


def _advance_to_pc_turn(bridge, *, max_rounds: int = 5) -> dict:
    for _ in range(max_rounds):
        status = bridge.status()
        if not status.get("combat"):
            pytest.fail("combat ended before PC turn")
        if is_pc_turn(status):
            return status
        adv = bridge.run_combat_monster_turns()
        assert adv.get("ok"), adv
    pytest.fail(f"PC turn not reached within {max_rounds} iterations")


def test_bridge_combat_start_attack_end(bridge):
    _ensure_combat_roster_session(bridge)

    start = bridge.start_combat(monster_specs=["grave-ghoul:1"])
    assert start.get("ok") is True
    assert start.get("action") == "combat_start"

    status = bridge.status()
    combat = status["combat"]
    assert combat is not None
    combatants = combat.get("combatants") or []
    pcs = [c for c in combatants if c.get("kind") == "pc"]
    ghouls = [c for c in combatants if str(c.get("id", "")).startswith("grave-ghoul")]
    assert pcs, "roster PC missing from combatants"
    assert ghouls, "grave-ghoul missing from combatants"

    status = _advance_to_pc_turn(bridge)
    combat = status["combat"]
    combatants = combat.get("combatants") or []
    turn_id = combat["turn_id"]
    pcs = [c for c in combatants if c.get("kind") == "pc"]
    ghouls = [c for c in combatants if str(c.get("id", "")).startswith("grave-ghoul")]
    attacker_id = (
        turn_id
        if any(c.get("id") == turn_id and c.get("kind") == "pc" for c in combatants)
        else pcs[0]["id"]
    )
    target_id = ghouls[0]["id"]

    attack = bridge.combat_attack(attacker_id, target_id)
    assert attack.get("ok") is True
    assert bridge.status().get("combat") is not None

    end = bridge.combat_end()
    assert end.get("ok") is True
    assert bridge.status().get("combat") is None
