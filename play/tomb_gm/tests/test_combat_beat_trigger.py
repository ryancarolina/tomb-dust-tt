"""Beat returns combat_trigger instead of starting combat directly."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"


def test_beat_emits_combat_trigger_not_start(command_ctx, tmp_path):
    import os

    from tomb_gm.services.beat import process_beat

    ctx = command_ctx
    now = datetime.now(timezone.utc).isoformat()
    session_id = "beat-test"
    ctx.conn.execute(
        "INSERT INTO campaigns (slug, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("test", "Test", now, now),
    )
    ctx.conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, "test", now, "delve"),
    )
    ctx.conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C-UG-1", "dungeon", "delve"),
    )
    ctx.conn.commit()
    rel = Path(os.path.relpath(BUILD, ctx.config.workspace))
    (ctx.config.workspace / "config.yaml").write_text(
        f"content_root: {rel.as_posix()}\n", encoding="utf-8"
    )
    from tomb_gm.domain import session as session_domain

    active_path = ctx.config.local_dir / "active.json"
    active_path.write_text(
        '{"campaign_slug":"test","session_id":"beat-test"}',
        encoding="utf-8",
    )

    result = process_beat(
        ctx,
        {
            "lines": [{"slot": 1, "raw": "I taunt the grave-ghoul to attack me!"}],
            "auto_combat": True,
        },
    )
    assert result.get("ok") is True
    summary = result.get("mechanical_summary") or []
    assert any(item.get("action") == "combat_trigger" for item in summary)
    assert not any(item.get("action") == "combat_start" for item in summary)
    row = ctx.conn.execute(
        "SELECT active FROM combat_state WHERE session_id = ?", (session_id,)
    ).fetchone()
    assert row is None or row["active"] == 0
