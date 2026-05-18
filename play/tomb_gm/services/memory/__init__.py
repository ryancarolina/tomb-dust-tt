from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from tomb_gm.services.memory import episodic, semantic


def remember_fact(
    conn: sqlite3.Connection,
    campaign_slug: str,
    fact: str,
    *,
    entities: list[str] | None = None,
    address: str | None = None,
    importance: int = 3,
    session_id: str | None = None,
) -> int:
    memory_id = semantic.remember(
        conn,
        campaign_slug,
        fact,
        entities=entities,
        address=address,
        importance=importance,
    )
    if session_id:
        episodic.append_event(
            conn,
            session_id,
            "memory.remember",
            {"memory_id": memory_id, "fact": fact},
        )
    return memory_id


def recall_facts(
    conn: sqlite3.Connection,
    campaign_slug: str,
    query: str,
    *,
    top: int = 5,
) -> list[dict[str, Any]]:
    return semantic.recall(conn, campaign_slug, query, top=top)


def build_recap(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    session_id: str | None,
    party: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summaries = []
    if session_id:
        rows = conn.execute(
            "SELECT id, text, created_at FROM scene_summaries "
            "WHERE session_id = ? ORDER BY created_at DESC LIMIT 3",
            (session_id,),
        ).fetchall()
        summaries = [{"id": r["id"], "text": r["text"], "created_at": r["created_at"]} for r in rows]
    elif campaign_slug:
        rows = conn.execute(
            "SELECT ss.id, ss.text, ss.created_at, ss.session_id "
            "FROM scene_summaries ss "
            "JOIN sessions s ON s.id = ss.session_id "
            "WHERE s.campaign_slug = ? "
            "ORDER BY ss.created_at DESC LIMIT 3",
            (campaign_slug,),
        ).fetchall()
        summaries = [
            {"id": r["id"], "text": r["text"], "created_at": r["created_at"], "session_id": r["session_id"]}
            for r in rows
        ]

    recent_events: list[dict[str, Any]] = []
    if session_id:
        recent_events = list(reversed(episodic.list_events(conn, session_id, limit=10)))

    memories = semantic.open_memories(conn, campaign_slug, limit=15)
    lines = []
    if summaries:
        lines.append(summaries[0]["text"])
    for mem in memories[:8]:
        lines.append(f"- {mem['fact']}")
    if party:
        addr = party.get("address")
        phase = party.get("phase")
        if addr or phase:
            lines.append(f"Party at {addr or '?'} (phase: {phase or '?'})")

    return {
        "campaign_slug": campaign_slug,
        "session_id": session_id,
        "scene_summaries": summaries,
        "memories": memories,
        "recent_events": recent_events,
        "recap_text": "\n".join(lines) if lines else "No prior memory for this campaign.",
    }


def compact_session(
    conn: sqlite3.Connection,
    session_id: str,
    campaign_slug: str,
    *,
    event_limit: int = 30,
) -> dict[str, Any]:
    events = list(reversed(episodic.list_events(conn, session_id, limit=event_limit)))
    memories = semantic.open_memories(conn, campaign_slug, limit=5)
    lines = [f"Session {session_id} — scene summary", ""]
    if events:
        lines.append("Recent events:")
        for ev in events[-20:]:
            lines.append(f"  - {episodic.format_event_line(ev)}")
    else:
        lines.append("No episodic events recorded this session.")
    if memories:
        lines.append("")
        lines.append("Pinned facts:")
        for mem in memories:
            lines.append(f"  - {mem['fact']}")
    text = "\n".join(lines)
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO scene_summaries (session_id, text, created_at) VALUES (?, ?, ?)",
        (session_id, text, now),
    )
    conn.execute(
        "UPDATE sessions SET summary_id = ? WHERE id = ?",
        (int(cur.lastrowid), session_id),
    )
    episodic.append_event(
        conn,
        session_id,
        "memory.compact",
        {"summary_id": int(cur.lastrowid), "event_count": len(events)},
    )
    conn.commit()
    return {"summary_id": int(cur.lastrowid), "text": text, "event_count": len(events)}
