from __future__ import annotations

import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.cli.cmd_character import handle_create
from tomb_gm.cli.cmd_core import handle_status
from tomb_gm.cli.cmd_roll import handle_attributes
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect, run_migrations
from tomb_gm.domain.character import roll_attribute_scores, standard_attribute_pool

REPO = Path(__file__).resolve().parents[3]
WORKSPACE = REPO / "play" / "workspace"
CAMPAIGN = "roll-attr-test"


@pytest.fixture()
def ctx():
    ws = resolve_workspace(str(WORKSPACE))
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO campaigns "
        "(slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (CAMPAIGN, "Roll Attr Test", "{}", "{}", now, now),
    )
    conn.execute("DELETE FROM characters WHERE campaign_slug = ?", (CAMPAIGN,))
    conn.commit()
    from tomb_gm.cli.context import CommandContext

    yield CommandContext(config=cfg, conn=conn)
    conn.close()


def test_roll_attribute_scores_range():
    scores, detail = roll_attribute_scores(random.Random(42))
    assert set(scores) == {"STR", "AGI", "STA", "INT", "SPI", "LUC"}
    assert all(1 <= v <= 10 for v in scores.values())
    assert len(detail) == 6


def test_standard_array_pool():
    meta, pool = standard_attribute_pool()
    assert meta["method"] == "standard-array"
    assert pool == [15, 14, 13, 12, 10, 8]


def test_roll_attributes_cli_seeded(ctx):
    out = handle_attributes(
        argparse.Namespace(workspace=str(ctx.config.workspace), method="roll", seed=99),
        ctx,
    )
    expected, _ = roll_attribute_scores(random.Random(99))
    assert out["ok"] is True
    assert out["attributes"] == expected


def test_character_create_roll_attributes(ctx):
    out = handle_create(
        argparse.Namespace(
            workspace=str(ctx.config.workspace),
            campaign=CAMPAIGN,
            name="Rolled",
            base_class="militia",
            character_id=None,
            str=None,
            agi=None,
            sta=None,
            int=None,
            spi=None,
            luc=None,
            skills=None,
            roll_attributes=True,
            seed=1,
        ),
        ctx,
    )
    assert out["ok"] is True
    assert "attribute_rolls" in out
    assert out["attributes"]["STR"] >= 1


def test_status_awaiting_character_creation(ctx):
    """Empty roster + active session → CHARACTER_CREATION (not PLAYER_ACTIONS)."""
    session_id = "test-session-char-create"
    now = datetime.now(timezone.utc).isoformat()
    ctx.conn.execute(
        "INSERT OR REPLACE INTO sessions "
        "(id, campaign_slug, started_at, ended_at) VALUES (?, ?, ?, NULL)",
        (session_id, CAMPAIGN, now),
    )
    ctx.conn.execute(
        "INSERT OR REPLACE INTO party_state "
        "(session_id, address, mode, phase, clocks_json, stamp_json, gold_in_transit) "
        "VALUES (?, '32-C', 'surface', 'preparation', ?, NULL, 0)",
        (session_id, '{"ingress":0,"delve":0,"extract":0,"max":6}'),
    )
    ctx.conn.commit()
    ctx.config.active_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.config.active_path.write_text(
        f'{{"session_id": "{session_id}", "campaign_slug": "{CAMPAIGN}"}}',
        encoding="utf-8",
    )
    try:
        st = handle_status(
            argparse.Namespace(workspace=str(ctx.config.workspace)),
            ctx,
        )
        assert st["awaiting"] == "CHARACTER_CREATION"
        assert st["roster"] == []
    finally:
        ctx.config.active_path.unlink(missing_ok=True)
        ctx.conn.execute("DELETE FROM party_state WHERE session_id = ?", (session_id,))
        ctx.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        ctx.conn.commit()
