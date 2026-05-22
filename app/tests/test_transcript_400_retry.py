"""APP-032: reactive 400 retry on malformed transcript in _chat_completion."""

from __future__ import annotations

import copy
import json

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, BadRequestError, RateLimitError

from gm.orchestrator import (
    _safe_prefix_fallback,
    is_malformed_transcript_400,
    sanitize_transcript_messages,
)
from tests.test_transcript_sanitize import (
    _tool_call,
    assert_transcript_invariants,
)

GOOGLE_MALFORMED_MSG = (
    "Tool-call assistant message produced no valid function calls "
    "but is followed by tool result messages"
)


def _bad_request_400(message: str) -> BadRequestError:
    response = httpx.Response(400, request=httpx.Request("POST", "http://test"))
    return BadRequestError(message, body={}, response=response)


def _api_status_400(message: str) -> APIStatusError:
    response = httpx.Response(400, request=httpx.Request("POST", "http://test"))
    return APIStatusError(message, response=response, body={})


def _rate_limit_error() -> RateLimitError:
    response = httpx.Response(429, request=httpx.Request("POST", "http://test"))
    return RateLimitError("rate limit", response=response, body={})


def _connection_error() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "http://test"))


HOLT_DEPTH1_MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "remember and travel"},
    {"role": "assistant", "content": None, "tool_calls": []},
    {"role": "system", "content": "TOOL FAILED (remember_fact): boom"},
    {"role": "tool", "tool_call_id": "c1", "content": "{}"},
]


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (_bad_request_400(GOOGLE_MALFORMED_MSG), True),
        (
            _bad_request_400(
                "tool-call assistant message produced no valid function calls"
            ),
            True,
        ),
        (
            _bad_request_400("no valid function calls but is followed by tool"),
            True,
        ),
        (
            _bad_request_400("tool result messages require tool_calls alignment"),
            True,
        ),
        (
            _api_status_400("tool result messages with tool_calls mismatch"),
            True,
        ),
        (_bad_request_400("invalid model: foo"), False),
        (_bad_request_400("invalid_api_key"), False),
        (_bad_request_400("context_length exceeded"), False),
        (_bad_request_400("tool result messages only"), False),
        (_rate_limit_error(), False),
        (_connection_error(), False),
        (ValueError("tool-call assistant message produced no valid function calls"), False),
    ],
)
def test_is_malformed_transcript_400_cases(exc, expected):
    assert is_malformed_transcript_400(exc) is expected


def test_malformed_400_then_success(orchestrator, monkeypatch):
    call_count = 0
    captured_messages: list[list[dict]] = []

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        captured_messages.append(list(kwargs.get("messages", [])))
        if call_count == 1:
            raise _bad_request_400(GOOGLE_MALFORMED_MSG)
        return {"content": "ok", "tool_calls": [], "finish_reason": "stop"}

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    original = copy.deepcopy(HOLT_DEPTH1_MESSAGES)
    response = orchestrator._chat_completion(messages=HOLT_DEPTH1_MESSAGES)

    assert response["content"] == "ok"
    assert call_count == 2
    expected_retry = sanitize_transcript_messages(
        _safe_prefix_fallback(HOLT_DEPTH1_MESSAGES)
    )
    assert captured_messages[1] == expected_retry
    assert captured_messages[1] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "remember and travel"},
    ]
    assert_transcript_invariants(captured_messages[1])
    assert HOLT_DEPTH1_MESSAGES == original


def test_unrelated_400_no_retry(orchestrator, monkeypatch):
    call_count = 0

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        raise _bad_request_400("invalid model: foo")

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(messages=[{"role": "user", "content": "hi"}])

    assert call_count == 1


def test_malformed_400_twice_propagates(orchestrator, monkeypatch):
    call_count = 0
    captured_messages: list[list[dict]] = []

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        captured_messages.append(list(kwargs.get("messages", [])))
        raise _bad_request_400(GOOGLE_MALFORMED_MSG)

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(BadRequestError):
        orchestrator._chat_completion(messages=HOLT_DEPTH1_MESSAGES)

    assert call_count == 2
    expected_retry = sanitize_transcript_messages(
        _safe_prefix_fallback(HOLT_DEPTH1_MESSAGES)
    )
    assert captured_messages[1] == expected_retry
    assert_transcript_invariants(captured_messages[1])


@pytest.mark.parametrize(
    "exc_factory",
    [_rate_limit_error, _connection_error],
)
def test_non_400_no_retry(orchestrator, monkeypatch, exc_factory):
    call_count = 0

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        raise exc_factory()

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    with pytest.raises(type(exc_factory())):
        orchestrator._chat_completion(messages=[{"role": "user", "content": "hi"}])

    assert call_count == 1


def test_caller_messages_unchanged_after_retry(orchestrator, monkeypatch):
    inner = {"role": "assistant", "content": None, "tool_calls": []}
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "remember and travel"},
        inner,
        {"role": "system", "content": "TOOL FAILED (remember_fact): boom"},
        {"role": "tool", "tool_call_id": "c1", "content": "{}"},
    ]
    original_len = len(messages)
    original_tool_calls = list(inner["tool_calls"])
    call_count = 0

    def fake_chat(client, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise _bad_request_400(GOOGLE_MALFORMED_MSG)
        return {"content": "ok", "tool_calls": [], "finish_reason": "stop"}

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat)

    orchestrator._chat_completion(messages=messages)

    assert len(messages) == original_len
    assert inner["tool_calls"] == original_tool_calls
    assert messages[2] is inner


@pytest.fixture
def exploration_ready(orchestrator):
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    return orchestrator


def test_llm_loop_depth1_retry_integration(exploration_ready, monkeypatch):
    call_index = 0

    def fake_chat(client, **kwargs):
        nonlocal call_index
        call_index += 1
        if call_index == 1:
            return {
                "content": "",
                "tool_calls": _tool_call(
                    "remember_fact",
                    {"fact": "x", "importance": 3},
                    call_id="c1",
                ),
                "finish_reason": "tool_calls",
            }
        if call_index == 2:
            raise _bad_request_400(GOOGLE_MALFORMED_MSG)
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
    assert "The GM falters" not in result
    assert call_index == 3
