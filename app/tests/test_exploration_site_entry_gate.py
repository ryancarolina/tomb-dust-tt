"""APP-024: block site-entry fiction without successful enter_dungeon / site_enter."""

from __future__ import annotations

import json

import pytest

from gm.orchestrator import (
    _SITE_ENTRY_REFUSAL_LINE,
    sanitize_premature_site_entry_flavor,
)

ENTRY_PROSE = "You step into the torchlit crypt. Corridors stretch ahead."
BENIGN_SURFACE = "The clerk stamps your permit. Wind off the salt road."
QUEST_SITE_DIRECTION = "Breley Undercrypt lies beneath the keep."
NPC_PAST_TENSE_UNDERCRYPT = "He went down into the undercrypt weeks ago."


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


def _surface_exploration_orchestrator(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    result = orchestrator.setup_new_game()
    assert result.get("ok"), result
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_restore_creation_from_session_state", lambda: None)
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)


def _patch_party_mode(monkeypatch: pytest.MonkeyPatch, orchestrator, mode: str) -> None:
    real_status = orchestrator.bridge.status

    def status() -> dict:
        st = dict(real_status())
        party = dict(st.get("party") or {})
        party["mode"] = mode
        st["party"] = party
        return st

    monkeypatch.setattr(orchestrator.bridge, "status", status)


def _assert_no_entry_markers(text: str) -> None:
    lower = text.lower()
    assert "torchlit" not in lower
    assert "corridor" not in lower
    assert "step into" not in lower


def test_sanitize_preserves_quest_site_name_direction():
    assert (
        sanitize_premature_site_entry_flavor(QUEST_SITE_DIRECTION, gate_active=True)
        == QUEST_SITE_DIRECTION
    )


def test_sanitize_preserves_npc_past_tense_undercrypt():
    assert (
        sanitize_premature_site_entry_flavor(NPC_PAST_TENSE_UNDERCRYPT, gate_active=True)
        == NPC_PAST_TENSE_UNDERCRYPT
    )


def test_sanitize_entry_prose_still_stripped():
    assert not sanitize_premature_site_entry_flavor(ENTRY_PROSE, gate_active=True).strip()


def test_sanitize_paragraph_ambiance_collapse():
    single_line = "Corridors stretch ahead."
    assert not sanitize_premature_site_entry_flavor(single_line, gate_active=True).strip()

    mixed = f"{QUEST_SITE_DIRECTION}\n\nCorridors stretch ahead."
    assert not sanitize_premature_site_entry_flavor(mixed, gate_active=True).strip()


def test_sanitize_premature_site_entry_flavor_unit():
    assert sanitize_premature_site_entry_flavor(BENIGN_SURFACE, gate_active=True) == BENIGN_SURFACE
    assert sanitize_premature_site_entry_flavor(BENIGN_SURFACE, gate_active=False) == BENIGN_SURFACE

    stripped = sanitize_premature_site_entry_flavor(ENTRY_PROSE, gate_active=True)
    assert not stripped.strip()
    assert sanitize_premature_site_entry_flavor(ENTRY_PROSE, gate_active=False) == ENTRY_PROSE

    mixed = f"{ENTRY_PROSE}\n\n{BENIGN_SURFACE}"
    out = sanitize_premature_site_entry_flavor(mixed, gate_active=True)
    assert BENIGN_SURFACE in out
    _assert_no_entry_markers(out)


def test_surface_no_tool_entry_fiction_stripped(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    _patch_llm_sequence(
        monkeypatch,
        [{"content": ENTRY_PROSE, "tool_calls": [], "finish_reason": "stop"}],
    )

    narration = orchestrator.process_turn("I enter the crypt.")

    _assert_no_entry_markers(narration)
    assert _SITE_ENTRY_REFUSAL_LINE in narration
    assert (orchestrator.bridge.status().get("party") or {}).get("mode") == "surface"


def test_surface_failed_enter_dungeon_no_entry_fiction(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: {"ok": False, "error": "missing site_address"},
    )
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": ENTRY_PROSE,
                "tool_calls": [_tool_call("enter_dungeon")],
                "finish_reason": "tool_calls",
            },
        ],
    )

    narration = orchestrator.process_turn("enter the undercrypt")

    assert "[Mechanics failed" in narration
    _assert_no_entry_markers(narration)
    assert _SITE_ENTRY_REFUSAL_LINE in narration


def test_surface_successful_enter_dungeon_allows_fiction(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: {"ok": True, "mode": "dungeon"},
    )
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [_tool_call("enter_dungeon", {"site_address": "23-A-UG-1"})],
                "finish_reason": "tool_calls",
            },
            {"content": ENTRY_PROSE, "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    narration = orchestrator.process_turn("enter the crypt")

    assert "torchlit" in narration.lower()
    assert "corridor" in narration.lower()


def test_success_then_failed_enter_dungeon_retains_fiction(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    calls = {"enter_dungeon": 0}

    def fake_execute(name, args):
        if name == "enter_dungeon":
            calls["enter_dungeon"] += 1
            if calls["enter_dungeon"] == 1:
                return {"ok": True, "mode": "dungeon"}
            return {"ok": False, "error": "bad retry"}
        return {"ok": False, "error": f"unexpected tool {name}"}

    monkeypatch.setattr(orchestrator, "_execute_tool", fake_execute)
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [_tool_call("enter_dungeon", {"site_address": "23-A-UG-1"}, call_id="tc1")],
                "finish_reason": "tool_calls",
            },
            {
                "content": ENTRY_PROSE,
                "tool_calls": [_tool_call("enter_dungeon", {}, call_id="tc2")],
                "finish_reason": "tool_calls",
            },
        ],
    )

    narration = orchestrator.process_turn("enter again")

    assert "torchlit" in narration.lower()
    assert orchestrator._entry_committed_this_turn is True
    assert orchestrator._last_tool_results["enter_dungeon"].get("ok") is False


def test_successful_site_enter_allows_fiction(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "surface")
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: {"ok": True, "mode": "site"},
    )
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [_tool_call("site_enter", {"site_address": "23-A"})],
                "finish_reason": "tool_calls",
            },
            {"content": ENTRY_PROSE, "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    narration = orchestrator.process_turn("enter the site")

    assert "torchlit" in narration.lower()
    assert orchestrator._entry_committed_this_turn is True


def test_site_entry_gate_bypass_when_in_dungeon(orchestrator, monkeypatch):
    _surface_exploration_orchestrator(orchestrator, monkeypatch)
    _patch_party_mode(monkeypatch, orchestrator, "dungeon")
    _patch_llm_sequence(
        monkeypatch,
        [{"content": ENTRY_PROSE, "tool_calls": [], "finish_reason": "stop"}],
    )

    narration = orchestrator.process_turn("I search the alcove.")

    assert ENTRY_PROSE in narration
    assert narration.count("[Location:") == 1
    assert "Awaiting:" in narration
