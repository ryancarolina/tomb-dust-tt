"""APP-089: encounter awareness FSM, contests, and combat gates (WS1 + WS2)."""

from __future__ import annotations

import json

import pytest

from gm.orchestrator import _ENCOUNTER_ENTRY_HINT, _ENCOUNTER_NOT_ENGAGED_HINT

ENEMY_FEATURES = [
    {
        "id": "feat-ghoul-1",
        "feature_type": "enemy",
        "display_name": "Grave Ghoul",
        "data_json": json.dumps({"monsterId": "grave-ghoul", "count": 1}),
    }
]

SITE_ID = "32-C-UG-1"
ROOM_ID = "chapel-stairs"


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


def _exploration_ready(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    result = orchestrator.setup_new_game()
    assert result.get("ok"), result
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    monkeypatch.setattr(orchestrator, "_restore_creation_from_session_state", lambda: None)
    monkeypatch.setattr(orchestrator, "_combat_active_in_db", lambda: False)


def _dungeon_party_status(
    orchestrator,
    monkeypatch: pytest.MonkeyPatch,
    *,
    site_id: str = SITE_ID,
    room_id: str = ROOM_ID,
) -> None:
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


def _seed_encounter(
    orchestrator,
    monkeypatch: pytest.MonkeyPatch,
    *,
    phase: str = "detected",
    site_id: str = SITE_ID,
    room_id: str = ROOM_ID,
) -> str:
    _dungeon_party_status(orchestrator, monkeypatch, site_id=site_id, room_id=room_id)
    key = f"{site_id}:{room_id}"
    orchestrator._encounter_by_room[key] = {
        "phase": phase,
        "threats": [{"monster_id": "grave-ghoul", "count": 1}],
    }
    return key


def test_enter_dungeon_enemy_sets_detected(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _dungeon_party_status(orchestrator, monkeypatch)

    monkeypatch.setattr(
        orchestrator.bridge,
        "enter_dungeon",
        lambda **kwargs: {"ok": True, "features": ENEMY_FEATURES},
    )

    result = orchestrator._execute_tool("enter_dungeon", {"site_address": SITE_ID})

    assert result.get("ok")
    assert result.get("encounter_hint") == _ENCOUNTER_ENTRY_HINT
    phase = orchestrator._current_encounter_phase(orchestrator.bridge.status())
    assert phase == "detected"
    assert not orchestrator._combat_active_in_db()


def test_start_combat_blocked_when_detected(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="detected")

    result = orchestrator._execute_tool(
        "start_combat",
        {"monster_specs": ["grave-ghoul:1"]},
    )

    assert not result.get("ok")
    assert result.get("error") == "ENCOUNTER_NOT_ENGAGED"
    assert _ENCOUNTER_NOT_ENGAGED_HINT in result.get("hint", "")
    assert not orchestrator._combat_active_in_db()


def test_hostile_input_promotes_engaged_before_tools(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="detected")

    tools_seen: list[str] = []
    real_execute = orchestrator._execute_tool

    def tracking_execute(name: str, args: dict) -> dict:
        tools_seen.append(name)
        if name == "process_beat":
            return {"ok": True, "mechanical_summary": []}
        return real_execute(name, args)

    monkeypatch.setattr(orchestrator, "_execute_tool", tracking_execute)
    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [_tool_call("process_beat", {"lines": ["look"]})],
                "finish_reason": "tool_calls",
            },
            {"content": "You raise your blade.", "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("I charge the ghoul")

    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "engaged"
    assert tools_seen and tools_seen[0] != "start_combat"


def test_pc_perceive_unnoticed_to_detected(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    key = _seed_encounter(orchestrator, monkeypatch, phase="unnoticed")

    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {"ok": True, "success": True, "total": 15, "dc": 12, "reason": "Perception"},
    )

    orchestrator._current_player_input = "listen for movement"
    result = orchestrator._execute_tool(
        "roll_d20",
        {"mod": 2, "dc": 12, "reason": "Perception check"},
    )

    assert result.get("ok")
    blob = orchestrator._encounter_by_room[key]
    assert blob["phase"] == "detected"
    assert blob["last_contest"]["contest_type"] == "pc_perceive"


def test_pc_sneak_win_stays_detected(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    key = _seed_encounter(orchestrator, monkeypatch, phase="detected")

    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {"ok": True, "success": True, "total": 18, "dc": 14, "reason": "Stealth"},
    )

    orchestrator._current_player_input = "sneak past the ghoul"
    orchestrator._execute_tool(
        "roll_d20",
        {"mod": 3, "dc": 14, "reason": "Stealth to sneak past"},
    )

    assert orchestrator._encounter_by_room[key]["phase"] == "detected"
    assert not orchestrator._combat_active_in_db()


def test_pc_sneak_fail_promotes_engaged(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    key = _seed_encounter(orchestrator, monkeypatch, phase="detected")

    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {"ok": True, "success": False, "total": 8, "dc": 14, "reason": "Stealth"},
    )
    start_calls: list[dict] = []
    real_start = orchestrator.bridge.start_combat

    def capture_start(**kwargs):
        start_calls.append(kwargs)
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)

    orchestrator._current_player_input = "try to sneak"
    orchestrator._execute_tool(
        "roll_d20",
        {"mod": 0, "dc": 14, "reason": "Stealth"},
    )
    assert orchestrator._encounter_by_room[key]["phase"] == "engaged"

    result = orchestrator._execute_tool(
        "start_combat",
        {"monster_specs": ["grave-ghoul:1"]},
    )
    assert result.get("ok")
    assert start_calls


def test_contest_type_from_roll_reason(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="detected")

    inferred = orchestrator._infer_contest_type(
        "Stealth to sneak past",
        "",
        "detected",
        ENEMY_FEATURES,
    )
    assert inferred == "pc_sneak"

    orchestrator._pending_contest_type = "pc_sneak"
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {"ok": True, "success": True, "total": 16, "dc": 12},
    )
    orchestrator._execute_tool("roll_d20", {"mod": 2, "dc": 12, "reason": "roll"})
    assert orchestrator._pending_contest_type is None


def test_monster_ambush_sets_ambush_and_surprise(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    key = _seed_encounter(orchestrator, monkeypatch, phase="unnoticed")
    orchestrator._encounter_by_room[key]["threats"] = []

    real_status = orchestrator.bridge.status

    def status_with_roster() -> dict:
        st = dict(real_status())
        st["roster"] = [{"character_id": "pc-test-1"}]
        return st

    monkeypatch.setattr(orchestrator.bridge, "status", status_with_roster)

    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {"ok": True, "success": False, "total": 5, "dc": 15, "reason": "Stealth"},
    )
    captured: list[dict] = []

    def capture_start(**kwargs):
        captured.append(kwargs)
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)

    orchestrator._current_player_input = "sneak through the shadows"
    orchestrator._execute_tool(
        "roll_d20",
        {"mod": 0, "dc": 15, "reason": "Stealth"},
    )

    blob = orchestrator._encounter_by_room[key]
    assert blob["phase"] == "ambush"
    assert "surprised_combatant_ids" in blob

    orchestrator._execute_tool("start_combat", {"monster_specs": ["grave-ghoul:1"]})
    assert captured
    assert captured[0].get("surprised_combatant_ids")


def test_beat_hostile_slot_promotes_engaged_when_detected(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="detected")

    start_calls: list[dict] = []

    def capture_start(**kwargs):
        start_calls.append(kwargs)
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)
    monkeypatch.setattr(
        orchestrator.bridge,
        "process_beat",
        lambda **kwargs: {
            "ok": True,
            "mechanical_summary": [
                {
                    "ok": True,
                    "action": "hostile",
                    "monster_specs": ["grave-ghoul:1"],
                    "slot": 1,
                }
            ],
        },
    )

    orchestrator._execute_tool("process_beat", {"lines": ["I attack the ghoul"]})

    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "engaged"
    assert not start_calls
    assert not orchestrator._combat_active_in_db()


def test_same_turn_enter_plus_start_combat_blocked(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _dungeon_party_status(orchestrator, monkeypatch)

    monkeypatch.setattr(
        orchestrator.bridge,
        "enter_dungeon",
        lambda **kwargs: {"ok": True, "features": ENEMY_FEATURES},
    )
    start_calls: list[dict] = []

    def capture_start(**kwargs):
        start_calls.append(kwargs)
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)

    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call("enter_dungeon", {"site_address": SITE_ID}, call_id="tc1"),
                    _tool_call("start_combat", {"monster_specs": ["grave-ghoul:1"]}, call_id="tc2"),
                ],
                "finish_reason": "tool_calls",
            },
            {"content": "Threat in the shadows.", "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("enter and fight")

    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "detected"
    assert not start_calls
    blocked = orchestrator._last_tool_results.get("start_combat") or {}
    assert blocked.get("error") == "ENCOUNTER_NOT_ENGAGED"


def test_beat_combat_trigger_gated(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="detected")

    start_calls: list[dict] = []

    def capture_start(**kwargs):
        start_calls.append(kwargs)
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)
    monkeypatch.setattr(
        orchestrator.bridge,
        "process_beat",
        lambda **kwargs: {
            "ok": True,
            "mechanical_summary": [
                {
                    "ok": True,
                    "action": "combat_trigger",
                    "monster_specs": ["grave-ghoul:1"],
                    "include_party": True,
                }
            ],
        },
    )

    orchestrator._execute_tool("process_beat", {"lines": ["attack"]})

    assert not start_calls
    assert not orchestrator._combat_active_in_db()


def test_beat_combat_trigger_ok_when_engaged(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="engaged")

    run_monster_calls: list[str] = []

    def capture_start(**kwargs):
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)
    monkeypatch.setattr(
        orchestrator.bridge,
        "run_combat_monster_turns",
        lambda: run_monster_calls.append("called") or {"ok": True, "mechanical": []},
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "process_beat",
        lambda **kwargs: {
            "ok": True,
            "mechanical_summary": [
                {
                    "ok": True,
                    "action": "combat_trigger",
                    "monster_specs": ["grave-ghoul:1"],
                    "include_party": True,
                }
            ],
        },
    )

    orchestrator._execute_tool("process_beat", {"lines": ["attack the ghoul"]})

    assert orchestrator.combat.active
    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "in_combat"
    assert not run_monster_calls


def test_encounter_state_export_import(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    key = _seed_encounter(orchestrator, monkeypatch, phase="engaged")

    exported = orchestrator.export_encounter_state()
    assert key in exported
    assert exported[key]["phase"] == "engaged"

    orchestrator._encounter_by_room.clear()
    orchestrator.import_encounter_state(exported)
    assert orchestrator._encounter_by_room[key]["phase"] == "engaged"


def test_tools_ok_append_only(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="engaged")

    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {"ok": True, "success": True, "total": 15, "dc": 10},
    )
    monkeypatch.setattr(orchestrator.bridge, "start_combat", lambda **kwargs: {"ok": True})

    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call("roll_d20", {"mod": 0, "dc": 10, "reason": "test"}, call_id="tc1"),
                    _tool_call("start_combat", {"monster_specs": ["grave-ghoul:1"]}, call_id="tc2"),
                ],
                "finish_reason": "tool_calls",
            },
            {"content": "Steel rings.", "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("fight")

    assert orchestrator._tools_ok_this_turn == ["roll_d20", "start_combat"]


def test_verify_retry_no_second_llm_loop(orchestrator, monkeypatch):
    _exploration_ready(orchestrator, monkeypatch)
    _seed_encounter(orchestrator, monkeypatch, phase="detected")

    llm_loop_calls = 0
    narrate_llm_calls = 0
    event_order: list[str] = []

    def fake_llm_loop(messages):
        nonlocal llm_loop_calls
        llm_loop_calls += 1
        return "Combat begins as the ghoul lunges."

    def fake_call_narration_llm(messages):
        nonlocal narrate_llm_calls
        narrate_llm_calls += 1
        if narrate_llm_calls == 1:
            return "Combat begins as the ghoul lunges."
        return (
            "A grave ghoul lurks in the chapel shadows. "
            "You could listen, slip past, or engage."
        )

    import gm.orchestrator as orchestrator_module

    real_verify_pass = orchestrator_module.log_narration_verify_pass
    real_emit = orchestrator._emit_narration

    def track_verify_pass(data):
        event_order.append("verify_pass")
        return real_verify_pass(data)

    def track_emit(narration):
        event_order.append("emit")
        return real_emit(narration)

    monkeypatch.setattr(orchestrator, "_llm_loop", fake_llm_loop)
    monkeypatch.setattr(orchestrator, "_call_narration_llm", fake_call_narration_llm)
    monkeypatch.setattr(orchestrator_module, "log_narration_verify_pass", track_verify_pass)
    monkeypatch.setattr(orchestrator, "_emit_narration", track_emit)
    monkeypatch.setattr(orchestrator.bridge, "ensure_cell_initialized", lambda: None)

    orchestrator.process_turn("look at the ghoul")

    assert llm_loop_calls == 1
    assert narrate_llm_calls >= 1
    assert "verify_pass" in event_order
    assert "emit" in event_order
    assert event_order.index("verify_pass") < event_order.index("emit")


def test_chubby_replay_no_instant_combat(orchestrator, monkeypatch):
    """Ticket repro: 32-C-UG-1 chapel-stairs + grave-ghoul — no combat until engage."""
    _exploration_ready(orchestrator, monkeypatch)
    _dungeon_party_status(orchestrator, monkeypatch)

    start_calls: list[dict] = []

    def capture_start(**kwargs):
        start_calls.append(kwargs)
        orchestrator.combat.active = True
        return {"ok": True, "action": "combat_start"}

    monkeypatch.setattr(orchestrator.bridge, "start_combat", capture_start)
    monkeypatch.setattr(
        orchestrator.bridge,
        "enter_dungeon",
        lambda **kwargs: {
            "ok": True,
            "features": ENEMY_FEATURES,
            "room": {"id": ROOM_ID},
        },
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_d20",
        lambda **kwargs: {
            "ok": True,
            "success": True,
            "total": 18,
            "dc": 14,
            "reason": "Stealth",
        },
    )
    monkeypatch.setattr(orchestrator.bridge, "ensure_cell_initialized", lambda: None)

    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call("enter_dungeon", {"site_address": SITE_ID}, call_id="tc1"),
                    _tool_call("start_combat", {"monster_specs": ["grave-ghoul:1"]}, call_id="tc2"),
                ],
                "finish_reason": "tool_calls",
            },
            {"content": "Cold chapel air. A grave ghoul waits on the stairs.", "tool_calls": [], "finish_reason": "stop"},
            {
                "content": "",
                "tool_calls": [
                    _tool_call(
                        "roll_d20",
                        {"mod": 3, "dc": 14, "reason": "Stealth to sneak past"},
                        call_id="tc3",
                    ),
                ],
                "finish_reason": "tool_calls",
            },
            {"content": "You edge past the ghoul without drawing its ire.", "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("I enter the dungeon")

    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "detected"
    assert not start_calls
    assert not orchestrator._combat_active_in_db()

    orchestrator.process_turn("I try to sneak past the ghoul quietly")

    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "detected"
    assert not start_calls
    assert not orchestrator._combat_active_in_db()

    _patch_llm_sequence(
        monkeypatch,
        [
            {
                "content": "",
                "tool_calls": [
                    _tool_call("start_combat", {"monster_specs": ["grave-ghoul:1"]}, call_id="tc4"),
                ],
                "finish_reason": "tool_calls",
            },
            {"content": "Steel meets rotting flesh.", "tool_calls": [], "finish_reason": "stop"},
        ],
    )

    orchestrator.process_turn("I attack the ghoul")

    assert orchestrator._current_encounter_phase(orchestrator.bridge.status()) == "in_combat"
    assert start_calls
