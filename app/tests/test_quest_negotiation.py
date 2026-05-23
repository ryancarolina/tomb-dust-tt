"""APP-108: Holt quest advance negotiation tests."""

from __future__ import annotations

import json

import pytest

QUEST_ID = "holt-brothers-signet"


def _gold(conn, char_id: str) -> int:
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = ?", (char_id,)).fetchone()[
            "sheet_json"
        ]
    )
    return int(sheet.get("goldGp", 0))


@pytest.fixture
def holt_setup(bridge):
    bridge.campaign_new("holt-test", "Holt Test")
    bridge.session_start("holt-test")
    created = bridge.character_create(
        name="Delver",
        background="novice",
        spi_score=18,
        str_score=14,
        skill_ids=["persuasion", "intimidation", "deception"],
        gold_gp=20,
    )
    assert created["ok"]
    bridge._holt_char_id = created["id"]
    return bridge


def _char_id(bridge) -> str:
    return getattr(bridge, "_holt_char_id", "delver")


def test_quest_offer_accept(holt_setup):
    bridge = holt_setup
    offered = bridge.offer_quest(QUEST_ID)
    assert offered["ok"]
    assert offered["state"] == "offered"

    accepted = bridge.accept_quest(QUEST_ID)
    assert accepted["ok"]
    assert accepted["state"] == "accepted"

    listed = bridge.list_quests()
    assert listed["ok"]
    assert listed["quests"][QUEST_ID]["state"] == "accepted"


def test_negotiate_fail_grants_zero_gp(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)
    before = _gold(bridge.ctx.conn, _char_id(bridge))

    from tomb_gm.services import quests
    from tomb_gm.cli.cmd_core import log_event

    result = quests.negotiate_quest_advance(
        bridge.ctx.conn,
        "holt-test",
        QUEST_ID,
        "persuasion",
        content_root=bridge.ctx.config.content_root,
        log_event=log_event,
        session_id=bridge._active_session_id(),
        character_id=_char_id(bridge),
        seed=1,
    )
    assert result["ok"]
    after = _gold(bridge.ctx.conn, _char_id(bridge))
    if result["margin"] < 0:
        assert result["advance_gp"] == 0
        assert after == before
    else:
        assert after >= before


def test_negotiate_high_margin_caps_at_50_gp(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)
    before = _gold(bridge.ctx.conn, _char_id(bridge))

    sheet = json.loads(
        bridge.ctx.conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ?",
            (_char_id(bridge),),
        ).fetchone()["sheet_json"]
    )
    for sk in sheet["skills"]:
        if sk["skillId"] in ("persuasion", "intimidation", "deception"):
            sk["level"] = 10
    sheet["attributes"]["SPI"] = 20
    sheet["classTier"] = 4
    bridge.ctx.conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ?",
        (json.dumps(sheet), _char_id(bridge)),
    )
    bridge.ctx.conn.commit()

    result = bridge.negotiate_quest_advance(
        QUEST_ID,
        "intimidation",
        character_id=_char_id(bridge),
        approach="Front me fifty gold, Holt.",
        seed=99,
    )
    assert result["ok"]
    after = _gold(bridge.ctx.conn, _char_id(bridge))
    assert result["advance_gp"] in (0, 25, 50)
    assert after == before + result["advance_gp"]
    assert result["grant"]["advancePaidGp"] <= 50


def test_grant_quest_advance_cap(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)

    grant = bridge.grant_quest_advance(QUEST_ID, 40)
    assert grant["ok"]
    assert grant["granted_gp"] == 40

    second = bridge.grant_quest_advance(QUEST_ID, 40)
    assert second["ok"]
    assert second["granted_gp"] == 10

    listed = bridge.list_quests()
    assert listed["quests"][QUEST_ID]["advancePaidGp"] == 50
