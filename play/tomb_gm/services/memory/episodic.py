from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


def append_event(
    conn: sqlite3.Connection,
    session_id: str | None,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    beat_id: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO events (session_id, beat_id, ts, type, payload_json) VALUES (?, ?, ?, ?, ?)",
        (
            session_id,
            beat_id,
            datetime.now(timezone.utc).isoformat(),
            event_type,
            json.dumps(payload or {}),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_events(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    limit: int = 50,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    if event_type:
        rows = conn.execute(
            "SELECT id, session_id, beat_id, ts, type, payload_json "
            "FROM events WHERE session_id = ? AND type = ? "
            "ORDER BY ts DESC LIMIT ?",
            (session_id, event_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, session_id, beat_id, ts, type, payload_json "
            "FROM events WHERE session_id = ? "
            "ORDER BY ts DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [_row_to_event(r) for r in rows]


def format_event_line(event: dict[str, Any]) -> str:
    payload = event.get("payload") or {}
    detail = payload.get("summary") or payload.get("message") or payload.get("fact")
    if not detail and payload:
        detail = json.dumps(payload, ensure_ascii=False)
    if detail:
        return f"[{event['type']}] {detail}"
    return f"[{event['type']}]"


def _row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "beat_id": row["beat_id"],
        "ts": row["ts"],
        "type": row["type"],
        "payload": json.loads(row["payload_json"] or "{}"),
    }
