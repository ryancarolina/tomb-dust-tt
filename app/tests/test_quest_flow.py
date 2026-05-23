"""APP-085: quest lifecycle refuse, hooks, deliver, abandon."""

from __future__ import annotations

import json

import pytest

from helpers import BUILD

QUEST_ID = "holt-brothers-signet"
QUEST_ITEM = "holt-signet-ring"
NPC_ID = "marshal-garrick-holt"
SITE = "32-C-UG-1"


def _gold(conn, char_id: str) -> int:
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = ?", (char_id,)).fetchone()[
            "sheet_json"
        ]
    )
    return int(sheet.get("goldGp", 0))


def _add_quest_item(conn, char_id: str, campaign: str) -> None:
    from tomb_gm.domain.inventory import add_item, ensure_normalized
    from tomb_gm.services.content import ContentService

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, campaign),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    content = ContentService(BUILD)
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)
    catalog = lookup.get(QUEST_ITEM) or content.load_item(QUEST_ITEM)
    add_item(sheet, QUEST_ITEM, catalog=catalog)
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, campaign),
    )
    conn.commit()


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
    assert created["ok"], created.get("error", created)
    bridge._holt_char_id = created["id"]
    return bridge


def _char_id(bridge) -> str:
    return getattr(bridge, "_holt_char_id", "delver")


def _active_quest_ids(bridge) -> list[str]:
    listed = bridge.list_quests_for_ui(active_only=True)
    assert listed["ok"]
    return [row["quest_id"] for row in listed.get("quests") or []]


def test_refuse_leaves_log_empty(holt_setup):
    bridge = holt_setup
    assert bridge.offer_quest(QUEST_ID)["ok"]
    declined = bridge.decline_quest(QUEST_ID)
    assert declined["ok"]
    assert declined["state"] == "declined"
    assert _active_quest_ids(bridge) == []


def test_accept_lists_quest(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    accepted = bridge.accept_quest(QUEST_ID)
    assert accepted["ok"]
    assert accepted["state"] == "accepted"
    assert QUEST_ID in _active_quest_ids(bridge)


def test_visit_site_objective_hook(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)

    refreshed = bridge._refresh_quest_objectives_after(site_address=SITE)
    assert refreshed["ok"]
    assert QUEST_ID in refreshed.get("updated", [])

    runtime = bridge.list_quests()["quests"][QUEST_ID]
    assert runtime["objectives"]["enter-undercrypt"] == "done"


def test_have_item_objective_hook(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)
    _add_quest_item(bridge.ctx.conn, _char_id(bridge), "holt-test")

    refreshed = bridge._refresh_quest_objectives_after(character_id=_char_id(bridge))
    assert refreshed["ok"]
    assert QUEST_ID in refreshed.get("updated", [])

    runtime = bridge.list_quests()["quests"][QUEST_ID]
    assert runtime["objectives"]["recover-ring"] == "done"


def test_deliver_removes_item(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)
    _add_quest_item(bridge.ctx.conn, _char_id(bridge), "holt-test")
    bridge._refresh_quest_objectives_after(site_address=SITE)
    bridge._refresh_quest_objectives_after(character_id=_char_id(bridge))

    before_gold = _gold(bridge.ctx.conn, _char_id(bridge))
    has_before = bridge.has_pack_item(QUEST_ITEM, character_id=_char_id(bridge))
    assert has_before["found"] is True

    delivered = bridge.deliver_quest_item(
        QUEST_ID,
        QUEST_ITEM,
        NPC_ID,
        character_id=_char_id(bridge),
    )
    assert delivered["ok"]
    assert delivered["state"] == "ready_to_turn_in"

    has_after = bridge.has_pack_item(QUEST_ITEM, character_id=_char_id(bridge))
    assert has_after["found"] is False

    completed = bridge.complete_quest(QUEST_ID, character_id=_char_id(bridge))
    assert completed["ok"]
    assert completed["state"] == "completed"
    assert _gold(bridge.ctx.conn, _char_id(bridge)) > before_gold
    assert QUEST_ID not in _active_quest_ids(bridge)


def test_abandon_removes_active(holt_setup):
    bridge = holt_setup
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)
    assert QUEST_ID in _active_quest_ids(bridge)

    abandoned = bridge.abandon_quest(QUEST_ID)
    assert abandoned["ok"]
    assert abandoned["state"] == "abandoned"
    assert _active_quest_ids(bridge) == []
