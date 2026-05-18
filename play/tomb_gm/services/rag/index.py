from __future__ import annotations

import sqlite3
from pathlib import Path


def systems_root(content_root: Path) -> Path:
    return content_root / "systems"


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    """Split markdown into chunks at ## headings (heading, body)."""
    sections: list[tuple[str, str]] = []
    heading = ""
    body: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if heading or body:
                chunk = "\n".join(body).strip()
                if chunk:
                    sections.append((heading, chunk))
            heading = line[3:].strip()
            body = []
        else:
            body.append(line)

    chunk = "\n".join(body).strip()
    if chunk:
        sections.append((heading, chunk))

    return sections


def index_rules(conn: sqlite3.Connection, content_root: Path) -> dict:
    root = systems_root(content_root)
    if not root.is_dir():
        raise FileNotFoundError(f"systems directory not found: {root}")

    conn.execute("DELETE FROM rules_fts")
    files = 0
    chunks = 0

    for md_path in sorted(root.rglob("*.md")):
        rel = md_path.relative_to(content_root).as_posix()
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


def is_indexed(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT COUNT(*) AS n FROM rules_fts").fetchone()
    return int(row["n"]) > 0
