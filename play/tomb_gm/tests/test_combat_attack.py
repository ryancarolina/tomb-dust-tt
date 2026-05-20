"""Tests for combat_attack service function."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"


@pytest.fixture()
def combat_ctx(tmp_path):
    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character
    from tomb_gm.domain.character import set_roster_slot
    from tomb_gm.services.simulation.combat import combat_attack, start_combat

    ws = tmp_path / "ws"
    (ws / ".local").mkdir(parents=True)
    (ws / "campaigns").mkdir()
    import os
    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(f"content_root: {rel_build.as_posix()}\n", encoding="utf-8")
    cfg = load_config(ws)
    content_root = cfg.content_root
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
        content_root=content_root,
        monster_specs=["grave-ghoul:1"],
        include_party=True,
        campaign_slug="test",
        seed=3,
    )
    assert start["ok"] is True
    ghoul_id = start["combatants"][0]["id"]
    yield {
        "conn": conn,
        "cfg": cfg,
        "session_id": session_id,
        "ghoul_id": ghoul_id,
        "combat_attack": combat_attack,
        "content_root": content_root,
    }
    conn.close()


def test_combat_attack_hits_and_damages(combat_ctx):
    ctx = combat_ctx
    before = json.loads(
        ctx["conn"].execute(
            "SELECT combatants_json FROM combat_state WHERE session_id = ?",
            (ctx["session_id"],),
        ).fetchone()["combatants_json"]
    )
    ghoul_hp_before = next(c["hp"] for c in before if c["id"] == ctx["ghoul_id"])

    result = ctx["combat_attack"](
        ctx["conn"],
        ctx["session_id"],
        "sammy",
        ctx["ghoul_id"],
        content_root=ctx["content_root"],
        campaign_slug="test",
        seed=99,
        enforce_turn=False,
    )
    assert result.get("ok") is True or result.get("hit") is not None
    assert "attacker" in result
    assert result["target"] == ctx["ghoul_id"]

    after = json.loads(
        ctx["conn"].execute(
            "SELECT combatants_json FROM combat_state WHERE session_id = ?",
            (ctx["session_id"],),
        ).fetchone()["combatants_json"]
    )
    ghoul_hp_after = next(c["hp"] for c in after if c["id"] == ctx["ghoul_id"])
    if result.get("hit"):
        assert ghoul_hp_after < ghoul_hp_before


def test_combat_attack_unknown_attacker(combat_ctx):
    ctx = combat_ctx
    result = ctx["combat_attack"](
        ctx["conn"],
        ctx["session_id"],
        "nobody",
        ctx["ghoul_id"],
        content_root=ctx["content_root"],
        campaign_slug="test",
    )
    assert result["ok"] is False
