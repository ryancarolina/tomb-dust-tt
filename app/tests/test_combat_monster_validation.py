"""APP-027: monster spec validation at combat start (V1–V8)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from test_tool_args import _dispatch_like_llm_loop


def _ensure_salt_road_session(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("salt-road")
    assert start.get("ok")


@pytest.fixture
def bridge_with_session(bridge):
    _ensure_salt_road_session(bridge)
    return bridge


@pytest.fixture
def orchestrator_with_session(orchestrator):
    _ensure_salt_road_session(orchestrator.bridge)
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    assert orchestrator.bridge.status().get("combat") is None
    return orchestrator


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


def _mock_chat_completion_once(monkeypatch, *, content: str, tool_name: str, tool_args: dict):
    calls: list = []

    def _fake_chat_completion(*args, **kwargs):
        calls.append(kwargs)
        return {
            "content": content,
            "tool_calls": _tool_call(tool_name, tool_args),
            "finish_reason": "tool_calls",
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat_completion)
    return calls


def _seed_exploration_messages(orchestrator) -> list:
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "look around"},
    ]


def _seed_encounter_engaged(orchestrator, monkeypatch) -> str:
    """Dungeon encounter in engaged phase so APP-089 gate allows start_combat through."""
    site_id = "32-C-UG-1"
    room_id = "chapel-stairs"
    real_status = orchestrator.bridge.status

    def status() -> dict:
        st = dict(real_status())
        party = dict(st.get("party") or {})
        party["mode"] = "dungeon"
        party["site_id"] = site_id
        party["dungeon_room_id"] = room_id
        st["party"] = party
        st["combat"] = None
        return st

    monkeypatch.setattr(orchestrator.bridge, "status", status)
    key = f"{site_id}:{room_id}"
    orchestrator._encounter_by_room[key] = {
        "phase": "engaged",
        "threats": [{"monster_id": "grave-ghoul", "count": 1}],
    }
    return key


# --- V1–V3: bridge pre-check ---


def test_bridge_unknown_monster_id(bridge_with_session):
    result = bridge_with_session.start_combat(monster_specs=["hollow-knight:1"])
    assert result.get("ok") is False
    assert "monster JSON not found: hollow-knight" in str(result.get("error", ""))


def test_bridge_invalid_monster_spec_format(bridge_with_session):
    result = bridge_with_session.start_combat(monster_specs=["not a spec"])
    assert result.get("ok") is False
    assert "invalid monster spec" in str(result.get("error", ""))


def test_bridge_empty_monster_specs(bridge_with_session):
    result = bridge_with_session.start_combat(monster_specs=[])
    assert result.get("ok") is False
    assert "monster_specs required" in str(result.get("error", ""))


# --- V5: tool args gate before bridge ---


def test_llm_loop_empty_monster_specs_blocks_bridge(orchestrator_with_session, monkeypatch):
    mock_start = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(orchestrator_with_session.bridge, "start_combat", mock_start)

    result = _dispatch_like_llm_loop(
        orchestrator_with_session, "start_combat", {"monster_specs": []}
    )

    assert result.get("ok") is False
    assert "monster_specs required" in str(result.get("error", ""))
    mock_start.assert_not_called()


# --- V6: _execute_tool bypasses R3, hits bridge R2 ---


def test_execute_tool_unknown_monster_no_combat_state(orchestrator_with_session):
    result = orchestrator_with_session._execute_tool(
        "start_combat", {"monster_specs": ["hollow-knight:1"]}
    )
    assert result.get("ok") is False
    assert orchestrator_with_session.bridge.status().get("combat") is None


def test_execute_tool_unknown_monster_engaged_dungeon(
    orchestrator_with_session, monkeypatch
):
    _seed_encounter_engaged(orchestrator_with_session, monkeypatch)
    result = orchestrator_with_session._execute_tool(
        "start_combat", {"monster_specs": ["hollow-knight:1"]}
    )
    assert result.get("ok") is False
    assert "hollow-knight" in str(result.get("error", ""))
    assert orchestrator_with_session.bridge.status().get("combat") is None


# --- V7: beat trigger real bridge path ---


def test_handle_combat_trigger_unknown_monster(orchestrator_with_session, monkeypatch):
    beat_result = {
        "mechanical_summary": [
            {"action": "combat_trigger", "monster_specs": ["hollow-knight:1"]},
        ],
    }
    monkeypatch.setattr(orchestrator_with_session, "_combat_active_in_db", lambda: False)
    run_turns = MagicMock()
    monkeypatch.setattr(
        orchestrator_with_session.bridge, "run_combat_monster_turns", run_turns
    )

    result = orchestrator_with_session._handle_combat_trigger(beat_result)

    assert result is not None
    assert result.startswith("[Mechanics failed — combat start:")
    assert "monster JSON not found: hollow-knight" in result
    assert orchestrator_with_session.combat.active is False
    run_turns.assert_not_called()


def test_handle_combat_trigger_unknown_monster_engaged_dungeon(
    orchestrator_with_session, monkeypatch
):
    _seed_encounter_engaged(orchestrator_with_session, monkeypatch)
    beat_result = {
        "mechanical_summary": [
            {"action": "combat_trigger", "monster_specs": ["hollow-knight:1"]},
        ],
    }
    monkeypatch.setattr(orchestrator_with_session, "_combat_active_in_db", lambda: False)
    run_turns = MagicMock()
    monkeypatch.setattr(
        orchestrator_with_session.bridge, "run_combat_monster_turns", run_turns
    )

    result = orchestrator_with_session._handle_combat_trigger(beat_result)

    assert result is not None
    assert result.startswith("[Mechanics failed — combat start:")
    assert "monster JSON not found: hollow-knight" in result
    assert orchestrator_with_session.combat.active is False
    run_turns.assert_not_called()


# --- V8: _llm_loop integration with real bridge ---


def test_llm_loop_start_combat_unknown_strips_fiction(orchestrator_with_session, monkeypatch):
    fiction = "Enemies charge with initiative!"
    _mock_chat_completion_once(
        monkeypatch,
        content=fiction,
        tool_name="start_combat",
        tool_args={"monster_specs": ["hollow-knight:1"]},
    )

    result = orchestrator_with_session._llm_loop(
        _seed_exploration_messages(orchestrator_with_session)
    )

    assert result.startswith("[Mechanics failed — start_combat:")
    assert "hollow-knight" in result
    assert "initiative" not in result.lower()
    assert "charge" not in result.lower()
    assert orchestrator_with_session.bridge.status().get("combat") is None


def test_llm_loop_start_combat_unknown_engaged_dungeon(
    orchestrator_with_session, monkeypatch
):
    _seed_encounter_engaged(orchestrator_with_session, monkeypatch)
    fiction = "Enemies charge with initiative!"
    _mock_chat_completion_once(
        monkeypatch,
        content=fiction,
        tool_name="start_combat",
        tool_args={"monster_specs": ["hollow-knight:1"]},
    )

    result = orchestrator_with_session._llm_loop(
        _seed_exploration_messages(orchestrator_with_session)
    )

    assert result.startswith("[Mechanics failed — start_combat:")
    assert "hollow-knight" in result
    assert "initiative" not in result.lower()
    assert "charge" not in result.lower()
    assert orchestrator_with_session.bridge.status().get("combat") is None
