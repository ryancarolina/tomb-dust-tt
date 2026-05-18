from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
WORKSPACE = PLAY / "workspace"


def _run(*args: str, seed: int | None = None) -> dict:
    import os

    cmd = [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE)]
    if seed is not None:
        cmd.extend(["--seed", str(seed)])
    cmd.extend(args)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout)


def _run_json(*args: str, seed: int | None = None) -> dict:
    import os

    cmd = [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE)]
    if seed is not None:
        cmd.extend(["--seed", str(seed)])
    cmd.extend(args)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    return json.loads(proc.stdout or proc.stderr)


def _db() -> sqlite3.Connection:
    from tomb_gm.config import load_config

    cfg = load_config(WORKSPACE)
    conn = sqlite3.connect(cfg.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_session(session_id: str = "test-session-ws6") -> None:
    from tomb_gm.config import load_config

    cfg = load_config(WORKSPACE)
    now = datetime.now(timezone.utc).isoformat()
    conn = _db()
    conn.execute(
        "INSERT OR IGNORE INTO campaigns (slug, display_name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        ("test-campaign", "Test", now, now),
    )
    conn.execute(
        "INSERT OR REPLACE INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, "test-campaign", now, "delve"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO party_state (session_id, address, mode, phase) "
        "VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "delve"),
    )
    conn.commit()
    cfg.active_path.write_text(
        json.dumps({"session_id": session_id, "campaign_slug": "test-campaign"}),
        encoding="utf-8",
    )
    conn.close()


def test_bridge_skill_bonus():
    from tomb_gm.rules.bridge import skill_bonus

    assert skill_bonus(3) == 1
    assert skill_bonus(10) == 4


def test_roll_d20_seeded():
    _run("init")
    out = _run("roll", "d20", "--mod", "5", "--dc", "13", "--reason", "test", seed=42)
    assert out["ok"] is True
    assert out["natural"] == 4
    assert out["total"] == 9
    assert out["success"] is False
    assert out["roll_id"].startswith("evt-")


def test_roll_d20_logs_event():
    _run("init")
    out = _run("roll", "d20", "--mod", "0", "--dc", "10", seed=1)
    evt_id = int(out["roll_id"].split("-", 1)[1])
    conn = _db()
    row = conn.execute("SELECT type, payload_json FROM events WHERE id = ?", (evt_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row["type"] == "roll"
    payload = json.loads(row["payload_json"])
    assert payload["kind"] == "d20"
    assert payload["natural"] == out["natural"]


def test_roll_attack_vs_ghoul_ac():
    _run("init")
    out = _run(
        "roll",
        "attack",
        "--ability-mod",
        "2",
        "--pb",
        "2",
        "--skill-level",
        "3",
        "--target-ac",
        "13",
        "--weapon",
        "1d8",
        "--ability-damage-mod",
        "2",
        "--natural",
        "17",
        seed=0,
    )
    assert out["ok"] is True
    assert out["hit"] is True
    assert out["critical"] is True
    assert out["damage"] == 17


def test_combat_start_status_end():
    from tomb_gm.config import load_config

    _run("init")
    _seed_session()
    cfg = load_config(WORKSPACE)
    try:
        _combat_start_status_end(cfg)
    finally:
        cfg.active_path.unlink(missing_ok=True)


def _combat_start_status_end(cfg) -> None:
    start = _run("combat", "start", "--monsters", "grave-ghoul:1", seed=7)
    assert start["ok"] is True
    assert len(start["combatants"]) == 1
    ghoul = start["combatants"][0]
    assert ghoul["monsterId"] == "grave-ghoul"
    assert ghoul["hp"] == 28
    assert ghoul["ac"] == 13

    status = _run("combat", "status")
    assert status["ok"] is True
    assert status["round"] == 1
    assert len(status["combatants"]) == 1

    ended = _run("combat", "end")
    assert ended["ok"] is True

    after = _run_json("combat", "status")
    assert after["ok"] is False


def test_combat_unknown_monster():
    from tomb_gm.config import load_config

    _run("init")
    _seed_session()
    cfg = load_config(WORKSPACE)
    try:
        import os

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "tomb_gm",
                "--workspace",
                str(WORKSPACE),
                "combat",
                "start",
                "--monsters",
                "not-a-real-monster:1",
            ],
            capture_output=True,
            text=True,
            cwd=str(PLAY),
            env=os.environ,
        )
        assert proc.returncode != 0
    finally:
        cfg.active_path.unlink(missing_ok=True)


def test_resolve_attack_walkthrough():
    import random

    from tomb_gm.rules.bridge import resolve_attack

    rng = random.Random(0)
    result, damage = resolve_attack(
        ability_mod=2,
        pb=2,
        skill_bonus_value=1,
        target_ac=13,
        weapon_damage="1d8",
        ability_damage_mod=2,
        rng=rng,
        natural=17,
    )
    assert result.total == 22
    assert result.critical
    assert damage == 17
