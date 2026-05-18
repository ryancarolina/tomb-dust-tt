"""Tests for shell hook human-only CLI blocking."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

from dev_team.human_approval import ParsedIntent, record_intent  # noqa: E402
from dev_team.human_gate import HUMAN_ACK_ENV, shell_gate_deny_reason  # noqa: E402
from dev_team.machine import DevTeamMachine  # noqa: E402
from dev_team.session import Session, SessionStore  # noqa: E402


class ShellGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.store = SessionStore(self.workspace)
        self.machine = DevTeamMachine(self.store)
        os.environ.pop(HUMAN_ACK_ENV, None)

    def tearDown(self) -> None:
        self._tmp.cleanup()
        os.environ.pop(HUMAN_ACK_ENV, None)

    def test_deny_approve_spec_without_chat_ack(self) -> None:
        self.machine.scope_begin("t")
        session = Session(state="SPEC_GATE", pending_human_gate="spec", work_slug=self.store.work.slug)
        session.save(self.store.session_path)

        cmd = "python .cursor/skills/dev-team/scripts/dev_team_cli.py --workspace . approve spec"
        deny = shell_gate_deny_reason(self.store, cmd)
        self.assertIsNotNone(deny)
        self.assertIn("chat ack", deny.lower())

    def test_allow_approve_with_ack(self) -> None:
        self.machine.scope_begin("t")
        session = Session(state="SPEC_GATE", pending_human_gate="spec", work_slug=self.store.work.slug)
        session.save(self.store.session_path)
        record_intent(self.store, session, ParsedIntent("approve", phase="spec"))

        cmd = "python .cursor/skills/dev-team/scripts/dev_team_cli.py approve spec"
        deny = shell_gate_deny_reason(self.store, cmd)
        self.assertIsNone(deny)

    def test_human_ack_env_bypasses_shell_gate(self) -> None:
        self.machine.scope_begin("t")
        session = Session(state="SPEC_GATE", pending_human_gate="spec", work_slug=self.store.work.slug)
        session.save(self.store.session_path)
        os.environ[HUMAN_ACK_ENV] = "1"
        cmd = "python .cursor/skills/dev-team/scripts/dev_team_cli.py approve spec"
        self.assertIsNone(shell_gate_deny_reason(self.store, cmd))


if __name__ == "__main__":
    unittest.main()
