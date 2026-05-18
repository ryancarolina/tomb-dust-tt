from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.cli.cmd_phase import (
    handle_clock_show,
    handle_clock_tick,
    handle_phase_set,
    handle_registry_stamp_buy,
)
from tomb_gm.cli.cmd_site import (
    handle_site_enter,
    handle_site_exits,
    handle_site_move,
    handle_site_where,
)
from tomb_gm.cli.cmd_core import handle_init
from tomb_gm.config import load_config
from tomb_gm.db.connection import connect, run_migrations

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
WORKSPACE = PLAY / "workspace"


def _ns(**kwargs) -> argparse.Namespace:
    base = {"workspace": str(WORKSPACE)}
    base.update(kwargs)
    return argparse.Namespace(**base)


def _seed_session(
    *,
    phase: str = "delve",
    address: str = "32-C-UG-1",
    gold: int = 200,
    stamp_primary: str = "32-C-UG-1",
) -> str:
    handle_init(_ns(), None)
    cfg = load_config(WORKSPACE)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    slug = "ws7-test"
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    stamp = {
        "primary": stamp_primary,
        "surfaceEntry": "32-C",
        "danger": "skirmisher",
        "costGp": 45,
        "validDays": 30,
        "issuedAt": now.replace("+00:00", "Z"),
    }
    conn.execute(
        """
        INSERT OR REPLACE INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at)
        VALUES (?, ?, '{}', '{}', ?, ?)
        """,
        (slug, "WS7 Test", now, now),
    )
    conn.execute(
        """
        INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase)
        VALUES (?, ?, ?, NULL, ?)
        """,
        (session_id, slug, now, phase),
    )
    conn.execute(
        """
        INSERT INTO party_state (
          session_id, address, mode, site_id, site_node_id, phase,
          stamp_json, clocks_json, gold_in_transit, flags_json
        ) VALUES (?, ?, 'surface', NULL, NULL, ?, ?, ?, ?, '{}')
        """,
        (
            session_id,
            address,
            phase,
            json.dumps(stamp),
            json.dumps({"ingress": 0, "delve": 0, "extract": 0, "max": 6}),
            gold,
        ),
    )
    conn.commit()
    conn.close()
    cfg.active_path.write_text(
        json.dumps({"campaign_slug": slug, "session_id": session_id}),
        encoding="utf-8",
    )
    return session_id


@pytest.fixture
def session_id():
    sid = _seed_session()
    yield sid
    cfg = load_config(WORKSPACE)
    if cfg.active_path.exists():
        cfg.active_path.unlink()


def test_site_enter_move_where_exits(session_id):
    enter = handle_site_enter(_ns(site_id="breley-undercrypt"), None)
    assert enter["ok"] is True
    assert enter["mode"] == "site"
    assert enter["node_id"] == "chapel-stairs"

    where = handle_site_where(_ns(), None)
    assert where["node_id"] == "chapel-stairs"
    assert "entry" in where["node"]["tags"]

    exits = handle_site_exits(_ns(), None)
    assert any(e["to"] == "ossuary-hall" and e["passable"] for e in exits["exits"])

    moved = handle_site_move(_ns(to_node="ossuary-hall"), None)
    assert moved["to"] == "ossuary-hall"

    where2 = handle_site_where(_ns(), None)
    assert where2["node_id"] == "ossuary-hall"


def test_clock_tick_updates_party(session_id):
    tick = handle_clock_tick(_ns(clock="delve", reason="loud fight", segments=1), None)
    assert tick["clocks"]["delve"] == 1

    show = handle_clock_show(_ns(), None)
    assert show["clocks"]["delve"] == 1


def test_phase_set_and_registry_stamp_buy(session_id):
    extract = handle_phase_set(_ns(phase="extract"), None)
    assert extract["phase"] == "extract"

    buy = handle_registry_stamp_buy(
        _ns(address="32-C-UG-1", danger="skirmisher", surface_entry=None),
        None,
    )
    assert buy["stamp"]["primary"] == "32-C-UG-1"
    assert buy["gold_in_transit"] < 200


def test_locked_edge_blocks_move(session_id):
    handle_site_enter(_ns(site_id="breley-undercrypt"), None)
    handle_site_move(_ns(to_node="ossuary-hall"), None)
    with pytest.raises(Exception, match="locked"):
        handle_site_move(_ns(to_node="marshal-tomb"), None)
