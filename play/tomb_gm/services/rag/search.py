from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from tomb_gm.services.rag.index import index_rules, is_indexed

_TERM = re.compile(r"\S+")


def ensure_index(conn: sqlite3.Connection, content_root: Path) -> None:
    if not is_indexed(conn):
        index_rules(conn, content_root)


def _query_terms(query: str) -> list[str]:
    return [t for t in _TERM.findall(query) if t]


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _excerpt(chunk: str, query: str, max_len: int = 400) -> str:
    terms = [t.lower() for t in _query_terms(query)]
    lower = chunk.lower()
    pos = 0
    for term in terms:
        idx = lower.find(term)
        if idx >= 0:
            pos = idx
            break
    start = max(0, pos - 80)
    text = chunk[start : start + max_len].replace("\n", " ")
    if start > 0:
        text = "..." + text
    if start + max_len < len(chunk):
        text = text + "..."
    return text


def search_rules(
    conn: sqlite3.Connection,
    content_root: Path,
    query: str,
    *,
    max_results: int = 5,
) -> list[dict]:
    ensure_index(conn, content_root)
    terms = _query_terms(query)
    if not terms:
        return []

    where = " AND ".join("chunk LIKE ? ESCAPE '\\'" for _ in terms)
    params = [f"%{_escape_like(t)}%" for t in terms]
    phrase_pat = f"%{_escape_like(query.strip())}%"
    params.extend([phrase_pat, phrase_pat, max_results])

    rows = conn.execute(
        f"SELECT path, heading, chunk FROM rules_fts WHERE {where} "
        "ORDER BY "
        "CASE WHEN chunk LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END, "
        "CASE WHEN heading LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END, "
        "path, heading LIMIT ?",
        params,
    ).fetchall()

    return [
        {
            "path": row["path"],
            "heading": row["heading"],
            "excerpt": _excerpt(row["chunk"], query),
        }
        for row in rows
    ]
