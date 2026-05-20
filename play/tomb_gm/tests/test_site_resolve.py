"""Tests for site address resolution."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.cli.context import CommandContext
from tomb_gm.config import load_config
from tomb_gm.db.connection import connect, run_migrations
from tomb_gm.domain.session import resume_session, start_session
from tomb_gm.services.content import ContentService
from tomb_gm.services.extraction import (
    ExtractionError,
    advance_phase_for_dungeon_entry,
    set_phase,
)
from tomb_gm.services.site_resolve import resolve_site_address

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"
CAMPAIGN = "site-resolve-test"
SESSION = "sess-site-resolve-test"


@pytest.fixture
def content() -> ContentService:
    return ContentService(BUILD)


@pytest.fixture
def play_ctx(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shutil.copy(REPO / "play" / "workspace" / "config.example.yaml", workspace / "config.yaml")
    ws = workspace.resolve()
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO campaigns "
        "(slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (CAMPAIGN, "Site Resolve", "{}", "{}", now, now),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase) "
        "VALUES (?, ?, ?, NULL, 'preparation')",
        (SESSION, CAMPAIGN, now),
    )
    conn.execute(
        "INSERT INTO party_state "
        "(session_id, address, mode, site_id, site_node_id, phase, stamp_json, clocks_json) "
        "VALUES (?, '32-C', 'surface', NULL, NULL, 'preparation', NULL, "
        "'{\"ingress\":0,\"delve\":0,\"extract\":0,\"max\":6}')",
        (SESSION,),
    )
    conn.commit()
    ctx = CommandContext(config=cfg, conn=conn)
    cfg.active_path.write_text(
        json.dumps({"session_id": SESSION, "campaign_slug": CAMPAIGN}),
        encoding="utf-8",
    )
    yield ctx
    conn.close()


def test_resolve_av_grid_direct(content: ContentService):
    out = resolve_site_address(content, "32-C-UG-1", current_surface_address="32-C")
    assert out["ok"] is True
    assert out["site_address"] == "32-C-UG-1"


def test_resolve_site_slug(content: ContentService):
    out = resolve_site_address(content, "breley-undercrypt", current_surface_address="32-C")
    assert out["ok"] is True
    assert out["site_address"] == "32-C-UG-1"
    assert out["resolved_from"] == "breley-undercrypt"


def test_resolve_display_name_from_surface_children(content: ContentService):
    out = resolve_site_address(content, "undercrypt", current_surface_address="32-C")
    assert out["ok"] is True
    assert out["site_address"] == "32-C-UG-1"


def test_resolve_ambiguous_crypts(content: ContentService):
    out = resolve_site_address(content, "breley", current_surface_address="32-C")
    assert out["ok"] is False
    assert out["error"] == "AMBIGUOUS_SITE"
    assert len(out["options"]) >= 2


def test_resolve_unknown(content: ContentService):
    out = resolve_site_address(content, "nonexistent-dungeon", current_surface_address="32-C")
    assert out["ok"] is False
    assert out["error"] == "UNKNOWN_SITE"


def test_advance_phase_for_dungeon_entry(play_ctx):
    result = advance_phase_for_dungeon_entry(play_ctx)
    assert result["ok"] is True
    assert result["phase"] == "delve"

    row = play_ctx.conn.execute(
        "SELECT phase FROM party_state WHERE session_id = ?", (SESSION,)
    ).fetchone()
    assert row["phase"] == "delve"


def test_set_phase_rejects_preparation_to_delve(play_ctx):
    with pytest.raises(ExtractionError, match="Cannot transition"):
        set_phase(play_ctx, "delve")


def test_resume_loads_sole_save_session(tmp_path: Path):
    workspace = tmp_path / "resume-workspace"
    workspace.mkdir()
    shutil.copy(REPO / "play" / "workspace" / "config.example.yaml", workspace / "config.yaml")
    cfg = load_config(workspace.resolve())
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('salt-road', 'Salt Road', '{}', '{}', ?, ?)",
        (now, now),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase) "
        "VALUES ('current', 'salt-road', ?, NULL, 'preparation')",
        (now,),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase, clocks_json) "
        "VALUES ('current', '32-C', 'surface', 'preparation', '{\"ingress\":0,\"delve\":0,\"extract\":0,\"max\":6}')",
    )
    conn.execute(
        "INSERT INTO characters (id, campaign_slug, slot, sheet_json, alive, created_at) "
        "VALUES ('dig', 'salt-road', 1, '{\"displayName\":\"Dig\",\"hp\":{\"current\":35,\"max\":35}}', 1, ?)",
        (now,),
    )
    conn.commit()

    result = resume_session(conn, cfg)
    assert result["ok"] is True
    assert result["session_id"] == "current"
    assert result["campaign_slug"] == "salt-road"
    conn.close()


def test_start_replaces_existing_save_session(tmp_path: Path):
    workspace = tmp_path / "start-workspace"
    workspace.mkdir()
    shutil.copy(REPO / "play" / "workspace" / "config.example.yaml", workspace / "config.yaml")
    cfg = load_config(workspace.resolve())
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('old-camp', 'Old', '{}', '{}', ?, ?), ('new-camp', 'New', '{}', '{}', ?, ?)",
        (now, now, now, now),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase) "
        "VALUES ('current', 'old-camp', ?, NULL, 'delve')",
        (now,),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase, clocks_json) "
        "VALUES ('current', '31-C', 'surface', 'delve', '{\"ingress\":0,\"delve\":0,\"extract\":0,\"max\":6}')",
    )
    conn.commit()

    from tomb_gm.domain.session import start_session

    result = start_session(conn, cfg, "new-camp")
    assert result["ok"] is True
    assert result["session_id"] == "current"
    assert result["campaign_slug"] == "new-camp"
    assert result["address"] == "32-C"

    rows = conn.execute("SELECT id FROM sessions WHERE ended_at IS NULL").fetchall()
    assert len(rows) == 1
    assert rows[0]["id"] == "current"

    party = conn.execute(
        "SELECT address, phase FROM party_state WHERE session_id = 'current'"
    ).fetchone()
    assert party["address"] == "32-C"
    assert party["phase"] == "preparation"
    conn.close()
