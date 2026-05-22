"""APP-052: Release smoke — new game → creation → surface beat → save → resume.

Headless orchestrator path with isolated workspace; no OpenRouter key required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from test_creation_flow import FIXED_ROLL, INPUTS
from test_encounter_awareness import _patch_llm_sequence, _tool_call
from test_engine_status_on_save import headless_app, read_save, save_path  # noqa: F401


def _patch_session_state_path(orchestrator, save_path: Path) -> None:
    orchestrator._session_state_path = lambda: save_path  # type: ignore[method-assign]


def _roll_attributes_patch(monkeypatch: pytest.MonkeyPatch, orchestrator) -> None:
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )


def _complete_creation(orchestrator, monkeypatch: pytest.MonkeyPatch) -> str:
    """Run canonical creation INPUTS; return last narration line."""
    _roll_attributes_patch(monkeypatch, orchestrator)
    last = ""
    for text, expected_step in INPUTS:
        last = orchestrator.process_turn(text)
        assert orchestrator.creation.step == expected_step, (
            f"After {text!r}: step={orchestrator.creation.step}, expected {expected_step}"
        )
    return last


def _run_surface_beat(orchestrator, monkeypatch: pytest.MonkeyPatch) -> tuple[str, list]:
    """One exploration turn on surface (32-C) via mock LLM process_beat."""
    beat_calls: list[dict] = []
    real_process_beat = orchestrator.bridge.process_beat

    def _tracking_process_beat(**kwargs):
        beat_calls.append(kwargs)
        return real_process_beat(**kwargs)

    monkeypatch.setattr(orchestrator.bridge, "process_beat", _tracking_process_beat)
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call(
                        "process_beat",
                        {"lines": [{"slot": "P1", "raw": "look around the registry yard"}]},
                    )
                ],
                "finish_reason": "tool_calls",
            },
            {"content": "Lantern smoke curls along the bailey stones.", "tool_calls": []},
        ],
    )

    narration = orchestrator.process_turn("look around the registry yard")
    return narration, beat_calls


def test_release_smoke_new_game_through_save_resume(
    headless_app, orchestrator, save_path, monkeypatch
):
    """APP-052: full release path without live OpenRouter or PyGame window."""
    _complete_creation(orchestrator, monkeypatch)

    status = orchestrator.bridge.status()
    assert orchestrator.creation.active is False
    assert len(status.get("roster") or []) >= 1
    assert status.get("awaiting") == "PLAYER_ACTIONS"
    party = status.get("party") or {}
    assert party.get("address") == "32-C"
    assert party.get("mode") == "surface"
    assert party.get("phase") == "preparation"
    assert orchestrator.bridge.has_save() is True

    beat_narration, beat_calls = _run_surface_beat(orchestrator, monkeypatch)
    assert beat_calls, "surface beat should invoke process_beat"
    assert beat_narration.strip()

    delver_name = status["roster"][0]["display_name"]
    _patch_session_state_path(orchestrator, save_path)
    headless_app.narration.lines.append({"text": beat_narration[:500], "voice": "gm"})
    headless_app._save_session()

    assert save_path.is_file()
    saved = read_save(save_path)
    assert saved.get("engine_status") is not None
    assert len(saved["engine_status"].get("roster") or []) >= 1
    assert saved["engine_status"]["roster"][0]["display_name"] == delver_name
    # Post-finalize saves omit creation_state (export returns None when inactive).
    assert saved.get("creation_state") is None

    orchestrator.history.clear()
    headless_app._load_session()
    assert len(headless_app.narration.lines) >= 1

    resume_narration = orchestrator.process_turn("load game")
    assert "no saved" not in resume_narration.lower()
    assert "no save session found" not in resume_narration.lower()

    resumed = orchestrator.bridge.status()
    assert len(resumed.get("roster") or []) >= 1
    assert resumed["roster"][0]["display_name"] == delver_name
    assert resumed.get("awaiting") == "PLAYER_ACTIONS"
    assert (resumed.get("party") or {}).get("mode") == "surface"

    reloaded = read_save(save_path)
    assert reloaded.get("engine_status") is not None
    assert reloaded["engine_status"]["roster"][0]["display_name"] == delver_name
