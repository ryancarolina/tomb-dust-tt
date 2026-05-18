"""Project-local SQLite memory for dev-team lessons (ttTomb-Dust only)."""

from __future__ import annotations

import re
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_SCOPE = "ttTomb-Dust"
MEMORY_DB_NAME = "memory.db"

# Lessons newer than this many days rank as "new"; older decay in recall ranking.
DECAY_HALF_LIFE_DAYS = 30
NEW_LESSON_DAYS = 7


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _age_bucket(created_at: str) -> str:
    days = (datetime.now(timezone.utc) - _parse_ts(created_at)).days
    if days <= NEW_LESSON_DAYS:
        return "new"
    if days <= DECAY_HALF_LIFE_DAYS:
        return "recent"
    return "old"


def _recency_score(created_at: str, last_recalled_at: str | None) -> float:
    """0–1 score; newer lessons and recently useful ones rank higher."""
    now = datetime.now(timezone.utc)
    created = _parse_ts(created_at)
    days_old = max(0, (now - created).days)
    created_score = 0.5 ** (days_old / DECAY_HALF_LIFE_DAYS)
    if last_recalled_at:
        recalled = _parse_ts(last_recalled_at)
        recall_days = max(0, (now - recalled).days)
        recall_score = 0.5 ** (recall_days / DECAY_HALF_LIFE_DAYS)
        return min(1.0, created_score * 0.6 + recall_score * 0.4)
    return created_score


@dataclass
class Lesson:
    id: int
    created_at: str
    updated_at: str
    last_recalled_at: str | None
    kind: str
    phase: str
    title: str
    lesson: str
    context: str
    source: str
    status: str
    hit_count: int
    session_id: str
    work_slug: str
    age_bucket: str
    tags: list[str]
    paths: list[str]


class MemoryStore:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.db_path = self.workspace / ".dev-team" / MEMORY_DB_NAME
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_recalled_at TEXT,
                    kind TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    title TEXT NOT NULL,
                    lesson TEXT NOT NULL,
                    context TEXT DEFAULT '',
                    source TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    hit_count INTEGER NOT NULL DEFAULT 1,
                    session_id TEXT DEFAULT '',
                    project_scope TEXT NOT NULL DEFAULT 'ttTomb-Dust',
                    work_slug TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS lesson_tags (
                    lesson_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (lesson_id, tag),
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS lesson_paths (
                    lesson_id INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    PRIMARY KEY (lesson_id, path),
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                );

                INSERT OR IGNORE INTO meta (key, value) VALUES ('project_scope', 'ttTomb-Dust');
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS lessons_fts USING fts5(
                    title, lesson, context,
                    content='lessons',
                    content_rowid='id'
                )
                """
            )
            cols = {r[1] for r in conn.execute("PRAGMA table_info(lessons)").fetchall()}
            if "work_slug" not in cols:
                conn.execute("ALTER TABLE lessons ADD COLUMN work_slug TEXT DEFAULT ''")
            conn.commit()
            self._rebuild_fts(conn)
        finally:
            conn.close()

    def _rebuild_fts(self, conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM lessons_fts")
        rows = conn.execute(
            "SELECT id, title, lesson, context FROM lessons WHERE status = 'active'"
        ).fetchall()
        for row in rows:
            conn.execute(
                "INSERT INTO lessons_fts(rowid, title, lesson, context) VALUES (?, ?, ?, ?)",
                (row["id"], row["title"], row["lesson"], row["context"]),
            )

    def _row_to_lesson(self, row: sqlite3.Row, conn: sqlite3.Connection) -> Lesson:
        tags = [
            r["tag"]
            for r in conn.execute(
                "SELECT tag FROM lesson_tags WHERE lesson_id = ?", (row["id"],)
            )
        ]
        paths = [
            r["path"]
            for r in conn.execute(
                "SELECT path FROM lesson_paths WHERE lesson_id = ?", (row["id"],)
            )
        ]
        return Lesson(
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_recalled_at=row["last_recalled_at"],
            kind=row["kind"],
            phase=row["phase"],
            title=row["title"],
            lesson=row["lesson"],
            context=row["context"] or "",
            source=row["source"] or "",
            status=row["status"],
            hit_count=row["hit_count"],
            session_id=row["session_id"] or "",
            work_slug=(row["work_slug"] if "work_slug" in row.keys() else "") or "",
            age_bucket=_age_bucket(row["created_at"]),
            tags=tags,
            paths=paths,
        )

    def add(
        self,
        *,
        kind: str,
        phase: str,
        title: str,
        lesson: str,
        context: str = "",
        source: str = "",
        status: str = "active",
        session_id: str = "",
        work_slug: str = "",
        tags: list[str] | None = None,
        paths: list[str] | None = None,
    ) -> Lesson:
        now = _utc_now()
        tags = tags or []
        paths = paths or []
        conn = self._connect()
        try:
            existing = conn.execute(
                """
                SELECT id FROM lessons
                WHERE status = 'active' AND lower(title) = lower(?)
                """,
                (title.strip(),),
            ).fetchone()
            if existing:
                lesson_id = existing["id"]
                conn.execute(
                    """
                    UPDATE lessons SET
                        updated_at = ?, lesson = ?, context = ?, source = ?,
                        hit_count = hit_count + 1, session_id = ?, work_slug = ?
                    WHERE id = ?
                    """,
                    (now, lesson, context, source, session_id, work_slug, lesson_id),
                )
                conn.execute("DELETE FROM lessons_fts WHERE rowid = ?", (lesson_id,))
                conn.execute(
                    "INSERT INTO lessons_fts(rowid, title, lesson, context) VALUES (?, ?, ?, ?)",
                    (lesson_id, title, lesson, context),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO lessons (
                        created_at, updated_at, kind, phase, title, lesson,
                        context, source, status, session_id, project_scope, work_slug
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now,
                        now,
                        kind,
                        phase,
                        title.strip(),
                        lesson,
                        context,
                        source,
                        status,
                        session_id,
                        PROJECT_SCOPE,
                        work_slug,
                    ),
                )
                lesson_id = cur.lastrowid

            for tag in tags:
                conn.execute(
                    "INSERT OR IGNORE INTO lesson_tags (lesson_id, tag) VALUES (?, ?)",
                    (lesson_id, tag.lower().strip()),
                )
            for path in paths:
                conn.execute(
                    "INSERT OR IGNORE INTO lesson_paths (lesson_id, path) VALUES (?, ?)",
                    (lesson_id, path.strip()),
                )
            conn.execute(
                "INSERT INTO lessons_fts(rowid, title, lesson, context) VALUES (?, ?, ?, ?)",
                (lesson_id, title, lesson, context),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
            return self._row_to_lesson(row, conn)
        finally:
            conn.close()

    def draft_from_feedback(
        self,
        target: str,
        feedback_content: str,
        *,
        session_id: str = "",
        work_slug: str = "",
    ) -> list[Lesson]:
        """Create draft lessons from QA feedback blockers (B-1, B-2, …)."""
        target = target.lower()
        phase = "spec" if target == "spec" else "dev"
        kind = "spec" if target == "spec" else "bug"
        blockers = re.findall(
            r"(?im)^-\s*(?:\[\s*\]\s*)?(B-\d+)\s*:\s*(.+)$",
            feedback_content,
        )
        if not blockers:
            blockers = [("B-1", line.strip()) for line in feedback_content.splitlines() if line.strip().startswith("- ")][:5]

        created: list[Lesson] = []
        for bid, text in blockers:
            title = f"{target} QA {bid}: {text[:60]}".strip()
            created.append(
                self.add(
                    kind=kind,
                    phase=phase,
                    title=title,
                    lesson=text.strip(),
                    context=f"From qa-{target}-feedback.md ({bid})",
                    source=f"qa-{target}-feedback",
                    status="draft",
                    session_id=session_id,
                    work_slug=work_slug,
                    tags=[target, "qa-reject", bid.lower()],
                )
            )
        return created

    def recall(
        self,
        *,
        phase: str | None = None,
        query: str = "",
        tags: list[str] | None = None,
        limit: int = 5,
        since: str | None = None,
    ) -> list[Lesson]:
        """Return ranked lessons; updates last_recalled_at."""
        tags = tags or []
        limit = max(1, min(limit, 20))
        conn = self._connect()
        try:
            candidates: list[tuple[int, float]] = []

            if query.strip():
                tokens = re.findall(r"\w+", query, re.UNICODE)
                fts_q = " OR ".join(tokens[:12]) if tokens else '""'
                fts_rows = conn.execute(
                    """
                    SELECT rowid, bm25(lessons_fts) AS rank
                    FROM lessons_fts
                    WHERE lessons_fts MATCH ?
                    ORDER BY rank
                    LIMIT 50
                    """,
                    (fts_q,),
                ).fetchall()
                for row in fts_rows:
                    candidates.append((row["rowid"], -row["rank"]))

            sql = "SELECT * FROM lessons WHERE status IN ('active', 'draft') AND project_scope = ?"
            params: list[Any] = [PROJECT_SCOPE]
            if phase:
                sql += " AND (phase = ? OR phase = 'general')"
                params.append(phase.lower())
            if since:
                sql += " AND created_at >= ?"
                params.append(since)
            rows = conn.execute(sql, params).fetchall()

            scored: dict[int, tuple[sqlite3.Row, float]] = {}
            for row in rows:
                lid = row["id"]
                text_score = next((s for i, s in candidates if i == lid), 0.1)
                recency = _recency_score(row["created_at"], row["last_recalled_at"])
                hit_boost = min(0.3, row["hit_count"] * 0.05)
                score = text_score * 0.4 + recency * 0.5 + hit_boost
                if tags:
                    row_tags = {
                        t["tag"]
                        for t in conn.execute(
                            "SELECT tag FROM lesson_tags WHERE lesson_id = ?", (lid,)
                        )
                    }
                    if row_tags.intersection({t.lower() for t in tags}):
                        score += 0.25
                scored[lid] = (row, score)

            if not query.strip() and rows:
                for row in rows:
                    lid = row["id"]
                    if lid not in scored:
                        scored[lid] = (
                            row,
                            _recency_score(row["created_at"], row["last_recalled_at"]),
                        )

            ranked = sorted(scored.values(), key=lambda x: x[1], reverse=True)[:limit]
            now = _utc_now()
            lessons: list[Lesson] = []
            for row, _ in ranked:
                conn.execute(
                    "UPDATE lessons SET last_recalled_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
            conn.commit()
            for row, _ in ranked:
                fresh = conn.execute("SELECT * FROM lessons WHERE id = ?", (row["id"],)).fetchone()
                lessons.append(self._row_to_lesson(fresh, conn))
            return lessons
        finally:
            conn.close()

    def promote(self, lesson_id: int) -> Lesson | None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE lessons SET status = 'active', updated_at = ? WHERE id = ?",
                (_utc_now(), lesson_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
            return self._row_to_lesson(row, conn) if row else None
        finally:
            conn.close()

    def deprecate(self, lesson_id: int) -> Lesson | None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE lessons SET status = 'deprecated', updated_at = ? WHERE id = ?",
                (_utc_now(), lesson_id),
            )
            conn.execute("DELETE FROM lessons_fts WHERE rowid = ?", (lesson_id,))
            conn.commit()
            row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
            return self._row_to_lesson(row, conn) if row else None
        finally:
            conn.close()

    def list_lessons(
        self,
        *,
        status: str | None = None,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[Lesson]:
        conn = self._connect()
        try:
            sql = "SELECT * FROM lessons WHERE project_scope = ?"
            params: list[Any] = [PROJECT_SCOPE]
            if status:
                sql += " AND status = ?"
                params.append(status)
            if kind:
                sql += " AND kind = ?"
                params.append(kind)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_lesson(r, conn) for r in rows]
        finally:
            conn.close()

    def stats(self) -> dict:
        conn = self._connect()
        try:
            total = conn.execute(
                "SELECT COUNT(*) FROM lessons WHERE project_scope = ?", (PROJECT_SCOPE,)
            ).fetchone()[0]
            by_status = {
                r["status"]: r["n"]
                for r in conn.execute(
                    """
                    SELECT status, COUNT(*) AS n FROM lessons
                    WHERE project_scope = ? GROUP BY status
                    """,
                    (PROJECT_SCOPE,),
                )
            }
            by_age = {"new": 0, "recent": 0, "old": 0}
            for row in conn.execute(
                "SELECT created_at FROM lessons WHERE project_scope = ? AND status != 'deprecated'",
                (PROJECT_SCOPE,),
            ):
                by_age[_age_bucket(row["created_at"])] += 1
            return {
                "db_path": str(self.db_path),
                "project_scope": PROJECT_SCOPE,
                "total": total,
                "by_status": by_status,
                "by_age_bucket": by_age,
            }
        finally:
            conn.close()

    def lesson_to_dict(self, lesson: Lesson) -> dict:
        d = asdict(lesson)
        return d
