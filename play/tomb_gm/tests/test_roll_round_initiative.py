"""Per-round initiative re-roll tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"


@pytest.fixture()
def combat_session(tmp_path):
    import os

    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character, set_roster_slot
    from tomb_gm.services.simulation.combat import roll_round_initiative, start_combat

    ws = tmp_path / "ws"
    (ws / ".local").mkdir(parents=True)
    (ws / "campaigns").mkdir()
    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(f"content_root: {rel_build.as_posix()}\n", encoding="utf-8")
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("test", "Test", now, now),
    )
    session_id = "current"
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, "test", now, "delve"),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "delve"),
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="test",
        display_name="Sammy",
        base_class="novice",
        character_id="sammy",
        skill_ids=["medicine", "spellcasting", "lore"],
    )
    set_roster_slot(conn, campaign_slug="test", slot=1, character_id="sammy")
    start = start_combat(
        conn,
        session_id=session_id,
        content_root=cfg.content_root,
        monster_specs=["grave-ghoul:1"],
        include_party=True,
        campaign_slug="test",
        seed=1,
    )
    assert start["ok"] is True
    order_r1 = [e["id"] for e in start["initiative"]]
    r2 = roll_round_initiative(
        conn,
        session_id,
        content_root=cfg.content_root,
        campaign_slug="test",
        seed=99,
        increment_round=True,
    )
    assert r2["ok"] is True
    assert r2["round"] == 2
    order_r2 = [e["id"] for e in r2["initiative"]]
    assert len(order_r2) == 2
    assert set(order_r2) == set(order_r1)
    yield {"conn": conn, "session_id": session_id, "cfg": cfg}
    conn.close()


def test_initiative_rerolls_each_round(combat_session):
    ctx = combat_session
    from tomb_gm.services.simulation.combat import roll_round_initiative

    r3 = roll_round_initiative(
        ctx["conn"],
        ctx["session_id"],
        content_root=ctx["cfg"].content_root,
        campaign_slug="test",
        seed=42,
        increment_round=True,
    )
    assert r3["round"] == 3
    assert r3["turn_index"] == 0
