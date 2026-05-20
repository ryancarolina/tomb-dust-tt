"""Tests for loot resolver and grant_loot persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"


@pytest.fixture
def loot_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character

    db_path = tmp_path / "loot.db"
    conn = connect(db_path)
    run_migrations(conn)
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('loot-test', 'Loot', '{}', '{}', '2026-01-01', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES ('sess1', 'loot-test', '2026-01-01', 'delve')"
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="loot-test",
        display_name="Looter",
        base_class="novice",
        character_id="delver-1",
        gold_gp=0,
    )
    conn.execute("UPDATE characters SET slot = 1 WHERE id = 'delver-1'")
    conn.commit()
    return conn


def test_loot_resolver_migrates_item_ids():
    from tomb_gm.services.loot_resolver import LootResolver, load_loot_id_migration

    migration = load_loot_id_migration(CONTENT)
    assert migration.get("burial-goods") == "burial-goods-junk"
    resolver = LootResolver(CONTENT)
    result = resolver.roll(tier="hazard", rng=__import__("random").Random(99))
    assert result["ok"] is True
    if result.get("grants"):
        assert all(g["itemId"] != "burial-goods" for g in result["grants"])


def test_grant_loot_persists_to_active_delver(loot_db):
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.loot_resolver import LootResolver, grant_loot

    conn = loot_db
    content = ContentService(CONTENT)
    resolver = LootResolver(CONTENT)
    rolled = {"ok": True, "gp": 12, "grants": [{"itemId": "burial-goods-junk", "quantity": 2}]}
    result = grant_loot(conn, content, campaign_slug="loot-test", loot_result=rolled)
    assert result["ok"] is True
    assert result["character_id"] == "delver-1"
    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'delver-1'").fetchone()["sheet_json"]
    )
    assert sheet["goldGp"] == 12
    pack = sheet["inventory"]["pack"]
    assert any(i["itemId"] == "burial-goods-junk" for i in pack)
