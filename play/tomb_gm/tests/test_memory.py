from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
WORKSPACE = PLAY / "workspace"


def _run(*args: str) -> dict:
    import os

    proc = subprocess.run(
        [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE), *args],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout)


def _seed_campaign_session() -> tuple[str, str]:
    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations

    cfg = load_config(WORKSPACE)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    slug = f"mem-test-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO campaigns (slug, display_name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (slug, "Memory Test", now, now),
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, slug, now, "exploration"),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "exploration"),
    )
    conn.commit()
    cfg.active_path.write_text(
        json.dumps({"campaign_slug": slug, "session_id": session_id}),
        encoding="utf-8",
    )
    conn.close()
    return slug, session_id


def test_remember_recall_recap_compact():
    _run("init")
    slug, session_id = _seed_campaign_session()

    remembered = _run(
        "memory",
        "remember",
        "--fact",
        "The party spared Sir Aldric at the ossuary gate.",
        "--entities",
        "aldric",
        "32-C-UG-1",
        "--importance",
        "5",
    )
    assert remembered["ok"] is True
    assert remembered["memory_id"] >= 1
    assert remembered["campaign_slug"] == slug

    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect
    from tomb_gm.services.memory import episodic

    cfg = load_config(WORKSPACE)
    conn = connect(cfg.db_path)
    episodic.append_event(
        conn,
        session_id,
        "travel",
        {"summary": "Moved to 32-C-UG-1"},
    )
    episodic.append_event(
        conn,
        session_id,
        "npc.deal",
        {"summary": "Marshal sold a registry stamp"},
    )
    conn.close()

    recalled = _run("memory", "recall", "--query", "aldric knight spared", "--top", "3")
    assert recalled["ok"] is True
    assert recalled["results"]
    assert any("Aldric" in r["fact"] for r in recalled["results"])

    recap = _run("memory", "recap")
    assert recap["ok"] is True
    assert "Aldric" in recap["recap_text"]
    assert recap["memories"]
    assert recap["session_id"] == session_id

    compacted = _run("memory", "compact")
    assert compacted["ok"] is True
    assert compacted["summary_id"] >= 1
    assert "Recent events" in compacted["text"]
    assert "travel" in compacted["text"].lower() or "Moved" in compacted["text"]

    recap_after = _run("memory", "recap")
    assert recap_after["scene_summaries"]
    assert session_id in recap_after["scene_summaries"][0].get("session_id", session_id) or recap_after[
        "scene_summaries"
    ][0]["text"]


def test_recall_requires_campaign():
    _run("init")
    from tomb_gm.config import load_config

    cfg = load_config(WORKSPACE)
    if cfg.active_path.exists():
        cfg.active_path.unlink()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tomb_gm",
            "--workspace",
            str(WORKSPACE),
            "memory",
            "recall",
            "--query",
            "test",
        ],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=__import__("os").environ,
    )
    out = json.loads(proc.stdout or proc.stderr)
    assert out["ok"] is False
