"""Tests for finish_reason length recovery (APP-079)."""

from __future__ import annotations

from gm.orchestrator import handle_finish_reason_length


def test_creation_length_discards_flavor_before_compose():
    recovery = handle_finish_reason_length(
        "length",
        "| Race | Adjustments |\n| Human | — |",
        body_pending=True,
        flavor_only=False,
        length_retries_left=1,
    )
    assert recovery.action == "discard"
    assert recovery.next_prose == ""


def test_creation_flavor_passes_max_tokens_500(orchestrator, monkeypatch):
    captured: dict = {}

    def fake_chat_completion(client, **kwargs):
        captured.update(kwargs)
        return {
            "content": "Brief flavor prose.",
            "tool_calls": [],
            "finish_reason": "stop",
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", fake_chat_completion)

    result = orchestrator._call_narration_llm([{"role": "user", "content": "flavor"}])

    assert captured.get("max_tokens") == 500
    assert result == "Brief flavor prose."


def test_skills_step_discards_truncated_flavor(orchestrator, monkeypatch):
    """Player sees code skills table only when LLM hits length mid-table."""
    orchestrator.creation.active = True
    orchestrator.creation.step = "SKILLS"
    orchestrator.creation.name = "Sumpty"
    orchestrator.creation.race = "undead"
    orchestrator.creation.chosen_class = "novice"
    orchestrator.creation.chosen_skills = []

    calls = {"n": 0}

    def _length_table(_messages):
        calls["n"] += 1
        orchestrator._last_finish_reason = "length"
        return "| Skill | Class key? |\n| Swordsmanship | |"

    monkeypatch.setattr(orchestrator, "_call_narration_llm", _length_table)

    narration = orchestrator._auto_present_skills("pick skills")

    assert "| Category | Skill | Class key? |" in narration
    assert narration.count("| Skill |") <= 1
    assert calls["n"] >= 1
