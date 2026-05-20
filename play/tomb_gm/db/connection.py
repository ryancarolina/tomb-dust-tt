from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def schema_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    """Add a column to a table only if it doesn't already exist."""
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    col_names = [c[1] for c in cols]
    if column not in col_names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def run_migrations(conn: sqlite3.Connection) -> int:
    current = schema_version(conn)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for path in migration_files:
        # Extract version from filename (e.g. 001_initial.sql → 1)
        try:
            file_version = int(path.stem.split("_")[0])
        except (ValueError, IndexError):
            file_version = 0

        if file_version <= current and current > 0:
            continue

        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)

    # Clean up any duplicate schema_version rows from past bugs
    try:
        conn.execute("DELETE FROM schema_version WHERE version < (SELECT MAX(version) FROM schema_version)")
    except Exception:
        pass

    # Post-SQL migrations: add columns safely (ALTER TABLE has no IF NOT EXISTS in SQLite)
    _add_column_if_missing(conn, "party_state", "scene_index", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "party_state", "scene_max", "INTEGER NOT NULL DEFAULT 3")
    _add_column_if_missing(conn, "party_state", "heading", "TEXT NOT NULL DEFAULT 'N'")
    _add_column_if_missing(conn, "party_state", "dungeon_room_id", "TEXT")

    conn.commit()
    return schema_version(conn)
