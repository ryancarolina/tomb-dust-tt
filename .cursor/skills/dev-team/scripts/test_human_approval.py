"""Tests for chat-based human gate acknowledgments."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

from dev_team.human_approval import parse_user_prompt, process_user_prompt  # noqa: E402
from dev_team.machine import DevTeamMachine  # noqa: E402
from dev_team.session import Session, SessionStore  # noqa: E402


class HumanApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.store = SessionStore(self.workspace)
        self.machine = DevTeamMachine(self.store)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parse_approve_spec(self) -> None:
        session = Session(state="SPEC_GATE", pending_human_gate="spec")
        intent = parse_user_prompt("approve spec", session)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.action, "approve")
        self.assertEqual(intent.phase, "spec")

    def test_parse_lgtm_at_gate(self) -> None:
        session = Session(state="RESEARCH_GATE", pending_human_gate="research")
        intent = parse_user_prompt("lgtm", session)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.phase, "research")

    def test_process_user_prompt_records_ack(self) -> None:
        self.store.begin_work("t")
        session = Session(
            state="SPEC_GATE",
            work_slug=self.store.work.slug if self.store.work else "",
            pending_human_gate="spec",
        )
        session.save(self.store.session_path)
        result = process_user_prompt(self.store, "approve spec")
        self.assertTrue(result["recorded"])
        ack_path = self.store.work.path / "gate-acks.jsonl"
        self.assertTrue(ack_path.exists())


if __name__ == "__main__":
    unittest.main()
