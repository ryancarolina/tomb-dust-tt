"""APP-086: quest item pack query, remove, deliver, economy guards."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"
APP = REPO / "app"

for _p in (APP, REPO / "play"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

QUEST_ITEM = "holt-signet-ring"
QUEST_ID = "holt-brothers-signet"
NPC_ID = "marshal-garrick-holt"
CAMPAIGN = "quest-inv-test"


@pytest.fixture
def quest_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character
    from tomb_gm.domain.creation import starting_kit_inventory

    conn = connect(tmp_path / "quest.db")
    run_migrations(conn)
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, 'Quest', '{}', '{}', '2026-01-01', '2026-01-01')",
        (CAMPAIGN,),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES ('sess1', ?, '2026-01-01', 'delve')",
        (CAMPAIGN,),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode) VALUES ('sess1', '32-C', 'surface')"
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug=CAMPAIGN,
        display_name="Delver",
        base_class="novice",
        character_id="delver",
        inventory=starting_kit_inventory(CONTENT, "novice"),
        gold_gp=50,
    )
    conn.execute("UPDATE characters SET slot = 1 WHERE id = 'delver'")
    conn.commit()
    return conn


@pytest.fixture
def quest_bridge(tmp_path):
    import os

    from gm.bridge import GameBridge
    from tomb_gm.domain.character import create_character
    from tomb_gm.domain.inventory import new_instance
    from tomb_gm.services.content import ContentService

    ws = tmp_path / "bridge-ws"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "campaigns").mkdir(exist_ok=True)
    rel_build = Path(os.path.relpath(CONTENT, ws))
    (ws / "config.yaml").write_text(
        f"content_root: {rel_build.as_posix()}\nlocal_dir: .local\nmax_players: 4\n",
        encoding="utf-8",
    )

    bridge = GameBridge(workspace=ws)
    bridge.init()
    bridge.campaign_new(CAMPAIGN, "Quest Inv Test")
    bridge.session_start(CAMPAIGN)
    lookup = ContentService(bridge.ctx.config.content_root).items_lookup()
    pack = [new_instance("rations", kind="consumable", uses=1, catalog=lookup.get("rations"))]
    create_character(
        bridge.ctx.conn,
        campaign_slug=CAMPAIGN,
        display_name="Delver",
        base_class="novice",
        character_id="delver",
        inventory={"pack": pack, "equipped": {}},
        gold_gp=50,
    )
    bridge.ctx.conn.execute(
        "UPDATE characters SET slot = 1 WHERE id = 'delver' AND campaign_slug = ?",
        (CAMPAIGN,),
    )
    bridge.ctx.conn.execute(
        "UPDATE party_state SET address = '32-C', mode = 'surface' WHERE session_id = ?",
        (bridge._active_session_id(),),
    )
    bridge.ctx.conn.commit()
    return bridge


def _add_quest_item_to_sheet(conn, char_id: str = "delver") -> str:
    from tomb_gm.domain.inventory import add_item, ensure_normalized
    from tomb_gm.services.content import ContentService

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, CAMPAIGN),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    content = ContentService(CONTENT)
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)
    catalog = lookup.get(QUEST_ITEM) or content.load_item(QUEST_ITEM)
    instance_ids = add_item(sheet, QUEST_ITEM, catalog=catalog)
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, CAMPAIGN),
    )
    conn.commit()
    return instance_ids[0]


def _pack_count(conn, char_id: str = "delver") -> int:
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, CAMPAIGN),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    return len(sheet.get("inventory", {}).get("pack", []))


def test_has_pack_item_after_add(quest_bridge):
    bridge = quest_bridge
    instance_id = _add_quest_item_to_sheet(bridge.ctx.conn)

    result = bridge.has_pack_item(QUEST_ITEM, character_id="delver")

    assert result["ok"] is True
    assert result["found"] is True
    assert result["quantity"] >= 1
    assert instance_id in result["instanceIds"]


def test_remove_pack_item_clears_row(quest_bridge):
    bridge = quest_bridge
    instance_id = _add_quest_item_to_sheet(bridge.ctx.conn)

    removed = bridge.remove_pack_item(instance_id=instance_id, character_id="delver")

    assert removed["ok"] is True
    assert removed["removed"]["itemId"] == QUEST_ITEM
    has_after = bridge.has_pack_item(QUEST_ITEM, character_id="delver")
    assert has_after["found"] is False
    assert has_after["quantity"] == 0


def test_deliver_quest_item_rejects_without_accept(quest_db):
    from tomb_gm.services import quests

    conn = quest_db
    _add_quest_item_to_sheet(conn)
    before = _pack_count(conn)

    result = quests.deliver_quest_item(
        conn,
        CAMPAIGN,
        QUEST_ID,
        QUEST_ITEM,
        NPC_ID,
        content_root=CONTENT,
        character_id="delver",
        has_item_fn=lambda iid: {"ok": True, "found": True, "itemId": iid},
        remove_item_fn=lambda **kw: {"ok": True, "removed": {"itemId": QUEST_ITEM}},
    )

    assert result["ok"] is False
    assert _pack_count(conn) == before


def test_deliver_quest_item_rejects_wrong_item(quest_db):
    from tomb_gm.services import quests
    from tomb_gm.services.economy import get_account_state

    conn = quest_db
    _add_quest_item_to_sheet(conn)
    quests.offer_quest(conn, CAMPAIGN, QUEST_ID, content_root=CONTENT)
    quests.accept_quest(conn, CAMPAIGN, QUEST_ID, content_root=CONTENT)
    before = _pack_count(conn)

    result = quests.deliver_quest_item(
        conn,
        CAMPAIGN,
        QUEST_ID,
        "wrong-item-id",
        NPC_ID,
        content_root=CONTENT,
        character_id="delver",
        has_item_fn=lambda iid: {"ok": True, "found": False},
        remove_item_fn=lambda **kw: {"ok": False, "error": "should not remove"},
    )

    assert result["ok"] is False
    assert _pack_count(conn) == before
    state = get_account_state(conn, CAMPAIGN)
    assert state["quests"][QUEST_ID]["objectives"]["return-ring"] != "done"


def test_sell_quest_item_blocked(quest_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import EconomyError, sell_item

    conn = quest_db
    instance_id = _add_quest_item_to_sheet(conn)
    before = _pack_count(conn)
    content = ContentService(CONTENT)

    with pytest.raises(EconomyError, match="Quest items cannot be sold"):
        sell_item(
            conn,
            content,
            campaign_slug=CAMPAIGN,
            session_id="sess1",
            character_id="delver",
            instance_id=instance_id,
        )

    assert _pack_count(conn) == before


def test_stash_deposit_quest_item_blocked(quest_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import EconomyError, stash_deposit_item

    conn = quest_db
    instance_id = _add_quest_item_to_sheet(conn)
    before = _pack_count(conn)
    content = ContentService(CONTENT)

    with pytest.raises(EconomyError, match="Quest items cannot be deposited"):
        stash_deposit_item(
            conn,
            content,
            campaign_slug=CAMPAIGN,
            session_id="sess1",
            character_id="delver",
            instance_id=instance_id,
        )

    assert _pack_count(conn) == before


def test_deliver_quest_item_happy_path(quest_bridge):
    bridge = quest_bridge
    bridge.offer_quest(QUEST_ID)
    bridge.accept_quest(QUEST_ID)
    _add_quest_item_to_sheet(bridge.ctx.conn)

    from tomb_gm.services.economy import get_account_state, save_account_state

    account = get_account_state(bridge.ctx.conn, CAMPAIGN)
    entry = account["quests"][QUEST_ID]
    entry["objectives"]["enter-undercrypt"] = "done"
    entry["objectives"]["recover-ring"] = "done"
    account["quests"][QUEST_ID] = entry
    save_account_state(bridge.ctx.conn, CAMPAIGN, account)

    result = bridge.deliver_quest_item(
        QUEST_ID,
        QUEST_ITEM,
        NPC_ID,
        character_id="delver",
    )

    assert result["ok"] is True
    assert result["objective_id"] == "return-ring"
    assert result["state"] == "ready_to_turn_in"
    has_after = bridge.has_pack_item(QUEST_ITEM, character_id="delver")
    assert has_after["found"] is False
    listed = bridge.list_quests()
    assert listed["quests"][QUEST_ID]["state"] == "ready_to_turn_in"
    assert listed["quests"][QUEST_ID]["objectives"]["return-ring"] == "done"
