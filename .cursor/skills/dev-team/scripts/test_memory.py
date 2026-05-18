"""Tests for dev-team memory store."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

from dev_team.memory_store import MemoryStore, PROJECT_SCOPE, _age_bucket  # noqa: E402


class MemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.memory = MemoryStore(self.workspace)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_add_and_recall(self) -> None:
        self.memory.add(
            kind="convention",
            phase="research",
            title="Use npm test",
            lesson="Run npm test not pytest in this repo",
            tags=["tooling"],
        )
        lessons = self.memory.recall(phase="research", query="npm test", limit=3)
        self.assertGreaterEqual(len(lessons), 1)
        self.assertEqual(lessons[0].title, "Use npm test")
        self.assertIsNotNone(lessons[0].last_recalled_at)

    def test_draft_from_feedback(self) -> None:
        fb = """## QA spec review

### Verdict
Fail

### Blockers
- B-1: AC-2 is not testable
- B-2: Missing Out scope
"""
        drafted = self.memory.draft_from_feedback("spec", fb, session_id="sess-1")
        self.assertEqual(len(drafted), 2)
        self.assertEqual(drafted[0].status, "draft")

    def test_age_bucket(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        self.assertEqual(_age_bucket(now), "new")
        self.assertEqual(_age_bucket(old), "old")

    def test_project_scope(self) -> None:
        stats = self.memory.stats()
        self.assertEqual(stats["project_scope"], PROJECT_SCOPE)

    def test_deprecate(self) -> None:
        lesson = self.memory.add(
            kind="bug",
            phase="dev",
            title="Stale tip",
            lesson="No longer applies",
        )
        self.memory.deprecate(lesson.id)
        active = self.memory.list_lessons(status="active")
        self.assertFalse(any(l.id == lesson.id for l in active))


if __name__ == "__main__":
    unittest.main()
