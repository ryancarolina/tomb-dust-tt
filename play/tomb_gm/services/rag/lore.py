"""Search lore-oriented markdown under build/systems/."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from tomb_gm.services.rag.index import chunk_markdown, is_indexed
from tomb_gm.services.rag.search import _escape_like, _excerpt, _query_terms, ensure_index

LORE_PREFIXES = (
    "systems/locations/",
    "systems/lore/",
    "systems/factions/",
    "systems/npcs/",
    "systems/world/",
)


def index_lore(conn: sqlite3.Connection, content_root: Path) -> dict:
    root = content_root / "systems"
    if not root.is_dir():
        raise FileNotFoundError(f"systems directory not found: {root}")
    conn.execute("DELETE FROM rules_fts WHERE path LIKE 'systems/locations/%' OR path LIKE 'systems/lore/%' "
                 "OR path LIKE 'systems/factions/%' OR path LIKE 'systems/npcs/%' OR path LIKE 'systems/world/%'")
    files = 0
    chunks = 0
    for md_path in sorted(root.rglob("*.md")):
        rel = md_path.relative_to(content_root).as_posix()
        if not any(rel.startswith(p) for p in LORE_PREFIXES):
            continue
        text = md_path.read_text(encoding="utf-8")
        for heading, chunk in chunk_markdown(text):
            conn.execute(
                "INSERT INTO rules_fts (path, heading, chunk) VALUES (?, ?, ?)",
                (rel, heading or None, chunk),
            )
            chunks += 1
        files += 1
    conn.commit()
    return {"files": files, "chunks": chunks}


def search_lore(
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
    prefix_clause = " OR ".join("path LIKE ?" for _ in LORE_PREFIXES)
    prefix_params = [p + "%" for p in LORE_PREFIXES]
    where = f"({prefix_clause}) AND " + " AND ".join("chunk LIKE ? ESCAPE '\\'" for _ in terms)
    params = prefix_params + [f"%{_escape_like(t)}%" for t in terms]
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
        {"path": row["path"], "heading": row["heading"], "excerpt": _excerpt(row["chunk"], query)}
        for row in rows
    ]
