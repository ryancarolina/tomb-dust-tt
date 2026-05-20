"""setup_new_game session lifecycle (APP-014): T-014a–c.

Run with: pytest -k "setup_new_game or session_lifecycle"
"""

from __future__ import annotations

import json

from gm.creation import CreationState


def count_open_sessions(conn) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE ended_at IS NULL"
    ).fetchone()
    return int(row["n"])


def count_corpses(conn) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM world_corpses").fetchone()
    return int(row["n"])


def _ensure_salt_road_campaign(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))


def test_setup_new_game_from_mid_creation(orchestrator, bridge):
    """T-014a: mid-creation reset returns NAME with a single active session."""
    _ensure_salt_road_campaign(bridge)
    start = bridge.session_start("salt-road")
    assert start.get("ok")

    orchestrator.creation = CreationState(active=True, step="SKILLS", name="Test")

    result = orchestrator.setup_new_game()

    assert result.get("ok")
    assert orchestrator.creation.active is True
    assert orchestrator.creation.step == "NAME"
    assert orchestrator.creation.name == ""

    status = bridge.status()
    assert status.get("active") is not None
    assert status["active"]["session_id"] == "current"

    conn = bridge.ctx.conn
    assert count_open_sessions(conn) <= 1
    assert count_open_sessions(conn) == 1


def test_setup_new_game_closes_prior_session(orchestrator, bridge, isolated_workspace):
    """T-014b: prior session is closed or wiped; new current session at NAME."""
    _ensure_salt_road_campaign(bridge)
    start = bridge.session_start("salt-road")
    assert start.get("ok")
    prior_session_id = start["session_id"]

    active_path = bridge.ctx.config.local_dir / "active.json"
    assert active_path.is_file()
    prior_active = json.loads(active_path.read_text(encoding="utf-8"))
    assert prior_active.get("session_id") == prior_session_id

    conn = bridge.ctx.conn
    prior_row = conn.execute(
        "SELECT id, ended_at FROM sessions WHERE id = ?", (prior_session_id,)
    ).fetchone()
    assert prior_row is not None
    assert prior_row["ended_at"] is None

    result = orchestrator.setup_new_game()

    assert result.get("ok")
    assert orchestrator.creation.step == "NAME"

    after_prior = conn.execute(
        "SELECT id, ended_at FROM sessions WHERE id = ? AND ended_at IS NOT NULL",
        (prior_session_id,),
    ).fetchone()
    current_row = conn.execute(
        "SELECT id, ended_at FROM sessions WHERE id = 'current'"
    ).fetchone()

    assert current_row is not None
    assert current_row["ended_at"] is None
    assert after_prior is not None or current_row["id"] == "current"
    assert count_open_sessions(conn) == 1

    status = bridge.status()
    assert status["active"]["session_id"] == "current"


def test_setup_new_game_preserves_corpses(orchestrator, bridge):
    """T-014c: world_corpses survive setup_new_game wipe."""
    _ensure_salt_road_campaign(bridge)
    start = bridge.session_start("salt-road")
    assert start.get("ok")

    created = bridge.character_create(name="Test Delver", background="novice", gold_gp=100)
    assert created.get("ok"), created.get("error")
    char_id = created["id"]

    death = bridge.process_delver_death(char_id, cause="test death")
    assert death.get("ok"), death.get("error")

    conn = bridge.ctx.conn
    corpses_before = count_corpses(conn)
    assert corpses_before >= 1

    result = orchestrator.setup_new_game()

    assert result.get("ok")
    assert count_corpses(conn) == corpses_before
