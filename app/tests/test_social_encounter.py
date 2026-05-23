"""APP-108: social encounter FSM tests."""

from __future__ import annotations

import pytest


def test_social_encounter_fsm_transitions(bridge):
    bridge.campaign_new("social-test", "Social Test")
    bridge.session_start("social-test")

    from tomb_gm.services import social_encounter as se

    conn = bridge.ctx.conn
    slug = "social-test"

    engaged = se.engage(conn, slug, npc_id="marshal-garrick-holt")
    assert engaged["ok"]
    assert engaged["phase"] == "active"

    enc_id = engaged["encounter_id"]
    contested = se.set_contested(conn, slug, enc_id, skill_id="persuasion")
    assert contested["phase"] == "contested"

    resolved = se.resolve_encounter(conn, slug, enc_id, margin=4)
    assert resolved["phase"] == "resolved"
    assert resolved["disposition"] == "favorable"

    reset = se.reset_encounter(conn, slug, enc_id)
    assert reset["phase"] == "idle"

    summary = se.active_encounter_summary(conn, slug)
    assert summary.get("phase") == "idle"


def test_bridge_social_encounter_helpers(bridge):
    bridge.campaign_new("social-bridge", "Social Bridge")
    bridge.session_start("social-bridge")

    status = bridge.social_encounter_status()
    assert status["ok"]
    assert status["phase"] == "idle"

    engaged = bridge.social_encounter_engage("marshal-garrick-holt", quest_id="holt-brothers-signet")
    assert engaged["ok"]
    assert engaged["phase"] == "active"

    status = bridge.social_encounter_status()
    assert status["phase"] == "active"
    assert status["npc_id"] == "marshal-garrick-holt"

    left = bridge.social_encounter_leave("marshal-garrick-holt", quest_id="holt-brothers-signet")
    assert left["ok"]
    assert left["phase"] == "idle"


def test_skill_check_bridge(bridge):
    bridge.campaign_new("skill-bridge", "Skill Bridge")
    bridge.session_start("skill-bridge")
    created = bridge.character_create(
        name="Diplomat",
        background="novice",
        spi_score=16,
        skill_ids=["persuasion", "deception", "etiquette"],
        gold_gp=0,
    )
    assert created["ok"]

    result = bridge.skill_check("persuasion", dc=12, reason="test charm", seed=3)
    assert result["ok"]
    assert result["skill_id"] == "persuasion"
    assert result["mod"] >= 3
    assert "success" in result
