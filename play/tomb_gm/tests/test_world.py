from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
WORKSPACE = PLAY / "workspace"
CAMPAIGN_SLUG = "ws2-test"


def _run(*args: str, expect_ok: bool = True) -> dict:
    import os

    proc = subprocess.run(
        [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE), *args],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    raw = proc.stdout or proc.stderr
    if expect_ok and proc.returncode != 0:
        raise AssertionError(f"CLI failed ({args}): {proc.stderr or proc.stdout}")
    if not expect_ok and proc.returncode == 0:
        data = json.loads(proc.stdout)
        if data.get("ok"):
            raise AssertionError(f"Expected failure for {args}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Non-JSON output for {args}: {raw}") from exc


def _bootstrap_session() -> str:
    from tomb_gm.config import load_config, resolve_workspace
    from tomb_gm.db.connection import connect

    ws = resolve_workspace(str(WORKSPACE))
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, '{}', '{}', ?, ?)",
        (CAMPAIGN_SLUG, "WS2 Test", now, now),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase) VALUES (?, ?, ?, NULL, ?)",
        (session_id, CAMPAIGN_SLUG, now, "preparation"),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "preparation"),
    )
    conn.commit()
    cfg.active_path.write_text(
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


@pytest.fixture(scope="module")
def active_session() -> str:
    _run("init")
    try:
        _run("campaign", "new", "--slug", CAMPAIGN_SLUG, "--name", "WS2 Test")
        out = _run("session", "start", "--campaign", CAMPAIGN_SLUG)
        return out["session_id"]
    except AssertionError:
        return _bootstrap_session()


def test_content_cell_32c():
    out = _run("content", "cell", "32-C")
    assert out["ok"] is True
    assert out["cell"]["displayName"] == "Breley Keep"


def test_content_monster_grave_ghoul():
    out = _run("content", "monster", "grave-ghoul")
    assert out["ok"] is True
    assert out["monster"]["id"] == "grave-ghoul"


def test_content_monster_missing_blocks():
    out = _run("content", "monster", "hollow-knight", expect_ok=False)
    assert out["ok"] is False
    assert out["blocked"] is True
    assert out["blockers"][0]["code"] == "MISSING_MONSTER_JSON"
    assert out["blockers"][0]["monster_id"] == "hollow-knight"


def test_content_weapon_dagger():
    out = _run("content", "weapon", "dagger")
    assert out["ok"] is True
    assert out["weapon"]["id"] == "dagger"


def test_world_where(active_session: str):
    out = _run("world", "where")
    assert out["ok"] is True
    assert out["address"] == "32-C"
    assert out["cell"]["displayName"] == "Breley Keep"


def test_world_exits_includes_neighbors(active_session: str):
    out = _run("world", "exits")
    assert out["ok"] is True
    addresses = [e["address"] for e in out["exits"]]
    assert "33-C" in addresses
    assert "32-C-UG-1" in addresses


def test_world_travel_surface(active_session: str):
    out = _run("world", "travel", "--to", "33-C")
    assert out["ok"] is True
    assert out["to"] == "33-C"
    where = _run("world", "where")
    assert where["address"] == "33-C"


def test_world_travel_layer(active_session: str):
    _run("world", "travel", "--to", "32-C")
    out = _run("world", "travel", "--to", "32-C-UG-1")
    assert out["ok"] is True
    where = _run("world", "where")
    assert where["address"] == "32-C-UG-1"


def test_world_travel_invalid(active_session: str):
    _run("world", "travel", "--to", "32-C")
    out = _run("world", "travel", "--to", "14-P", expect_ok=False)
    assert out["ok"] is False
    assert out["error"] == "INVALID_TRAVEL"


def test_world_travel_unknown_address(active_session: str):
    out = _run("world", "travel", "--to", "99-Z", expect_ok=False)
    assert out["ok"] is False
    assert out["error"] == "UNKNOWN_ADDRESS"
