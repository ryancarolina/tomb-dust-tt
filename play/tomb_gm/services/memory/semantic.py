from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any


def remember(
    conn: sqlite3.Connection,
    campaign_slug: str,
    fact: str,
    *,
    entities: list[str] | None = None,
    address: str | None = None,
    importance: int = 3,
    source_event_id: int | None = None,
    embed: bool = True,
) -> int:
    importance = max(1, min(5, importance))
    entities_json = json.dumps(entities or [])
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO memories (campaign_slug, fact, entities_json, address, importance, "
        "source_event_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (campaign_slug, fact, entities_json, address, importance, source_event_id, now),
    )
    memory_id = int(cur.lastrowid)
    if embed:
        _upsert_embedding(conn, memory_id, fact)
    conn.commit()
    return memory_id


def recall(
    conn: sqlite3.Connection,
    campaign_slug: str,
    query: str,
    *,
    top: int = 5,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, fact, entities_json, address, importance, created_at, last_recalled_at "
        "FROM memories WHERE campaign_slug = ? AND superseded_by IS NULL",
        (campaign_slug,),
    ).fetchall()
    scored: list[tuple[float, sqlite3.Row]] = []
    for row in rows:
        entities = json.loads(row["entities_json"] or "[]")
        score = _score_memory(query, row["fact"], entities, row["importance"], row["created_at"])
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    results: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for score, row in scored[:top]:
        if score <= 0 and query.strip():
            continue
        conn.execute(
            "UPDATE memories SET last_recalled_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        results.append(
            {
                "id": row["id"],
                "fact": row["fact"],
                "entities": json.loads(row["entities_json"] or "[]"),
                "address": row["address"],
                "importance": row["importance"],
                "score": round(score, 2),
                "created_at": row["created_at"],
            }
        )
    if results:
        conn.commit()
    return results


def open_memories(
    conn: sqlite3.Connection,
    campaign_slug: str,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, fact, entities_json, address, importance, created_at "
        "FROM memories WHERE campaign_slug = ? AND superseded_by IS NULL "
        "ORDER BY importance DESC, created_at DESC LIMIT ?",
        (campaign_slug, limit),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "fact": r["fact"],
            "entities": json.loads(r["entities_json"] or "[]"),
            "address": r["address"],
            "importance": r["importance"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def _score_memory(
    query: str,
    fact: str,
    entities: list[str],
    importance: int,
    created_at: str,
) -> float:
    q = query.strip().lower()
    if not q:
        return float(importance * 2 + _recency_decay(created_at))
    return (
        importance * 2
        + _recency_decay(created_at)
        + _keyword_match(q, fact.lower())
        + _entity_overlap(q, entities)
    )


def _recency_decay(created_at: str) -> float:
    try:
        ts = created_at.replace("Z", "+00:00")
        created = datetime.fromisoformat(ts)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    age_days = (datetime.now(timezone.utc) - created).total_seconds() / 86400.0
    return max(0.0, 5.0 - age_days * 0.25)


def _keyword_match(query: str, fact: str) -> float:
    q_tokens = {t for t in re.split(r"\W+", query) if len(t) > 1}
    f_tokens = {t for t in re.split(r"\W+", fact) if len(t) > 1}
    if not q_tokens:
        return 0.0
    overlap = len(q_tokens & f_tokens)
    return float(overlap * 2)


def _entity_overlap(query: str, entities: list[str]) -> float:
    score = 0.0
    for entity in entities:
        e = entity.strip().lower()
        if not e:
            continue
        if e in query or query in e:
            score += 3.0
        elif any(tok in e or e in tok for tok in re.split(r"\W+", query) if len(tok) > 1):
            score += 1.5
    return score


def _upsert_embedding(conn: sqlite3.Connection, memory_id: int, fact: str) -> None:
    vector = _simple_embed(fact)
    conn.execute(
        "INSERT OR REPLACE INTO memory_embeddings (memory_id, vector_blob) VALUES (?, ?)",
        (memory_id, vector),
    )


def _simple_embed(text: str) -> bytes:
    tokens = [t for t in re.split(r"\W+", text.lower()) if len(t) > 2]
    counts: dict[str, int] = {}
    for tok in tokens:
        counts[tok] = counts.get(tok, 0) + 1
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    payload = {k: v / norm for k, v in counts.items()}
    return json.dumps(payload).encode("utf-8")
