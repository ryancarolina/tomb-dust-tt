"""Vertical slice: buy → equip → loot → stash → sell gate (inventory v3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"


@pytest.fixture
def slice_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character, set_roster_slot
    from tomb_gm.domain.creation import starting_kit_inventory
    from tomb_gm.services.economy import migrate_account_stash

    conn = connect(tmp_path / "slice.db")
    run_migrations(conn)
    state = migrate_account_stash({"stashGp": 0})
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('slice', 'Slice', '{}', ?, '2026-01-01', '2026-01-01')",
        (json.dumps(state),),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES ('sess1', 'slice', '2026-01-01', 'delve')"
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode) VALUES ('sess1', '32-C', 'surface')"
    )
    conn.commit()

    create_character(
        conn,
        campaign_slug="slice",
        display_name="Delver",
        base_class="militia",
        character_id="delver",
        inventory=starting_kit_inventory(CONTENT, "militia"),
        gold_gp=100,
    )
    set_roster_slot(conn, campaign_slug="slice", slot=1, character_id="delver")
    conn.commit()
    return conn


def test_extraction_vertical_slice(slice_db):
    from tomb_gm.domain.inventory import ensure_normalized, equip, get_pack
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import EconomyError, buy_from_vendor, list_stash, sell_item, stash_deposit_item
    from tomb_gm.services.loot_resolver import grant_loot

    conn = slice_db
    content = ContentService(CONTENT)

    bought = buy_from_vendor(
        conn,
        content,
        campaign_slug="slice",
        session_id="sess1",
        character_id="delver",
        vendor_id="registry-quartermaster",
        item_id="leather",
        quantity=1,
    )
    assert bought["ok"] is True

    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'delver'").fetchone()["sheet_json"]
    )
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)
    leather = next(i for i in get_pack(sheet) if i["itemId"] == "leather")
    assert equip(get_pack(sheet), leather["instanceId"], "chest", item_lookup=lookup)["ok"] is True
    conn.execute("UPDATE characters SET sheet_json = ? WHERE id = 'delver'", (json.dumps(sheet),))
    conn.commit()

    grant = grant_loot(
        conn,
        content,
        campaign_slug="slice",
        loot_result={"ok": True, "gp": 8, "grants": [{"itemId": "burial-goods-junk", "quantity": 1}]},
    )
    assert grant["ok"] is True
    assert grant["character_id"] == "delver"

    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'delver'").fetchone()["sheet_json"]
    )
    junk = next(i for i in get_pack(sheet) if i["itemId"] == "burial-goods-junk")
    assert stash_deposit_item(
        conn,
        content,
        campaign_slug="slice",
        session_id="sess1",
        character_id="delver",
        instance_id=junk["instanceId"],
    )["ok"] is True
    assert len(list_stash(conn, "slice")["stash"]["pack"]) == 1

    leather_row = next(i for i in get_pack(sheet) if i["itemId"] == "leather")
    with pytest.raises(EconomyError, match="equipped"):
        sell_item(
            conn,
            content,
            campaign_slug="slice",
            session_id="sess1",
            character_id="delver",
            instance_id=leather_row["instanceId"],
        )
