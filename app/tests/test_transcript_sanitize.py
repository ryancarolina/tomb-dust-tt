"""APP-031: transcript sanitize before every orchestrator chat_completion."""

from __future__ import annotations

import json

import pytest

from gm.orchestrator import sanitize_transcript_messages


def assert_transcript_invariants(messages: list[dict]) -> None:
    """Every tool row has matching id on nearest preceding assistant tool_calls."""
    pending_ids: set[str] | None = None
    for msg in messages:
        role = msg.get("role")
        if role == "assistant":
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                pending_ids = {tc["id"] for tc in tool_calls}
            else:
                pending_ids = None
        elif role == "tool":
            tool_id = msg.get("tool_call_id")
            assert pending_ids is not None, "orphan tool message"
            assert tool_id in pending_ids, f"tool {tool_id!r} not in pending {pending_ids!r}"
            pending_ids.discard(tool_id)
            if not pending_ids:
                pending_ids = None


def _tool_call(name: str, args: dict, *, call_id: str = "call_1") -> list[dict]:
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


def _tool_result(call_id: str, result: dict | str = "{}") -> dict:
    content = result if isinstance(result, str) else json.dumps(result)
    return {"role": "tool", "tool_call_id": call_id, "content": content}


def _assistant_tool_round(
    *calls: tuple[str, dict, str],
    content: str | None = None,
) -> tuple[dict, list[dict]]:
    tool_calls = [
        {
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)},
        }
        for name, args, call_id in calls
    ]
    assistant = {"role": "assistant", "content": content, "tool_calls": tool_calls}
    tools = [_tool_result(call_id) for _, _, call_id in calls]
    return assistant, tools


# ─── T1 ───────────────────────────────────────────────────────────────────


def test_orphan_tool_no_preceding_assistant():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "tool", "tool_call_id": "x", "content": "{}"},
    ]
    out = sanitize_transcript_messages(messages)
    assert out == [{"role": "user", "content": "hello"}]
    assert_transcript_invariants(out)


# ─── T2 ───────────────────────────────────────────────────────────────────


def test_assistant_empty_tool_calls_followed_by_tool():
    messages = [
        {"role": "assistant", "content": "thinking", "tool_calls": []},
        {"role": "tool", "tool_call_id": "x", "content": "{}"},
    ]
    out = sanitize_transcript_messages(messages)
    assert out == [{"role": "assistant", "content": "thinking"}]
    assert_transcript_invariants(out)


# ─── T3 ───────────────────────────────────────────────────────────────────


def test_invalid_tool_call_missing_id():
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "", "function": {"name": "remember_fact", "arguments": "{}"}}],
        },
        _tool_result("c1"),
    ]
    out = sanitize_transcript_messages(messages)
    assert out == []
    assert_transcript_invariants(out)


# ─── T4 ───────────────────────────────────────────────────────────────────


def test_valid_two_tool_chain():
    assistant, tools = _assistant_tool_round(
        ("remember_fact", {"fact": "a"}, "c1"),
        ("travel", {"destination": "32-C"}, "c2"),
        content="",
    )
    messages = [assistant, *tools]
    out = sanitize_transcript_messages(messages)
    assert len(out) == 3
    assert out[0]["tool_calls"][0]["id"] == "c1"
    assert out[0]["tool_calls"][1]["id"] == "c2"
    assert out[1]["tool_call_id"] == "c1"
    assert out[2]["tool_call_id"] == "c2"
    assert out is not messages
    assert all(out[i] is not messages[i] for i in range(3))
    assert out[0]["tool_calls"] == messages[0]["tool_calls"]
    assert_transcript_invariants(out)


# ─── T5 ───────────────────────────────────────────────────────────────────


def test_unmatched_tool_call_id():
    assistant, tools = _assistant_tool_round(("remember_fact", {}, "c1"))
    messages = [assistant, tools[0], _tool_result("wrong-id")]
    out = sanitize_transcript_messages(messages)
    assert len(out) == 2
    assert out[1]["tool_call_id"] == "c1"
    assert_transcript_invariants(out)


# ─── T6 ───────────────────────────────────────────────────────────────────


def test_system_between_assistant_and_tool():
    assistant, tools = _assistant_tool_round(("combat_action", {"action": "attack"}, "c1"))
    system_line = {
        "role": "system",
        "content": "TOOL FAILED (combat_action): {\"ok\": false}. You MUST narrate this failure honestly.",
    }
    messages = [assistant, system_line, tools[0]]
    out = sanitize_transcript_messages(messages)
    assert out[0]["role"] == "assistant"
    assert out[1]["role"] == "tool"
    assert out[2]["role"] == "system"
    assert "TOOL FAILED" in out[2]["content"]
    assert_transcript_invariants(out)


# ─── T7 ───────────────────────────────────────────────────────────────────


def test_holt_session_shape():
    empty_calls = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "remember Holt"},
        {"role": "assistant", "content": None, "tool_calls": []},
        _tool_result("c1"),
    ]
    out_empty = sanitize_transcript_messages(empty_calls)
    assert all(m.get("role") != "tool" for m in out_empty)
    assert out_empty == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "remember Holt"},
    ]
    assert_transcript_invariants(out_empty)

    missing_name = [
        {"role": "user", "content": "x"},
        {
            "role": "assistant",
            "content": "ok",
            "tool_calls": [{"id": "c1", "type": "function", "function": {"arguments": "{}"}}],
        },
        _tool_result("c1"),
    ]
    out_missing = sanitize_transcript_messages(missing_name)
    assert out_missing == [{"role": "user", "content": "x"}, {"role": "assistant", "content": "ok"}]
    assert_transcript_invariants(out_missing)


# ─── T8 ───────────────────────────────────────────────────────────────────


@pytest.fixture
def exploration_ready(orchestrator):
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    return orchestrator


def test_wrapper_called_in_llm_loop(exploration_ready, monkeypatch):
    call_index = 0
    captured_second: list[list[dict]] = []

    def fake_chat(*args, **kwargs):
        nonlocal call_index
        call_index += 1
        if call_index == 1:
            return {
                "content": "",
                "tool_calls": _tool_call("remember_fact", {"fact": "x", "importance": 3}, call_id="c1"),
                "finish_reason": "tool_calls",
            }
        captured_second.append(list(kwargs.get("messages", [])))
        return {"content": "Narration.", "tool_calls": [], "finish_reason": "stop"}

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)
    monkeypatch.setattr(
        exploration_ready,
        "_execute_tool",
        lambda name, args: {"ok": False, "error": "boom"},
    )

    result = exploration_ready._llm_loop(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "go"},
        ]
    )

    assert result == "Narration."
    assert len(captured_second) == 1
    second_messages = captured_second[0]
    assert_transcript_invariants(second_messages)
    assistant_idx = next(
        i for i, m in enumerate(second_messages)
        if m.get("role") == "assistant" and m.get("tool_calls")
    )
    assert second_messages[assistant_idx + 1]["role"] == "tool"
    assert second_messages[assistant_idx + 2]["role"] == "system"
    assert "TOOL FAILED" in second_messages[assistant_idx + 2]["content"]


# ─── T9 ───────────────────────────────────────────────────────────────────


def test_sanitize_does_not_mutate_caller_list():
    inner = {
        "role": "assistant",
        "content": "hi",
        "tool_calls": [{"id": "", "function": {"name": "x", "arguments": "{}"}}],
    }
    messages = [{"role": "user", "content": "u"}, inner]
    original_len = len(messages)
    original_calls = list(inner["tool_calls"])
    out = sanitize_transcript_messages(messages)
    assert len(messages) == original_len
    assert inner["tool_calls"] == original_calls
    assert out is not messages
    assert out[0] is not messages[0]


# ─── T10 ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("messages", "expected"),
    [
        ([{"role": "tool", "tool_call_id": "x", "content": "{}"}], []),
        (
            [
                {"role": "system", "content": "s"},
                {"role": "user", "content": "u"},
                {"role": "tool", "tool_call_id": "x", "content": "{}"},
            ],
            [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
        ),
        (
            [
                {"role": "system", "content": "s1"},
                {"role": "system", "content": "s2"},
                {"role": "user", "content": "u"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": "", "function": {"name": "x", "arguments": "{}"}}],
                },
                {"role": "tool", "tool_call_id": "bad", "content": "{}"},
            ],
            [
                {"role": "system", "content": "s1"},
                {"role": "system", "content": "s2"},
                {"role": "user", "content": "u"},
            ],
        ),
    ],
)
def test_tail_invalid_returns_safe_prefix(messages, expected):
    out = sanitize_transcript_messages(messages)
    assert out == expected
    for i, exp in enumerate(expected):
        assert out[i] == exp
        assert out[i] is not exp
