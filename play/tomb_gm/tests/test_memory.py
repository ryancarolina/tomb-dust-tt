from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PLAY = Path(__file__).resolve().parents[3] / "play"


def _seed_campaign_session(run_tomb_gm, test_config, test_db) -> tuple[str, str]:
    slug = f"mem-test-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    test_db.execute(
        "INSERT OR IGNORE INTO campaigns (slug, display_name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (slug, "Memory Test", now, now),
    )
    test_db.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, slug, now, "exploration"),
    )
    test_db.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "exploration"),
    )
    test_db.commit()
    test_config.active_path.write_text(
        json.dumps({"campaign_slug": slug, "session_id": session_id}),
        encoding="utf-8",
    )
    return slug, session_id


def test_remember_recall_recap_compact(run_tomb_gm, test_config, test_db):
    run_tomb_gm("init")
    slug, session_id = _seed_campaign_session(run_tomb_gm, test_config, test_db)

    remembered = run_tomb_gm(
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

    from tomb_gm.db.connection import connect
    from tomb_gm.services.memory import episodic

    conn = connect(test_config.db_path)
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

    recalled = run_tomb_gm("memory", "recall", "--query", "aldric knight spared", "--top", "3")
    assert recalled["ok"] is True
    assert recalled["results"]
    assert any("Aldric" in r["fact"] for r in recalled["results"])

    recap = run_tomb_gm("memory", "recap")
    assert recap["ok"] is True
    assert "Aldric" in recap["recap_text"]
    assert recap["memories"]
    assert recap["session_id"] == session_id

    compacted = run_tomb_gm("memory", "compact")
    assert compacted["ok"] is True
    assert compacted["summary_id"] >= 1
    assert "Recent events" in compacted["text"]
    assert "travel" in compacted["text"].lower() or "Moved" in compacted["text"]

    recap_after = run_tomb_gm("memory", "recap")
    assert recap_after["scene_summaries"]
    assert session_id in recap_after["scene_summaries"][0].get("session_id", session_id) or recap_after[
        "scene_summaries"
    ][0]["text"]


def test_recall_requires_campaign(run_tomb_gm, test_config, isolated_workspace):
    import os

    run_tomb_gm("init")
    if test_config.active_path.exists():
        test_config.active_path.unlink()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tomb_gm",
            "--workspace",
            str(isolated_workspace),
            "memory",
            "recall",
            "--query",
            "test",
        ],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    out = json.loads(proc.stdout or proc.stderr)
    assert out["ok"] is False
