"""APP-028: combat tool failure narration — no false success fiction."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

BEAT_FAILURE = (
    "[Mechanics failed — combat start: monster JSON not found: grave-ghoul]\n\n"
    "Combat could not begin."
)


def _tool_call(name: str, args: dict, *, call_id: str = "call_1") -> list:
    return [
        {
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(args),
            },
        }
    ]


def _mock_chat_completion_once(
    monkeypatch,
    *,
    content: str,
    tool_name: str,
    tool_args: dict,
    call_id: str = "call_1",
) -> list:
    """Single chat_completion return with one tool call; count calls via list wrapper."""
    calls: list = []

    def _fake_chat_completion(*args, **kwargs):
        calls.append(kwargs)
        return {
            "content": content,
            "tool_calls": _tool_call(tool_name, tool_args, call_id=call_id),
            "finish_reason": "tool_calls",
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat_completion)
    return calls


def _mock_bridge_tool(monkeypatch, orchestrator, name: str, result: dict):
    """Patch orchestrator.bridge method for isolated tool result."""
    monkeypatch.setattr(orchestrator.bridge, name, MagicMock(return_value=result))


def _seed_exploration_messages(orchestrator) -> list:
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "look around"},
    ]


@pytest.fixture
def exploration_ready(orchestrator):
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    assert orchestrator.bridge.status().get("combat") is None
    return orchestrator


# ─── T1 ───────────────────────────────────────────────────────────────────


def test_handle_combat_trigger_returns_failure_string(orchestrator, monkeypatch):
    beat_result = {
        "mechanical_summary": [
            {"action": "combat_trigger", "monster_specs": ["grave-ghoul:1"]},
        ],
    }
    monkeypatch.setattr(
        orchestrator.bridge,
        "start_combat",
        MagicMock(return_value={"ok": False, "error": "monster JSON not found: grave-ghoul"}),
    )
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)
    run_turns = MagicMock()
    monkeypatch.setattr(orchestrator.bridge, "run_combat_monster_turns", run_turns)

    result = orchestrator._handle_combat_trigger(beat_result)

    assert result == BEAT_FAILURE
    assert orchestrator.combat.active is False
    orchestrator.bridge.start_combat.assert_called_once()
    run_turns.assert_not_called()


# ─── T2 ───────────────────────────────────────────────────────────────────


def test_beat_trigger_e2e_llm_loop_short_circuits(exploration_ready, monkeypatch):
    calls = _mock_chat_completion_once(
        monkeypatch,
        content="Ghouls leap from the crypt.",
        tool_name="process_beat",
        tool_args={},
    )
    beat_result = {
        "ok": True,
        "mechanical_summary": [
            {"action": "combat_trigger", "monster_specs": ["grave-ghoul:1"]},
        ],
    }
    monkeypatch.setattr(
        exploration_ready.bridge,
        "process_beat",
        MagicMock(return_value=beat_result),
    )
    monkeypatch.setattr(
        exploration_ready.bridge,
        "start_combat",
        MagicMock(return_value={"ok": False, "error": "monster JSON not found: grave-ghoul"}),
    )
    monkeypatch.setattr(exploration_ready, "_combat_active_in_db", lambda: False)

    result = exploration_ready._llm_loop(_seed_exploration_messages(exploration_ready))

    assert result == BEAT_FAILURE
    assert "Ghouls" not in result
    assert len(calls) == 1
    assert exploration_ready.bridge.status().get("combat") is None


# ─── T3–T7 ────────────────────────────────────────────────────────────────

_LLM_LOOP_ALL_FAILED_CASES = [
    (
        "start_combat",
        "monster JSON not found: hollow-knight",
        ["initiative", "charge"],
        "Enemies charge with initiative!",
    ),
    (
        "combat_attack",
        "attacker not in combat",
        ["damage", "hit"],
        "Your blade hits for 12 damage.",
    ),
    (
        "combat_end",
        "no active combat",
        ["combat ended", "victory"],
        "Combat ended in victory!",
    ),
    (
        "cast_spell",
        "not in combat",
        ["spell damage", "effect"],
        "Arcane spell damage erupts with magical effect.",
    ),
    (
        "fortune_spend",
        "no Fortune remaining",
        ["Fortune spent", "reroll"],
        "Fortune spent on a reroll.",
    ),
]


@pytest.mark.parametrize(
    "tool_name,error,banned,content",
    _LLM_LOOP_ALL_FAILED_CASES,
    ids=[c[0] for c in _LLM_LOOP_ALL_FAILED_CASES],
)
def test_llm_loop_all_failed_strips_content(
    exploration_ready, monkeypatch, tool_name, error, banned, content
):
    _mock_chat_completion_once(
        monkeypatch,
        content=content,
        tool_name=tool_name,
        tool_args={},
    )
    monkeypatch.setattr(
        exploration_ready.bridge,
        tool_name,
        MagicMock(return_value={"ok": False, "error": error}),
    )

    result = exploration_ready._llm_loop(_seed_exploration_messages(exploration_ready))

    assert result.startswith(f"[Mechanics failed — {tool_name}:")
    for word in banned:
        assert word.lower() not in result.lower()
    # No assistant fiction appended after prefix
    assert "\n\n" + content.split(".")[0] not in result
    if "\n\n" in result:
        after_prefix = result.split("\n\n", 1)[1]
        for word in banned:
            assert word.lower() not in after_prefix.lower()


# ─── T8 ───────────────────────────────────────────────────────────────────


def test_combat_inner_all_failed_strips_content(orchestrator, monkeypatch):
    orchestrator.combat.active = True
    hit_fiction = "Your sword strikes true for 15 damage!"
    calls: list = []

    def _fake_chat(*args, **kwargs):
        calls.append(1)
        return {
            "content": hit_fiction,
            "tool_calls": _tool_call(
                "combat_action",
                {"action": "attack", "actor_id": "pc1", "target_id": "m1"},
            ),
            "finish_reason": "tool_calls",
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat)
    monkeypatch.setattr(
        orchestrator,
        "_execute_combat_action",
        MagicMock(return_value={"ok": False, "error": "not your turn"}),
    )

    messages = [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}]
    result = orchestrator._combat_llm_loop_inner(messages, depth=0)

    assert "[Mechanics failed" in result
    assert "damage" not in result.lower()
    assert "hit" not in result.lower()
    assert hit_fiction not in result
    assert len(calls) == 1


# ─── T9 ───────────────────────────────────────────────────────────────────


def test_combat_inner_wrong_tool_failure(orchestrator, monkeypatch):
    orchestrator.combat.active = True

    def _fake_chat(*args, **kwargs):
        return {
            "content": "You swing and connect!",
            "tool_calls": _tool_call("start_combat", {"monster_specs": ["ghoul:1"]}),
            "finish_reason": "tool_calls",
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat)

    messages = [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}]
    result = orchestrator._combat_llm_loop_inner(messages, depth=0)

    assert "[Mechanics failed" in result
    assert "connect" not in result.lower()
    assert "start_combat" in result


# ─── T10 ──────────────────────────────────────────────────────────────────


def test_combat_inner_partial_failure_injects_tool_failed(orchestrator, monkeypatch):
    orchestrator.combat.active = True
    call_count = {"n": 0}

    def _execute_side_effect(**kwargs):
        if kwargs.get("action") == "attack":
            return {"ok": False, "error": "invalid target"}
        return {"ok": True, "mechanical": [{"action": "combat_attack", "hit": True, "damage": 5}]}

    monkeypatch.setattr(orchestrator, "_execute_combat_action", _execute_side_effect)
    monkeypatch.setattr(orchestrator, "_combat_auto_chain", lambda: [])
    monkeypatch.setattr(orchestrator, "_sync_combat_from_status", lambda: None)

    def _fake_chat(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return {
                "content": "You strike twice.",
                "tool_calls": [
                    *_tool_call(
                        "combat_action",
                        {"action": "attack", "actor_id": "pc1", "target_id": "bad"},
                        call_id="call_fail",
                    ),
                    *_tool_call(
                        "combat_action",
                        {"action": "defend", "actor_id": "pc1"},
                        call_id="call_ok",
                    ),
                ],
                "finish_reason": "tool_calls",
            }
        return {"content": "You recover and defend.", "tool_calls": [], "finish_reason": "stop"}

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat)

    messages = [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}]
    result = orchestrator._combat_llm_loop_inner(messages, depth=0)

    assert "[Mechanics failed" not in result
    tool_failed_idx = None
    tool_result_idx = None
    for i, msg in enumerate(messages):
        if msg.get("role") == "system" and "TOOL FAILED (combat_action)" in msg.get("content", ""):
            tool_failed_idx = i
        if msg.get("role") == "tool" and "invalid target" in msg.get("content", ""):
            tool_result_idx = i
    assert tool_failed_idx is not None
    assert tool_result_idx is not None
    assert tool_failed_idx < tool_result_idx


# ─── T11 ──────────────────────────────────────────────────────────────────


def test_all_failed_or_beat_failure_logs(exploration_ready, monkeypatch):
    log_calls: list = []

    def _spy_log_error(context, message):
        log_calls.append((context, message))

    monkeypatch.setattr("gm.orchestrator.log_error", _spy_log_error)
    _mock_chat_completion_once(
        monkeypatch,
        content="Ghouls leap from the crypt.",
        tool_name="process_beat",
        tool_args={},
    )
    beat_result = {
        "ok": True,
        "mechanical_summary": [
            {"action": "combat_trigger", "monster_specs": ["grave-ghoul:1"]},
        ],
    }
    monkeypatch.setattr(
        exploration_ready.bridge,
        "process_beat",
        MagicMock(return_value=beat_result),
    )
    monkeypatch.setattr(
        exploration_ready.bridge,
        "start_combat",
        MagicMock(return_value={"ok": False, "error": "monster JSON not found: grave-ghoul"}),
    )
    monkeypatch.setattr(exploration_ready, "_combat_active_in_db", lambda: False)

    exploration_ready._llm_loop(_seed_exploration_messages(exploration_ready))

    assert any(ctx == "llm_loop" for ctx, _ in log_calls)
