from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.services.content import ContentService
from tomb_gm.services.world import WorldService, resolve_surface_address

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"

CAMPAIGN_SLUG = "ws2-test"


@pytest.fixture
def content() -> ContentService:
    return ContentService(BUILD)


def _bootstrap_session(test_config, test_db) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    test_db.execute(
        "INSERT OR IGNORE INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, '{}', '{}', ?, ?)",
        (CAMPAIGN_SLUG, "WS2 Test", now, now),
    )
    test_db.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase) VALUES (?, ?, ?, NULL, ?)",
        (session_id, CAMPAIGN_SLUG, now, "preparation"),
    )
    test_db.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "preparation"),
    )
    test_db.commit()
    test_config.active_path.write_text(
        json.dumps(
            {
                "campaign_slug": CAMPAIGN_SLUG,
                "session_id": session_id,
                "activated_at": now,
            }
        ),
        encoding="utf-8",
    )
    return session_id


@pytest.fixture
def active_session(run_tomb_gm, test_config, test_db):
    run_tomb_gm("init")
    try:
        run_tomb_gm("campaign", "new", "--slug", CAMPAIGN_SLUG, "--name", "WS2 Test")
        out = run_tomb_gm("session", "start", "--campaign", CAMPAIGN_SLUG)
        return out["session_id"]
    except AssertionError:
        return _bootstrap_session(test_config, test_db)


def test_content_cell_32c(run_tomb_gm):
    run_tomb_gm("init")
    out = run_tomb_gm("content", "cell", "32-C")
    assert out["ok"] is True
    assert out["cell"]["displayName"] == "Breley Keep"


def test_content_monster_grave_ghoul(run_tomb_gm):
    run_tomb_gm("init")
    out = run_tomb_gm("content", "monster", "grave-ghoul")
    assert out["ok"] is True
    assert out["monster"]["id"] == "grave-ghoul"


def test_content_monster_missing_blocks(run_tomb_gm):
    run_tomb_gm("init")
    out = run_tomb_gm("content", "monster", "hollow-knight", expect_ok=False)
    assert out["ok"] is False
    assert out["blocked"] is True
    assert out["blockers"][0]["code"] == "MISSING_MONSTER_JSON"
    assert out["blockers"][0]["monster_id"] == "hollow-knight"


def test_content_weapon_dagger(run_tomb_gm):
    run_tomb_gm("init")
    out = run_tomb_gm("content", "weapon", "dagger")
    assert out["ok"] is True
    assert out["weapon"]["id"] == "dagger"


def test_world_where(run_tomb_gm, active_session):
    out = run_tomb_gm("world", "where")
    assert out["ok"] is True
    assert out["address"] == "32-C"
    assert out["cell"]["displayName"] == "Breley Keep"


def test_world_exits_includes_neighbors(run_tomb_gm, active_session):
    out = run_tomb_gm("world", "exits")
    assert out["ok"] is True
    addresses = [e["address"] for e in out["exits"]]
    assert "33-C" in addresses
    assert "32-C-UG-1" in addresses


def test_world_travel_surface(run_tomb_gm, active_session):
    out = run_tomb_gm("world", "travel", "--to", "33-C")
    assert out["ok"] is True
    assert out["to"] == "33-C"
    where = run_tomb_gm("world", "where")
    assert where["address"] == "33-C"


def test_world_travel_layer(run_tomb_gm, active_session):
    run_tomb_gm("world", "travel", "--to", "32-C")
    out = run_tomb_gm("world", "travel", "--to", "32-C-UG-1")
    assert out["ok"] is True
    where = run_tomb_gm("world", "where")
    assert where["address"] == "32-C-UG-1"


def test_world_travel_invalid(run_tomb_gm, active_session):
    run_tomb_gm("world", "travel", "--to", "32-C")
    out = run_tomb_gm("world", "travel", "--to", "14-P", expect_ok=False)
    assert out["ok"] is False
    assert out["error"] == "INVALID_TRAVEL"


def test_world_travel_unknown_address(run_tomb_gm, active_session):
    out = run_tomb_gm("world", "travel", "--to", "99-Z", expect_ok=False)
    assert out["ok"] is False
    assert out["error"] == "UNKNOWN_ADDRESS"


def test_resolve_surface_address_kings_road(content: ContentService):
    out = resolve_surface_address(content, "kings road", from_address="32-C")
    assert out["ok"] is True
    assert out["address"] == "33-C"
    assert out["resolved_from"] == "kings road"


def test_resolve_surface_address_kings_road_not_current_cell(content: ContentService):
    out = resolve_surface_address(content, "kings road", from_address="32-C")
    assert out["ok"] is True
    assert out["address"] != "32-C"


def test_resolve_surface_address_exit_scope(content: ContentService):
    out = resolve_surface_address(content, "silversea cove", from_address="32-C")
    assert out["ok"] is False
    assert out["error"] == "UNKNOWN_ADDRESS"


def test_resolve_surface_address_ambiguous(content: ContentService):
    out = resolve_surface_address(content, "silversea cove", from_address="1-B")
    assert out["ok"] is False
    assert out["error"] == "AMBIGUOUS_ADDRESS"
    option_addrs = {opt["address"] for opt in out["options"]}
    assert option_addrs == {"1-A", "2-B"}


def test_resolve_surface_address_use_enter_dungeon(content: ContentService):
    out = resolve_surface_address(content, "undercrypt", from_address="32-C")
    assert out["ok"] is False
    assert out["error"] == "USE_ENTER_DUNGEON"
    assert "enter" in out["message"].lower() or "dungeon" in out["message"].lower()


def test_resolve_surface_address_canonical_passthrough(content: ContentService):
    out = resolve_surface_address(content, "33-C", from_address="32-C")
    assert out["ok"] is True
    assert out["address"] == "33-C"


def test_resolve_surface_address_then_can_travel(content: ContentService):
    resolved = resolve_surface_address(content, "kings road", from_address="32-C")
    assert resolved["ok"] is True
    world = WorldService(content)
    ok, code = world.can_travel("32-C", resolved["address"])
    assert ok is True
    assert code is None


def test_world_travel_friendly_kings_road_bridge(
    isolated_workspace, run_tomb_gm, test_config, test_db
):
    run_tomb_gm("init")
    _bootstrap_session(test_config, test_db)
    from gm.bridge import GameBridge

    bridge = GameBridge(workspace=isolated_workspace)
    try:
        result = bridge.world_travel(to_address="kings road")
        assert result["ok"] is True
        assert result["to"] == "33-C"
        assert bridge.status()["party"]["address"] == "33-C"
    finally:
        bridge.ctx.conn.close()
