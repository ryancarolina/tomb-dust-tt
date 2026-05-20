from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PLAY = Path(__file__).resolve().parents[3] / "play"


def _seed_session(test_config, test_db, session_id: str = "test-session-ws6") -> None:
    now = datetime.now(timezone.utc).isoformat()
    test_db.execute(
        "INSERT OR IGNORE INTO campaigns (slug, display_name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        ("test-campaign", "Test", now, now),
    )
    test_db.execute(
        "INSERT OR REPLACE INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, "test-campaign", now, "delve"),
    )
    test_db.execute(
        "INSERT OR REPLACE INTO party_state (session_id, address, mode, phase) "
        "VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "delve"),
    )
    test_db.commit()
    test_config.active_path.write_text(
        json.dumps({"session_id": session_id, "campaign_slug": "test-campaign"}),
        encoding="utf-8",
    )


def test_bridge_skill_bonus():
    from tomb_gm.rules.bridge import skill_bonus

    assert skill_bonus(3) == 1
    assert skill_bonus(10) == 4


def test_roll_d20_seeded(run_tomb_gm):
    run_tomb_gm("init")
    out = run_tomb_gm("roll", "d20", "--mod", "5", "--dc", "13", "--reason", "test", seed=42)
    assert out["ok"] is True
    assert out["natural"] == 4
    assert out["total"] == 9
    assert out["success"] is False
    assert out["roll_id"].startswith("evt-")


def test_roll_d20_logs_event(run_tomb_gm, test_db):
    run_tomb_gm("init")
    out = run_tomb_gm("roll", "d20", "--mod", "0", "--dc", "10", seed=1)
    evt_id = int(out["roll_id"].split("-", 1)[1])
    row = test_db.execute("SELECT type, payload_json FROM events WHERE id = ?", (evt_id,)).fetchone()
    assert row is not None
    assert row["type"] == "roll"
    payload = json.loads(row["payload_json"])
    assert payload["kind"] == "d20"
    assert payload["natural"] == out["natural"]


def test_roll_attack_vs_ghoul_ac(run_tomb_gm):
    run_tomb_gm("init")
    out = run_tomb_gm(
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


def test_combat_start_status_end(run_tomb_gm, test_config, test_db):
    run_tomb_gm("init")
    _seed_session(test_config, test_db)
    start = run_tomb_gm("combat", "start", "--monsters", "grave-ghoul:1", seed=7)
    assert start["ok"] is True
    assert len(start["combatants"]) == 1
    ghoul = start["combatants"][0]
    assert ghoul["monsterId"] == "grave-ghoul"
    assert ghoul["hp"] == 28
    assert ghoul["ac"] == 13

    status = run_tomb_gm("combat", "status")
    assert status["ok"] is True
    assert status["round"] == 1
    assert len(status["combatants"]) == 1

    ended = run_tomb_gm("combat", "end")
    assert ended["ok"] is True

    after = run_tomb_gm("combat", "status", expect_ok=False)
    assert after["ok"] is False


def test_combat_unknown_monster(run_tomb_gm, test_config, test_db, isolated_workspace):
    import os

    run_tomb_gm("init")
    _seed_session(test_config, test_db)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tomb_gm",
            "--workspace",
            str(isolated_workspace),
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
