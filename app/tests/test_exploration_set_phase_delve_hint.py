"""APP-022: hint compass_exits + enter_dungeon on failed set_phase(delve)."""

from __future__ import annotations

import json

import pytest

from test_exploration_site_entry_gate import (
    BENIGN_SURFACE,
    ENTRY_PROSE,
    _patch_llm_sequence,
    _patch_party_mode,
    _surface_exploration_orchestrator,
    _tool_call,
)

_SET_PHASE_DELVE_FAIL = {"ok": False, "error": "Cannot transition from preparation to delve"}


def _mock_set_phase_delve_fail(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: (
            _SET_PHASE_DELVE_FAIL
            if name == "set_phase"
            else {"ok": False, "error": f"unexpected {name}"}
        ),
    )


def _assert_hint_phrases(text: str) -> None:
    lower = text.lower()
    assert "compass_exits" in lower
    assert "enter_dungeon" in lower


def _assert_no_delve_hint(text: str) -> None:
    lower = text.lower()
    assert "do not use set_phase to enter a site" not in lower
    assert "compass_exits" not in lower or "enter_dungeon" not in lower


def test_failed_set_phase_delve_tool_result_has_hint(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    _mock_set_phase_delve_fail(orchestrator, monkeypatch)
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [_tool_call("set_phase", {"phase": "delve"})],
                "finish_reason": "tool_calls",
            },
            {"content": BENIGN_SURFACE, "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("go underground")

    hint = orchestrator._last_tool_results["set_phase"].get("hint", "")
    _assert_hint_phrases(hint)


def test_all_failed_content_includes_player_hint(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    _mock_set_phase_delve_fail(orchestrator, monkeypatch)
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": ENTRY_PROSE,
                "tool_calls": [_tool_call("set_phase", {"phase": "delve"})],
                "finish_reason": "tool_calls",
            },
        ],
    )

    narration = orchestrator.process_turn("delve now")

    assert "[Mechanics failed" in narration
    _assert_hint_phrases(narration)
    lower = narration.lower()
    assert "torchlit" not in lower
    assert "corridor" not in lower
    assert "step into" not in lower


def test_failed_set_phase_ingress_no_hint(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: (
            {"ok": False, "error": "Cannot transition from preparation to ingress"}
            if name == "set_phase"
            else {"ok": False, "error": f"unexpected {name}"}
        ),
    )
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": ENTRY_PROSE,
                "tool_calls": [_tool_call("set_phase", {"phase": "ingress"})],
                "finish_reason": "tool_calls",
            },
        ],
    )

    narration = orchestrator.process_turn("enter ingress")

    assert "hint" not in orchestrator._last_tool_results.get("set_phase", {})
    _assert_no_delve_hint(narration)


def test_successful_set_phase_delve_no_hint(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "ingress")
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: (
            {"ok": True, "phase": "delve"}
            if name == "set_phase"
            else {"ok": False, "error": f"unexpected {name}"}
        ),
    )
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [_tool_call("set_phase", {"phase": "delve"})],
                "finish_reason": "tool_calls",
            },
            {"content": BENIGN_SURFACE, "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("advance to delve")

    result = orchestrator._last_tool_results.get("set_phase", {})
    assert "hint" not in result
    assert result.get("ok") is True


def test_partial_success_enter_dungeon_no_player_hint(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")

    def fake_execute(name, args):
        if name == "set_phase":
            return _SET_PHASE_DELVE_FAIL
        if name == "enter_dungeon":
            return {"ok": True, "mode": "dungeon"}
        return {"ok": False, "error": f"unexpected {name}"}

    monkeypatch.setattr(orchestrator, "_execute_tool", fake_execute)
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call("set_phase", {"phase": "delve"}, call_id="tc1"),
                    _tool_call("enter_dungeon", {"site_address": "23-A-UG-1"}, call_id="tc2"),
                ],
                "finish_reason": "tool_calls",
            },
            {"content": BENIGN_SURFACE, "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    narration = orchestrator.process_turn("enter the crypt")

    set_phase_result = orchestrator._last_tool_results.get("set_phase", {})
    if "hint" in set_phase_result:
        _assert_hint_phrases(set_phase_result["hint"])
    assert "[Mechanics failed" not in narration
    assert "do not use set_phase to enter a site" not in narration.lower()


def test_system_tool_failed_message_includes_hint(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    _mock_set_phase_delve_fail(orchestrator, monkeypatch)

    messages: list[dict] = [{"role": "user", "content": "go down"}]
    queue = [
        {
            "content": "",
            "tool_calls": [_tool_call("set_phase", {"phase": "delve"})],
            "finish_reason": "tool_calls",
        },
    ]

    def fake_chat_completion(client, **kwargs):
        if not queue:
            raise RuntimeError("LLM response queue exhausted")
        resp = queue.pop(0)
        tool_calls = resp.get("tool_calls") or []
        return {
            "content": resp.get("content", ""),
            "tool_calls": tool_calls,
            "finish_reason": resp.get(
                "finish_reason",
                "tool_calls" if tool_calls else "stop",
            ),
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat_completion)

    orchestrator._llm_loop(messages)

    system_msgs = [m for m in messages if m.get("role") == "system"]
    assert system_msgs
    combined = " ".join(m["content"] for m in system_msgs)
    assert "TOOL FAILED (set_phase)" in combined
    _assert_hint_phrases(combined)
