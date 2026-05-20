"""Tests for vendor buy/sell and fence gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"


@pytest.fixture
def economy_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character
    from tomb_gm.domain.creation import starting_kit_inventory

    conn = connect(tmp_path / "economy.db")
    run_migrations(conn)
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('econ-test', 'Econ', '{}', '{}', '2026-01-01', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES ('sess1', 'econ-test', '2026-01-01', 'delve')"
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode) VALUES ('sess1', '32-C', 'surface')"
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="econ-test",
        display_name="Trader",
        base_class="novice",
        character_id="trader",
        inventory=starting_kit_inventory(CONTENT, "novice"),
        gold_gp=200,
    )
    conn.execute("UPDATE characters SET slot = 1 WHERE id = 'trader'")
    conn.commit()
    return conn


def test_sell_equipped_blocked(economy_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import EconomyError, sell_item

    conn = economy_db
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'trader'").fetchone()["sheet_json"]
    )
    equipped = next(i for i in sheet["inventory"]["pack"] if i.get("equipped"))
    content = ContentService(CONTENT)
    with pytest.raises(EconomyError, match="equipped"):
        sell_item(
            conn,
            content,
            campaign_slug="econ-test",
            session_id="sess1",
            character_id="trader",
            instance_id=equipped["instanceId"],
        )


def test_sell_unequipped_by_instance(economy_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.economy import sell_item

    conn = economy_db
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'trader'").fetchone()["sheet_json"]
    )
    carried = next(i for i in sheet["inventory"]["pack"] if not i.get("equipped"))
    before_gold = sheet["goldGp"]
    content = ContentService(CONTENT)
    result = sell_item(
        conn,
        content,
        campaign_slug="econ-test",
        session_id="sess1",
        character_id="trader",
        instance_id=carried["instanceId"],
    )
    assert result["ok"] is True
    assert result["net_gp"] >= 1
    after = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'trader'").fetchone()["sheet_json"]
    )
    assert after["goldGp"] > before_gold
