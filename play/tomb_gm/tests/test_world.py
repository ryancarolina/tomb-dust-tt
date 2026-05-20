from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

CAMPAIGN_SLUG = "ws2-test"


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
