"""APP-051: Golden path — mock LLM creation → enter undercrypt → one beat."""

from __future__ import annotations

import json

import pytest

from test_creation_flow import FIXED_ROLL, INPUTS

SITE_ID = "32-C-UG-1"


def _tool_call(name: str, args: dict | None = None, *, call_id: str = "tc1") -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args or {}),
        },
    }


def _patch_llm_sequence(monkeypatch: pytest.MonkeyPatch, responses: list[dict]) -> None:
    queue = list(responses)

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


def complete_mock_creation(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the canonical Dumpy apprentice creation loop with fixed rolls."""
    drift_events: list[dict] = []
    monkeypatch.setattr(
        "gm.orchestrator.log_creation_drift",
        lambda data: drift_events.append(data),
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )

    for text, expected_step in INPUTS:
        orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step, (
            f"After {text!r}: step={orchestrator.creation.step}, expected {expected_step}"
        )

    assert drift_events == [], f"unexpected creation_drift: {drift_events}"
    assert orchestrator.creation.active is False
    assert orchestrator.creation.step == "WORLD_INTRO"

    status = orchestrator.bridge.status()
    assert len(status["roster"]) >= 1
    assert status["awaiting"] == "PLAYER_ACTIONS"
    assert status["roster"][0]["display_name"] == "Dumpy"
    party = status["party"]
    assert party["address"] == "32-C"
    assert party["phase"] == "preparation"
    assert party["mode"] == "surface"


@pytest.fixture
def golden_path_creation(orchestrator, monkeypatch):
    """Post-creation orchestrator: roster exists, Breley surface, mock LLM only."""
    complete_mock_creation(orchestrator, monkeypatch)
    yield orchestrator


def test_golden_path_creation_enter_undercrypt_one_beat(golden_path_creation, monkeypatch):
    orchestrator = golden_path_creation

    tools_seen: list[str] = []
    real_execute = orchestrator._execute_tool

    def tracking_execute(name: str, args: dict) -> dict:
        tools_seen.append(name)
        return real_execute(name, args)

    monkeypatch.setattr(orchestrator, "_execute_tool", tracking_execute)

    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call("enter_dungeon", {"site_address": SITE_ID}, call_id="tc-enter"),
                ],
                "finish_reason": "tool_calls",
            },
            {
                "content": "Cold air rises from the undercrypt stair.",
                "tool_calls": [],
                "finish_reason": "stop",
            },
        ],
    )

    enter_narration = orchestrator.process_turn("enter the undercrypt")

    party = orchestrator.bridge.status()["party"]
    assert party["mode"] == "dungeon"
    assert party["site_id"] == SITE_ID
    assert party["phase"] == "delve"
    assert "enter_dungeon" in tools_seen
    assert "Cold air" in enter_narration or "Test narration." in enter_narration

    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call(
                        "process_beat",
                        {"lines": [{"raw": "I look around the antechamber"}]},
                        call_id="tc-beat",
                    ),
                ],
                "finish_reason": "tool_calls",
            },
            {
                "content": "Torchlight catches worn stone and iron brackets.",
                "tool_calls": [],
                "finish_reason": "stop",
            },
        ],
    )

    beat_narration = orchestrator.process_turn("I look around")

    assert "process_beat" in tools_seen
    assert orchestrator.bridge.status()["party"]["mode"] == "dungeon"
    assert orchestrator.bridge.status()["party"]["site_id"] == SITE_ID
    assert orchestrator.bridge.status().get("combat") is None
    assert "Torchlight" in beat_narration or "Test narration." in beat_narration

    beat_result = orchestrator._last_tool_results.get("process_beat") or {}
    assert beat_result.get("ok") is True
    mechanical = beat_result.get("mechanical_summary") or []
    assert any(m.get("action") == "look" for m in mechanical)
