"""APP-107: exploration economy/social narration verify."""

from __future__ import annotations

import json

import pytest

from gm.narration_verify import (
    TurnTruth,
    build_exploration_turn_truth,
    format_turn_truth_for_prompt,
    verify_narration,
)


def _status(*, gold: int = 62) -> dict:
    return {
        "roster": [{"slot": 1, "gold": gold, "hp": "10/10", "fortune": "1/1"}],
        "party": {"address": "32-C", "phase": "preparation", "mode": "surface"},
        "combat": None,
    }


def _exploration_truth(
    *,
    gold: int = 62,
    tool_results: dict | None = None,
    social_state: dict | None = None,
) -> TurnTruth:
    return build_exploration_turn_truth(
        _status(gold=gold),
        tool_results or {},
        social_state=social_state,
    )


class TestExplorationEconomyVerify:
    def test_gold_mismatch_on_wrong_total(self):
        truth = _exploration_truth(gold=62)
        result = verify_narration("You count 112 gold total in your pouch.", truth)
        assert not result.passed
        assert any(v.startswith("gold_mismatch:112vs62") for v in result.violations)

    def test_social_payment_without_tool(self):
        truth = _exploration_truth(gold=20)
        result = verify_narration("Holt agrees to pay you fifty gold for the job.", truth)
        assert not result.passed
        assert "social_payment_without_tool" in result.violations

    def test_social_outcome_without_roll(self):
        truth = _exploration_truth(gold=20)
        result = verify_narration("Your persuasion succeeds and Holt relents.", truth)
        assert not result.passed
        assert "social_outcome_without_roll" in result.violations

    def test_inventory_claim_without_tool(self):
        truth = _exploration_truth(gold=20)
        result = verify_narration("The clerk hands you a healing draught.", truth)
        assert not result.passed
        assert "inventory_claim_without_tool" in result.violations

    def test_negotiate_quest_advance_allows_payment_prose(self):
        tool_results = {
            "negotiate_quest_advance": {
                "ok": True,
                "advance_gp": 50,
                "skill_id": "persuasion",
                "margin": 6,
                "check": {
                    "ok": True,
                    "skill_id": "persuasion",
                    "success": True,
                    "margin": 6,
                },
                "grant": {"ok": True, "granted_gp": 50, "goldGp_after": 70},
            }
        }
        truth = build_exploration_turn_truth(
            _status(gold=70),
            tool_results,
            social_state={"phase": "resolved", "npc_id": "marshal-garrick-holt"},
        )
        prose = "Holt slides fifty gold across the table with a grudging nod."
        result = verify_narration(prose, truth)
        assert result.passed

    def test_build_exploration_turn_truth_fields(self):
        tool_results = {
            "skill_check": {
                "ok": True,
                "skill_id": "persuasion",
                "success": True,
                "margin": 3,
            },
            "grant_quest_advance": {
                "ok": True,
                "granted_gp": 25,
            },
        }
        truth = build_exploration_turn_truth(
            _status(gold=45),
            tool_results,
            social_state={"phase": "contested", "npc_id": "marshal-garrick-holt"},
        )
        assert truth.engine_gold_gp == 45
        assert truth.gold_delta_this_turn == 25
        assert truth.step == "social"
        assert truth.social_encounter_phase == "contested"
        assert truth.active_npc_id == "marshal-garrick-holt"
        assert len(truth.skill_check_results) == 1
        assert "npc_payment" in truth.allowed_social_outcomes
        assert "advance_gp:25" in truth.allowed_social_outcomes

    def test_format_turn_truth_includes_economy_block(self):
        truth = _exploration_truth(gold=62)
        block = format_turn_truth_for_prompt(truth, creation=None)
        assert "Engine gold (after tools): 62 gp" in block
        assert "Do not claim GP totals" in block


def _tool_call(name: str, args: dict | None = None, *, call_id: str = "tc1") -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args or {}),
        },
    }


def _exploration_ready(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    result = orchestrator.setup_new_game()
    assert result.get("ok"), result
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_restore_creation_from_session_state", lambda: None)
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    monkeypatch.setattr(orchestrator, "_encounter_verify_active", lambda _status: False)


def test_orchestrator_verify_pass_after_negotiate_tool(orchestrator, monkeypatch):
    """Integration: settled _llm_loop prose passes verify when negotiate tool ok."""
    _exploration_ready(orchestrator, monkeypatch)

    negotiate_result = {
        "ok": True,
        "advance_gp": 50,
        "skill_id": "persuasion",
        "margin": 8,
        "check": {"ok": True, "skill_id": "persuasion", "success": True, "margin": 8},
        "grant": {"ok": True, "granted_gp": 50},
    }

    llm_loop_calls = 0
    narrate_llm_calls = 0
    verify_events: list[dict] = []

    def fake_llm_loop(messages):
        nonlocal llm_loop_calls
        llm_loop_calls += 1
        orchestrator._last_tool_results = {
            "negotiate_quest_advance": negotiate_result,
        }
        orchestrator._tools_ok_this_turn = ["negotiate_quest_advance"]
        return "Holt counts out fifty gold and pushes the coins toward you."

    def fake_call_narration_llm(messages):
        nonlocal narrate_llm_calls
        narrate_llm_calls += 1
        return "Holt counts out fifty gold and pushes the coins toward you."

    import gm.orchestrator as orchestrator_module

    real_status = orchestrator.bridge.status

    def status_with_gold() -> dict:
        st = dict(real_status())
        roster = [dict(r) for r in (st.get("roster") or [])]
        if roster:
            roster[0]["gold"] = 70
        st["roster"] = roster
        st["combat"] = None
        return st

    def fake_social_state() -> dict:
        return {"ok": True, "phase": "resolved", "npc_id": "marshal-garrick-holt"}

    monkeypatch.setattr(orchestrator, "_llm_loop", fake_llm_loop)
    monkeypatch.setattr(orchestrator, "_call_narration_llm", fake_call_narration_llm)
    monkeypatch.setattr(orchestrator.bridge, "status", status_with_gold)
    monkeypatch.setattr(orchestrator, "_social_state_for_truth", fake_social_state)
    monkeypatch.setattr(
        orchestrator_module,
        "log_narration_verify_pass",
        lambda data: verify_events.append(data),
    )
    monkeypatch.setattr(orchestrator, "_emit_narration", lambda narration: None)
    monkeypatch.setattr(orchestrator.bridge, "ensure_cell_initialized", lambda: None)

    orchestrator.process_turn("Front me fifty gold, Holt.")

    assert llm_loop_calls == 1
    assert narrate_llm_calls == 0
    assert verify_events
    assert verify_events[0].get("mode") == "exploration"
    assert verify_events[0].get("step") in ("economy", "social")
