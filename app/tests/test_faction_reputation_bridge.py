"""Bridge integration tests for faction reputation (APP-100)."""

from __future__ import annotations

import json

import pytest


def _ensure_campaign_session(bridge) -> None:
    result = bridge.campaign_new("rep-bridge", "Rep Bridge")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("rep-bridge")
    assert start.get("ok")


@pytest.fixture
def bridge_with_rep_session(bridge):
    _ensure_campaign_session(bridge)
    return bridge


def test_list_factions_defaults(bridge_with_rep_session):
    bridge = bridge_with_rep_session
    result = bridge.list_factions()
    assert result.get("ok") is True
    factions = result.get("factions") or []
    assert len(factions) == 4
    for row in factions:
        assert row["rep"] == 0
        assert "tier" in row


def test_adjust_and_status_reputation(bridge_with_rep_session):
    bridge = bridge_with_rep_session
    adj = bridge.adjust_faction_rep("knights-of-breley", 1, "quest_reward")
    assert adj.get("ok") is True
    assert adj.get("after") == 1

    status = bridge.status()
    rep = status.get("reputation") or {}
    assert rep["knights-of-breley"]["value"] == 1
    assert rep["knights-of-breley"]["tier"] == "blessing"


def test_faction_effects_at_breley_holt_cap(bridge_with_rep_session):
    bridge = bridge_with_rep_session
    bridge.adjust_faction_rep("knights-of-breley", 2, "test")
    effects = bridge.faction_effects_at("32-C")
    assert effects.get("ok") is True
    assert effects["effects"].get("holt_advance_cap_bonus") == 25


def test_faction_effects_at_breley_holt_dc_penalty(bridge_with_rep_session):
    bridge = bridge_with_rep_session
    bridge.adjust_faction_rep("knights-of-breley", -2, "test")
    effects = bridge.faction_effects_at("32-C")
    assert effects.get("ok") is True
    assert effects["effects"].get("holt_advance_dc_modifier") == 2


def test_get_faction_rep(bridge_with_rep_session):
    bridge = bridge_with_rep_session
    bridge.adjust_faction_rep("delvers-registry", 1, "stamp_paid")
    got = bridge.get_faction_rep("delvers-registry")
    assert got.get("ok") is True
    assert got["value"] == 1
    assert got["tier"] == "stamp_discount"
    assert "registry_stamp_discount" in got.get("mechanicalKeys", [])


def test_rep_persists_after_account_state_roundtrip(bridge_with_rep_session):
    bridge = bridge_with_rep_session
    bridge.adjust_faction_rep("knights-of-breley", 1, "persist_test")
    campaign_slug = bridge._campaign_slug()
    row = bridge.ctx.conn.execute(
        "SELECT account_state_json FROM campaigns WHERE slug = ?",
        (campaign_slug,),
    ).fetchone()
    state = json.loads(row["account_state_json"])
    assert state["reputation"]["knights-of-breley"] == 1


def test_orchestrator_list_factions_tool(orchestrator):
    _ensure_campaign_session(orchestrator.bridge)
    result = orchestrator._execute_tool("list_factions", {})
    assert result.get("ok") is True
    assert len(result.get("factions") or []) == 4
