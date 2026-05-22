"""APP-034: structured api_error JSONL on _chat_completion failures."""

from __future__ import annotations

import json

import httpx
import pytest
from openai import BadRequestError

from gm.logger import (
    REDACTED,
    extract_tool_chain,
    redact_secrets,
    summarize_messages_for_log,
)
from tests.test_transcript_400_retry import (
    GOOGLE_MALFORMED_MSG,
    HOLT_DEPTH1_MESSAGES,
    _bad_request_400,
)
from tests.test_transcript_sanitize import _tool_call


@pytest.fixture
def captured_logs(monkeypatch):
    entries: list[tuple[str, dict]] = []

    def _capture(entry_type, data):
        entries.append((entry_type, data if isinstance(data, dict) else {"raw": data}))

    monkeypatch.setattr("gm.logger.log_entry", _capture)
    return entries


# ─── U1–U3 redaction ──────────────────────────────────────────────────────


def test_redact_secrets_openrouter_key():
    out = redact_secrets("Error sk-or-v1-abc123secret")
    assert REDACTED in out
    assert "sk-or-v1-abc123secret" not in out


def test_redact_secrets_bearer():
    out = redact_secrets("Authorization: Bearer eyJhbG.token")
    assert "Bearer [REDACTED]" in out
    assert "eyJhbG.token" not in out


def test_redact_secrets_nested_dict():
    out = redact_secrets({
        "api_key": "sk-or-x",
        "nested": {"authorization": "Bearer z"},
    })
    assert out["api_key"] == REDACTED
    assert out["nested"]["authorization"] == REDACTED


# ─── U4–U5 serialization ──────────────────────────────────────────────────


def test_summarize_messages_tool_calls():
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": _tool_call("remember_fact", {"fact": "x" * 300, "importance": 3}),
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "{}"},
        {"role": "tool", "tool_call_id": "call_2", "content": "{}"},
    ]
    messages[0]["tool_calls"].append({
        "id": "call_2",
        "type": "function",
        "function": {"name": "travel", "arguments": json.dumps({"to": "23-A"})},
    })

    summary = summarize_messages_for_log(messages)
    assert summary[0]["role"] == "assistant"
    assert len(summary[0]["tool_calls"]) == 2
    for tc in summary[0]["tool_calls"]:
        assert tc["id"] in ("call_1", "call_2")
        assert tc["name"] in ("remember_fact", "travel")
        assert len(tc["arguments_preview"]) <= 120
    assert summary[1]["tool_call_id"] == "call_1"
    assert summary[2]["tool_call_id"] == "call_2"


def test_extract_tool_chain_order():
    messages = [
        {"role": "user", "content": "go"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": _tool_call("remember_fact", {"fact": "a"}, call_id="c1"),
        },
        {"role": "tool", "tool_call_id": "c1", "content": "{}"},
        {"role": "system", "content": "interstitial"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": _tool_call("travel", {"to": "23-A"}, call_id="c2"),
        },
        {"role": "tool", "tool_call_id": "c2", "content": '{"ok": true}'},
    ]
    chain = extract_tool_chain(messages)
    assert len(chain) == 2
    assert chain[0]["assistant_tool_calls"] == [{"id": "c1", "name": "remember_fact"}]
    assert chain[0]["tool_results"] == [{"tool_call_id": "c1", "content_len": 2}]
    assert chain[1]["assistant_tool_calls"] == [{"id": "c2", "name": "travel"}]
    assert chain[1]["tool_results"][0]["tool_call_id"] == "c2"


# ─── I1–I5 integration ────────────────────────────────────────────────────


def test_log_api_error_on_unrelated_400(orchestrator, monkeypatch, captured_logs):
    def fake_chat(client, **kwargs):
        raise _bad_request_400("invalid model: foo")

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            context="llm_loop",
            depth=1,
        )

    api_errors = [(t, d) for t, d in captured_logs if t == "api_error"]
    assert len(api_errors) == 1
    _, data = api_errors[0]
    assert data["context"] == "llm_loop"
    assert data["attempt"] == 1
    assert data["malformed_transcript_400"] is False
    assert data["depth"] == 1


def test_log_api_error_malformed_400_twice(orchestrator, monkeypatch, captured_logs):
    call_count = 0

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        raise _bad_request_400(GOOGLE_MALFORMED_MSG)

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(
            messages=HOLT_DEPTH1_MESSAGES,
            context="llm_loop",
            depth=1,
        )

    api_errors = [(t, d) for t, d in captured_logs if t == "api_error"]
    assert len(api_errors) == 1
    _, data = api_errors[0]
    assert data["attempt"] == 2
    assert data.get("retry_truncated") is True
    assert data["sent_len"] < data["original_len"]
    assert call_count == 2


def test_malformed_400_retry_success_no_api_error(orchestrator, monkeypatch, captured_logs):
    call_count = 0

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise _bad_request_400(GOOGLE_MALFORMED_MSG)
        return {"content": "ok", "tool_calls": [], "finish_reason": "stop"}

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    response = orchestrator._chat_completion(
        messages=HOLT_DEPTH1_MESSAGES,
        context="llm_loop",
    )

    assert response["content"] == "ok"
    assert not any(t == "api_error" for t, _ in captured_logs)
    assert any(t == "transcript_400_retry" for t, _ in captured_logs)


def test_chat_completion_passes_context_depth(orchestrator, monkeypatch):
    captured: list[dict] = []

    def spy_log_api_error(data):
        captured.append(data)

    def fake_chat(client, **kwargs):
        raise _bad_request_400("server error")

    monkeypatch.setattr("gm.orchestrator.log_api_error", spy_log_api_error)
    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(
            messages=[{"role": "user", "content": "travel"}],
            tools=[],
            context="llm_loop",
            depth=2,
        )

    assert len(captured) == 1
    assert captured[0]["context"] == "llm_loop"
    assert captured[0]["depth"] == 2


def test_logger_never_raises(orchestrator, monkeypatch):
    def broken_log_entry(*args, **kwargs):
        raise OSError("disk full")

    def fake_chat(client, **kwargs):
        raise _bad_request_400("invalid model: foo")

    monkeypatch.setattr("gm.logger.log_entry", broken_log_entry)
    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            context="llm_loop",
        )


# ─── I6–I9 combat + dedupe ────────────────────────────────────────────────


def test_combat_tools_failure_logged(orchestrator, monkeypatch, captured_logs):
    orchestrator.combat.active = True

    def fake_chat(client, **kwargs):
        raise _bad_request_400("server error")

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    messages = [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}]
    result = orchestrator._combat_llm_loop_inner(messages, depth=0)

    assert "[Mechanics failed — API error:" in result
    api_errors = [d for t, d in captured_logs if t == "api_error"]
    assert len(api_errors) == 1
    assert api_errors[0]["context"] == "combat_tools"
    assert api_errors[0]["depth"] == 0


def test_combat_narrate_failure_logged(orchestrator, monkeypatch, captured_logs):
    orchestrator.combat.active = True
    call_n = 0

    def fake_chat(client, **kwargs):
        nonlocal call_n
        call_n += 1
        if call_n == 1:
            return {
                "content": "",
                "tool_calls": _tool_call(
                    "combat_action",
                    {"action": "attack", "actor_id": "pc1", "target_id": "m1"},
                ),
                "finish_reason": "tool_calls",
            }
        raise _bad_request_400("server error")

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)
    monkeypatch.setattr(
        orchestrator,
        "_execute_combat_action",
        lambda **kw: {"ok": True, "mechanical": [{"action": "combat_attack", "hit": True}]},
    )
    monkeypatch.setattr(orchestrator, "_combat_auto_chain", lambda: [])
    monkeypatch.setattr(orchestrator, "_sync_combat_from_status", lambda: None)

    messages = [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}]
    orchestrator._combat_llm_loop_inner(messages, depth=0)

    api_errors = [d for t, d in captured_logs if t == "api_error"]
    assert len(api_errors) == 1
    assert api_errors[0]["context"] == "combat_narrate"


def test_no_duplicate_log_error_on_llm_loop_fail(orchestrator, monkeypatch, captured_logs):
    log_error_calls: list[tuple[str, str]] = []

    def spy_log_error(context, error):
        log_error_calls.append((context, error))

    def fake_chat(client, **kwargs):
        raise _bad_request_400("invalid model: foo")

    monkeypatch.setattr("gm.orchestrator.log_error", spy_log_error)
    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "look around"}]
    result = orchestrator._llm_loop(messages, depth=0)

    assert "The GM falters. (API error:" in result
    assert not any(ctx == "chat_completion" for ctx, _ in log_error_calls)
    api_errors = [d for t, d in captured_logs if t == "api_error"]
    assert len(api_errors) == 1
    assert api_errors[0]["context"] == "llm_loop"


def test_tool_chain_on_400_with_tools(orchestrator, monkeypatch, captured_logs):
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "remember"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": _tool_call("remember_fact", {"fact": "test", "importance": 3}),
        },
        {"role": "tool", "tool_call_id": "call_1", "content": '{"ok": true}'},
    ]

    def fake_chat(client, **kwargs):
        raise _bad_request_400("invalid model: foo")

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(messages=messages, tools=[], context="llm_loop", depth=0)

    api_errors = [d for t, d in captured_logs if t == "api_error"]
    assert len(api_errors) == 1
    data = api_errors[0]
    assert data["tool_chain"]
    assert data["tool_chain"][0]["assistant_tool_calls"][0]["name"] == "remember_fact"
    tool_rows = [row for row in data["messages_summary"] if row.get("role") == "tool"]
    assert tool_rows
    assert tool_rows[0].get("tool_call_id") == "call_1"
