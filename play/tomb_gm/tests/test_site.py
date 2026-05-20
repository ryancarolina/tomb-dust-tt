from __future__ import annotations

import json
import uuid

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
from tomb_gm.db.connection import run_migrations
from helpers import seed_campaign, utc_now


def _seed_session(
    args_ns,
    test_config,
    test_db,
    *,
    phase: str = "delve",
    address: str = "32-C-UG-1",
    gold: int = 200,
    stamp_primary: str = "32-C-UG-1",
) -> str:
    handle_init(args_ns(), None)
    run_migrations(test_db)
    slug = "ws7-test"
    session_id = str(uuid.uuid4())
    now = utc_now()
    stamp = {
        "primary": stamp_primary,
        "surfaceEntry": "32-C",
        "danger": "skirmisher",
        "costGp": 45,
        "validDays": 30,
        "issuedAt": now.replace("+00:00", "Z"),
    }
    seed_campaign(test_db, slug, "WS7 Test")
    test_db.execute(
        """
        INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase)
        VALUES (?, ?, ?, NULL, ?)
        """,
        (session_id, slug, now, phase),
    )
    test_db.execute(
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
    test_db.commit()
    test_config.active_path.write_text(
        json.dumps({"campaign_slug": slug, "session_id": session_id}),
        encoding="utf-8",
    )
    return session_id


@pytest.fixture
def session_id(args_ns, test_config, test_db):
    sid = _seed_session(args_ns, test_config, test_db)
    yield sid
    if test_config.active_path.exists():
        test_config.active_path.unlink()


def test_site_enter_move_where_exits(args_ns, session_id):
    enter = handle_site_enter(args_ns(site_id="breley-undercrypt"), None)
    assert enter["ok"] is True
    assert enter["mode"] == "site"
    assert enter["node_id"] == "chapel-stairs"

    where = handle_site_where(args_ns(), None)
    assert where["node_id"] == "chapel-stairs"
    assert "entry" in where["node"]["tags"]

    exits = handle_site_exits(args_ns(), None)
    assert any(e["to"] == "ossuary-hall" and e["passable"] for e in exits["exits"])

    move = handle_site_move(args_ns(to_node="ossuary-hall"), None)
    assert move["to"] == "ossuary-hall"

    where2 = handle_site_where(args_ns(), None)
    assert where2["node_id"] == "ossuary-hall"


def test_clock_tick_updates_party(args_ns, session_id):
    tick = handle_clock_tick(args_ns(clock="delve", reason="loud fight", segments=1), None)
    assert tick["clocks"]["delve"] == 1

    show = handle_clock_show(args_ns(), None)
    assert show["clocks"]["delve"] == 1


def test_phase_set_and_registry_stamp_buy(args_ns, session_id):
    extract = handle_phase_set(args_ns(phase="extract"), None)
    assert extract["phase"] == "extract"

    buy = handle_registry_stamp_buy(
        args_ns(address="32-C-UG-1", danger="skirmisher", surface_entry=None),
        None,
    )
    assert buy["stamp"]["primary"] == "32-C-UG-1"
    assert buy["gold_in_transit"] < 200


def test_locked_edge_blocks_move(args_ns, session_id):
    handle_site_enter(args_ns(site_id="breley-undercrypt"), None)
    handle_site_move(args_ns(to_node="ossuary-hall"), None)
    with pytest.raises(Exception, match="locked"):
        handle_site_move(args_ns(to_node="marshal-tomb"), None)
