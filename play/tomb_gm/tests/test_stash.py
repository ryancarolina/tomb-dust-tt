"""Tests for account stash v3 and hub gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"


@pytest.fixture
def stash_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character
    from tomb_gm.domain.creation import starting_kit_inventory
    from tomb_gm.services.economy import migrate_account_stash

    conn = connect(tmp_path / "stash.db")
    run_migrations(conn)
    state = migrate_account_stash({"stashGp": 50, "stashItems": ["legacy-ignored"]})
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('stash-test', 'Stash', '{}', ?, '2026-01-01', '2026-01-01')",
        (json.dumps(state),),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES ('sess1', 'stash-test', '2026-01-01', 'delve')"
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode) VALUES ('sess1', '32-C', 'surface')"
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="stash-test",
        display_name="Carrier",
        base_class="novice",
        character_id="carrier",
        inventory=starting_kit_inventory(CONTENT, "novice"),
        gold_gp=10,
    )
    conn.execute("UPDATE characters SET slot = 1 WHERE id = 'carrier'")
    conn.commit()
    return conn


def test_migrate_account_stash():
    from tomb_gm.services.economy import migrate_account_stash

    state = migrate_account_stash({"stashGp": 99, "stashItems": ["old"]})
    assert state["stashGp"] == 99
    assert state["stash"]["inventoryVersion"] == 3
    assert state["stash"]["pack"] == []
    assert "stashItems" not in state


def test_stash_deposit_item_reids(stash_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import stash_deposit_item, get_account_state

    conn = stash_db
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'carrier'").fetchone()["sheet_json"]
    )
    carried = next(i for i in sheet["inventory"]["pack"] if not i.get("equipped"))
    source_id = carried["instanceId"]
    content = ContentService(CONTENT)
    result = stash_deposit_item(
        conn,
        content,
        campaign_slug="stash-test",
        session_id="sess1",
        character_id="carrier",
        instance_id=source_id,
    )
    assert result["ok"] is True
    state = get_account_state(conn, "stash-test")
    stash_ids = {i["instanceId"] for i in state["stash"]["pack"]}
    assert source_id not in stash_ids


def test_stash_blocked_in_dungeon(stash_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import EconomyError, stash_deposit_item

    conn = stash_db
    conn.execute("UPDATE party_state SET mode = 'dungeon', site_id = '32-C-UG-1' WHERE session_id = 'sess1'")
    conn.commit()
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'carrier'").fetchone()["sheet_json"]
    )
    carried = next(i for i in sheet["inventory"]["pack"] if not i.get("equipped"))
    content = ContentService(CONTENT)
    with pytest.raises(EconomyError, match="surface"):
        stash_deposit_item(
            conn,
            content,
            campaign_slug="stash-test",
            session_id="sess1",
            character_id="carrier",
            instance_id=carried["instanceId"],
        )
