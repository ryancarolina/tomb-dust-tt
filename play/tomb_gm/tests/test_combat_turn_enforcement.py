"""Turn order enforcement and monster auto-turn chain."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"


@pytest.fixture()
def combat_ctx(tmp_path):
    import os

    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character, set_roster_slot
    from tomb_gm.services.simulation.combat import combat_attack, combat_status, start_combat

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
        seed=7,
    )
    ghoul_id = next(c["id"] for c in start["combatants"] if c["kind"] == "monster")
    yield {
        "conn": conn,
        "cfg": cfg,
        "session_id": session_id,
        "ghoul_id": ghoul_id,
        "combat_attack": combat_attack,
        "combat_status": combat_status,
    }
    conn.close()


def test_wrong_turn_rejected(combat_ctx):
    ctx = combat_ctx
    status = ctx["combat_status"](ctx["conn"], ctx["session_id"])
    turn_id = status["turn_id"]
    wrong = "sammy" if turn_id != "sammy" else ctx["ghoul_id"]
    result = ctx["combat_attack"](
        ctx["conn"],
        ctx["session_id"],
        wrong,
        ctx["ghoul_id"] if wrong == "sammy" else "sammy",
        content_root=ctx["cfg"].content_root,
        campaign_slug="test",
        enforce_turn=True,
    )
    if turn_id == "sammy":
        assert result["ok"] is False
        assert "not your turn" in result.get("error", "")
    else:
        assert result["ok"] is False


def test_resolve_pc_action_runs_monster_turns(combat_ctx):
    from tomb_gm.services.simulation.combat import combat_status, resolve_pc_action_and_advance

    ctx = combat_ctx
    status = combat_status(ctx["conn"], ctx["session_id"])
    if status.get("turn_kind") != "pc":
        pytest.skip("seed did not put PC first — skip chain test")

    result = resolve_pc_action_and_advance(
        ctx["conn"],
        ctx["session_id"],
        action="ATTACK",
        actor_id="sammy",
        target_id=ctx["ghoul_id"],
        content_root=ctx["cfg"].content_root,
        campaign_slug="test",
        seed=50,
    )
    assert result["ok"] is True
    actions = [m.get("action") for m in result.get("mechanical") or []]
    assert "combat_attack" in actions or any(
        m.get("hit") is not None for m in result.get("mechanical") or []
    )
