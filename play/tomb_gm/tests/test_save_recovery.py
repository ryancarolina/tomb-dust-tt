"""Save slot recovery when tests orphan the session campaign."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from helpers import BUILD, make_isolated_workspace
from tomb_gm.config import load_config
from tomb_gm.db.connection import connect, run_migrations
from tomb_gm.domain.character import create_character, set_roster_slot
from tomb_gm.domain.campaign import create_campaign
from tomb_gm.domain.session import SAVE_SESSION_ID, resume_session, start_session


@pytest.fixture()
def polluted_workspace(tmp_path):
    ws = make_isolated_workspace(tmp_path)
    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(
        f"content_root: {rel_build.as_posix()}\nlocal_dir: .local\nmax_players: 4\n",
        encoding="utf-8",
    )
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)

    create_campaign(conn, cfg, "salt-road", "Salt Road")
    create_campaign(conn, cfg, "ws2-test", "WS2 Test")
    create_character(
        conn,
        campaign_slug="salt-road",
        display_name="Sammy",
        base_class="novice",
        character_id="sammy",
        skill_ids=["medicine", "spellcasting", "lore"],
    )
    set_roster_slot(conn, campaign_slug="salt-road", slot=1, character_id="sammy")
    start_session(conn, cfg, "ws2-test")

    yield cfg, conn, resume_session
    conn.close()


def test_resume_recovers_orphaned_player_campaign(polluted_workspace):
    cfg, conn, resume_session = polluted_workspace
    result = resume_session(conn, cfg)
    assert result["ok"] is True
    assert result["campaign_slug"] == "salt-road"
    assert result.get("recovered_campaign") is True

    row = conn.execute(
        "SELECT campaign_slug FROM sessions WHERE id = ?", (SAVE_SESSION_ID,)
    ).fetchone()
    assert row["campaign_slug"] == "salt-road"
