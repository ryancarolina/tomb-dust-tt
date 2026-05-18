"""Human gates for high-impact table decisions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

GATE_TYPES = frozenset(
    {"EXTRACT_COMMIT", "DEATH", "PROMOTION", "STAMP_PURCHASE"}
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_gate(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    gate_type: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if gate_type not in GATE_TYPES:
        raise ValueError(f"Unknown gate type: {gate_type}")
    gate_id = f"gate-{uuid.uuid4().hex[:12]}"
    conn.execute(
        "INSERT INTO gates (id, session_id, gate_type, payload_json, resolved_at, resolution) "
        "VALUES (?, ?, ?, ?, NULL, NULL)",
        (gate_id, session_id, gate_type, json.dumps(payload or {})),
    )
    conn.commit()
    return {"gate_id": gate_id, "gate_type": gate_type, "payload": payload or {}}


def resolve_gate(
    conn: sqlite3.Connection,
    *,
    gate_id: str,
    approve: bool,
) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM gates WHERE id = ?", (gate_id,)).fetchone()
    if not row:
        raise ValueError(f"Gate not found: {gate_id}")
    if row["resolved_at"]:
        return {
            "ok": False,
            "error": "already_resolved",
            "gate_id": gate_id,
            "resolution": row["resolution"],
        }
    resolution = "approved" if approve else "rejected"
    conn.execute(
        "UPDATE gates SET resolved_at = ?, resolution = ? WHERE id = ?",
        (_now(), resolution, gate_id),
    )
    conn.commit()
    return {
        "ok": True,
        "gate_id": gate_id,
        "gate_type": row["gate_type"],
        "resolution": resolution,
        "payload": json.loads(row["payload_json"] or "{}"),
    }


def pending_gate(conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM gates WHERE session_id = ? AND resolved_at IS NULL "
        "ORDER BY rowid DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "gate_id": row["id"],
        "gate_type": row["gate_type"],
        "payload": json.loads(row["payload_json"] or "{}"),
    }
