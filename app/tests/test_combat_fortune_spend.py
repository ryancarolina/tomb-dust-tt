"""APP-103: Fortune spend in combat — pool decrement, pending advantage, inner-loop dispatch."""

from __future__ import annotations

import json

import pytest

from gm.combat_fsm import is_pc_turn


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


def _multi_tool_call(calls: list[tuple[str, dict]]) -> list:
    out: list = []
    for i, (name, args) in enumerate(calls):
        out.extend(_tool_call(name, args, call_id=f"call_{i + 1}"))
    return out


def _ensure_salt_road_session(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("salt-road")
    assert start.get("ok"), start.get("error")


def _advance_to_pc_turn(bridge, *, max_rounds: int = 8) -> dict:
    for _ in range(max_rounds):
        status = bridge.status()
        if not status.get("combat"):
            pytest.fail("combat ended before PC turn")
        if is_pc_turn(status):
            return status
        adv = bridge.run_combat_monster_turns()
        assert adv.get("ok"), adv
    pytest.fail(f"PC turn not reached within {max_rounds} iterations")


def _set_fortune(
    bridge,
    char_id: str,
    current: int,
    max_: int | None = None,
    *,
    pending: bool | None = None,
) -> None:
    campaign_slug = bridge._campaign_slug()
    row = bridge.ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, campaign_slug),
    ).fetchone()
    assert row is not None
    sheet = json.loads(row["sheet_json"])
    fortune = sheet.setdefault("fortune", {"current": 0, "max": 1, "pendingAdvantage": False})
    fortune["current"] = current
    fortune["max"] = max_ if max_ is not None else current
    if pending is not None:
        fortune["pendingAdvantage"] = pending
    bridge.ctx.conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, campaign_slug),
    )
    bridge.ctx.conn.commit()


def _fortune_from_sheet(bridge, char_id: str) -> dict:
    campaign_slug = bridge._campaign_slug()
    row = bridge.ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, campaign_slug),
    ).fetchone()
    return json.loads(row["sheet_json"])["fortune"]


def _bootstrap_pc_combat(orchestrator) -> tuple[dict, str, str, str]:
    bridge = orchestrator.bridge
    _ensure_salt_road_session(bridge)
    created = bridge.character_create(name="Sammy", background="militia")
    assert created.get("ok"), created.get("error")
    char_id = created["id"]
    start = bridge.start_combat(monster_specs=["grave-ghoul:1"])
    assert start.get("ok"), start.get("error")
    status = _advance_to_pc_turn(bridge)
    combat = status["combat"]
    turn_id = combat["turn_id"]
    ghouls = [
        c
        for c in combat.get("combatants") or []
        if str(c.get("id", "")).startswith("grave-ghoul")
    ]
    assert ghouls, "grave-ghoul missing from combatants"
    orchestrator.combat.active = True
    return status, char_id, turn_id, ghouls[0]["id"]


def _mock_combat_chat(monkeypatch, *, tool_calls: list, content: str = "", narrate: str = "Done.") -> None:
    call_n = {"n": 0}

    def _fake_chat(*args, **kwargs):
        call_n["n"] += 1
        if call_n["n"] == 1:
            return {
                "content": content,
                "tool_calls": tool_calls,
                "finish_reason": "tool_calls",
            }
        return {"content": narrate, "tool_calls": [], "finish_reason": "stop"}

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat)


def _combat_attack_row(mechanical: list[dict]) -> dict | None:
    for item in mechanical:
        if item.get("action") == "combat_attack":
            return item
    return None


def _fortune_spend_row(mechanical: list[dict]) -> dict | None:
    for item in mechanical:
        if item.get("action") == "fortune_spend":
            return item
    return None


@pytest.fixture
def orchestrator_with_session(orchestrator):
    _ensure_salt_road_session(orchestrator.bridge)
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    assert orchestrator.bridge.status().get("combat") is None
    return orchestrator


# --- F1 — spend + ATTACK batch ---


def test_f1_spend_and_attack_batch_pool_and_advantage(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _, char_id, turn_id, target_id = _bootstrap_pc_combat(orch)
    _set_fortune(orch.bridge, char_id, 2, 2)
    monkeypatch.setattr(orch, "_combat_auto_chain", lambda: [])

    _mock_combat_chat(
        monkeypatch,
        tool_calls=_multi_tool_call(
            [
                ("fortune_spend", {"character_id": turn_id}),
                (
                    "combat_action",
                    {"action": "ATTACK", "actor_id": turn_id, "target_id": target_id},
                ),
            ]
        ),
        content="Fortune and steel.",
    )

    messages = [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}]
    orch._combat_llm_loop_inner(messages, depth=0)

    fortune = _fortune_from_sheet(orch.bridge, char_id)
    assert fortune["current"] == 1
    assert fortune["max"] == 2
    assert fortune.get("pendingAdvantage") is False

    mechanical = orch.combat.last_mechanical or []
    spend_row = _fortune_spend_row(mechanical)
    assert spend_row is not None
    assert spend_row.get("pending_advantage") is True
    attack_row = _combat_attack_row(mechanical)
    assert attack_row is not None
    assert attack_row.get("advantage") is True
    assert attack_row.get("natural_high") >= attack_row.get("natural_low")


# --- F2 — status footer ---


def test_f2_status_footer_shows_decremented_fortune(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _, char_id, turn_id, target_id = _bootstrap_pc_combat(orch)
    _set_fortune(orch.bridge, char_id, 2, 2)
    monkeypatch.setattr(orch, "_combat_auto_chain", lambda: [])

    _mock_combat_chat(
        monkeypatch,
        tool_calls=_multi_tool_call(
            [
                ("fortune_spend", {"character_id": turn_id}),
                (
                    "combat_action",
                    {"action": "ATTACK", "actor_id": turn_id, "target_id": target_id},
                ),
            ]
        ),
    )
    orch._combat_llm_loop_inner(
        [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}],
        depth=0,
    )

    roster = orch.bridge.status().get("roster") or []
    entry = next((r for r in roster if r.get("character_id") == char_id), None)
    assert entry is not None
    assert entry.get("fortune") == "1/2"


# --- F3 — empty pool APP-028 ---


def test_f3_empty_pool_all_failed_no_spent_fiction(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _, char_id, turn_id, _ = _bootstrap_pc_combat(orch)
    _set_fortune(orch.bridge, char_id, 0, 2)

    _mock_combat_chat(
        monkeypatch,
        tool_calls=_tool_call("fortune_spend", {"character_id": turn_id}),
        content="Fortune spent on a reroll.",
    )

    result = orch._combat_llm_loop_inner(
        [{"role": "system", "content": "combat"}, {"role": "user", "content": "spend fortune"}],
        depth=0,
    )

    assert result.startswith("[Mechanics failed — fortune_spend:")
    assert "fortune spent" not in result.lower()
    assert _fortune_from_sheet(orch.bridge, char_id)["current"] == 0


# --- F4 — engine unit advantage ---


def test_f4_engine_perform_attack_roll_advantage_dual_naturals(bridge):
    _ensure_salt_road_session(bridge)
    created = bridge.character_create(name="RollTester", background="militia")
    assert created.get("ok"), created.get("error")
    char_id = created["id"]
    _set_fortune(bridge, char_id, 2, 2, pending=True)

    from tomb_gm.services.simulation.rolls import perform_attack_roll

    def _log_event(conn, session_id, kind, payload):
        pass

    roll = perform_attack_roll(
        bridge.ctx.conn,
        _log_event,
        session_id=bridge._active_session_id(),
        ability_mod=2,
        pb=2,
        skill_level=3,
        target_ac=12,
        weapon_damage="1d6",
        ability_damage_mod=1,
        seed=42,
        character_id=char_id,
        campaign_slug=bridge._campaign_slug(),
    )

    assert roll.get("advantage") is True
    assert roll.get("natural_high") is not None
    assert roll.get("natural_low") is not None
    assert roll["natural_high"] >= roll["natural_low"]
    assert _fortune_from_sheet(bridge, char_id).get("pendingAdvantage") is False


# --- F5 — second roll plain ---


def test_f5_second_attack_roll_no_advantage(bridge):
    _ensure_salt_road_session(bridge)
    created = bridge.character_create(name="RollTester2", background="militia")
    assert created.get("ok"), created.get("error")
    char_id = created["id"]
    _set_fortune(bridge, char_id, 2, 2, pending=True)

    from tomb_gm.services.simulation.rolls import perform_attack_roll

    def _log_event(conn, session_id, kind, payload):
        pass

    kwargs = dict(
        conn=bridge.ctx.conn,
        log_event=_log_event,
        session_id=bridge._active_session_id(),
        ability_mod=2,
        pb=2,
        skill_level=3,
        target_ac=12,
        weapon_damage="1d6",
        ability_damage_mod=1,
        seed=99,
        character_id=char_id,
        campaign_slug=bridge._campaign_slug(),
    )
    first = perform_attack_roll(**kwargs)
    assert first.get("advantage") is True
    second = perform_attack_roll(**kwargs)
    assert "advantage" not in second


# --- F6 — narrate-only Fortune ---


def test_f6_narrate_only_fortune_no_mechanical_spend_row(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _, _, turn_id, target_id = _bootstrap_pc_combat(orch)
    monkeypatch.setattr(orch, "_combat_auto_chain", lambda: [])

    _mock_combat_chat(
        monkeypatch,
        tool_calls=_tool_call(
            "combat_action",
            {"action": "ATTACK", "actor_id": turn_id, "target_id": target_id},
        ),
        content="You spend Fortune and strike true!",
        narrate="The blade finds flesh.",
    )
    orch._combat_llm_loop_inner(
        [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}],
        depth=0,
    )

    mechanical = orch.combat.last_mechanical or []
    assert _fortune_spend_row(mechanical) is None


# --- F7 — wrong tool in combat ---


def test_f7_combat_inner_wrong_tool_start_combat_rejected(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _bootstrap_pc_combat(orch)

    def _fake_chat(*args, **kwargs):
        return {
            "content": "You swing and connect!",
            "tool_calls": _tool_call("start_combat", {"monster_specs": ["ghoul:1"]}),
            "finish_reason": "tool_calls",
        }

    monkeypatch.setattr("gm.orchestrator.chat_completion", _fake_chat)

    result = orch._combat_llm_loop_inner(
        [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}],
        depth=0,
    )

    assert "[Mechanics failed" in result
    assert "connect" not in result.lower()
    assert "start_combat" in result


# --- F8 — spend only, turn unchanged ---


def test_f8_fortune_spend_only_turn_unchanged_pending_set(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _, char_id, turn_id, _ = _bootstrap_pc_combat(orch)
    _set_fortune(orch.bridge, char_id, 2, 2)
    turn_before = orch.bridge.status()["combat"]["turn_id"]

    _mock_combat_chat(
        monkeypatch,
        tool_calls=_tool_call("fortune_spend", {"character_id": turn_id}),
    )
    result = orch._combat_llm_loop_inner(
        [{"role": "system", "content": "combat"}, {"role": "user", "content": "spend fortune"}],
        depth=0,
    )

    assert "Mechanics failed" not in result
    assert orch.bridge.status()["combat"]["turn_id"] == turn_before
    fortune = _fortune_from_sheet(orch.bridge, char_id)
    assert fortune["current"] == 1
    assert fortune.get("pendingAdvantage") is True


# --- F9 — END_TURN clears pending ---


def test_f9_end_turn_clears_pending_no_advantage_next_attack(orchestrator_with_session):
    orch = orchestrator_with_session
    _, char_id, turn_id, target_id = _bootstrap_pc_combat(orch)
    _set_fortune(orch.bridge, char_id, 2, 2)

    spend = orch._execute_combat_fortune_spend(character_id=turn_id)
    assert spend.get("ok") is True
    assert _fortune_from_sheet(orch.bridge, char_id).get("pendingAdvantage") is True

    end = orch._execute_combat_action("END_TURN", actor_id=turn_id)
    assert end.get("ok") is True
    assert _fortune_from_sheet(orch.bridge, char_id).get("pendingAdvantage") is False

    status = _advance_to_pc_turn(orch.bridge)
    turn_id2 = status["combat"]["turn_id"]
    ghouls = [
        c
        for c in status["combat"].get("combatants") or []
        if str(c.get("id", "")).startswith("grave-ghoul") and int(c.get("hp", 0)) > 0
    ]
    if not ghouls:
        pytest.skip("ghoul defeated before second PC attack")
    attack = orch.bridge.combat_attack(turn_id2, ghouls[0]["id"])
    assert attack.get("ok") is True
    assert attack.get("advantage") is not True
    assert "advantage" not in attack


# --- F10 — CAST (deferred) ---


@pytest.mark.skip(
    reason="ATTACK-only MVP; spell_cast.py not in ticket Expected files (APP-103 WS-CAST)"
)
def test_f10_cast_spell_attack_after_spend_has_advantage(orchestrator_with_session):
    pytest.fail("F10 requires spell_cast.py wire — see APP-103 WS-CAST")


# --- F11 — batch reorder ---


def test_f11_reorder_attack_before_spend_still_advantaged(orchestrator_with_session, monkeypatch):
    orch = orchestrator_with_session
    _, char_id, turn_id, target_id = _bootstrap_pc_combat(orch)
    _set_fortune(orch.bridge, char_id, 2, 2)
    monkeypatch.setattr(orch, "_combat_auto_chain", lambda: [])

    _mock_combat_chat(
        monkeypatch,
        tool_calls=_multi_tool_call(
            [
                (
                    "combat_action",
                    {"action": "ATTACK", "actor_id": turn_id, "target_id": target_id},
                ),
                ("fortune_spend", {"character_id": turn_id}),
            ]
        ),
    )
    orch._combat_llm_loop_inner(
        [{"role": "system", "content": "combat"}, {"role": "user", "content": "attack"}],
        depth=0,
    )

    attack_row = _combat_attack_row(orch.combat.last_mechanical or [])
    assert attack_row is not None
    assert attack_row.get("advantage") is True
    assert _fortune_from_sheet(orch.bridge, char_id)["current"] == 1
