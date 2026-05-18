"""Tests for dev-team state machine."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import patch

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

from dev_team.human_approval import ParsedIntent, record_intent  # noqa: E402
from dev_team.human_gate import HUMAN_ACK_ENV  # noqa: E402
from dev_team.machine import DevTeamMachine, TransitionError  # noqa: E402
from dev_team.session import MAX_QA_LOOPS, SessionStore  # noqa: E402
from dev_team.validators import validate_research, validate_spec, validate_task_scope  # noqa: E402

TASK_SCOPE_OK = (
    "Add a CSV export button on the admin reports page so admins can download report data."
)

RESEARCH_OK = """## Research brief

### Request
Add CSV export to the reports page for admin users.

### Findings
- `src/reports/ReportTable.tsx` renders the grid.
- `src/api/reports.ts` exposes GET /reports.

### Risks & unknowns
- Large exports may timeout — consider pagination.

### Recommendation
Proceed with a streaming CSV endpoint.
"""

SPEC_OK = """## Product spec

### Problem
Admins need to export report data.

### Scope
**In:** CSV download on reports page.
**Out:** PDF export, scheduled exports.

### Acceptance criteria
- [ ] AC-1: Admin sees Export CSV button on /reports.
- [ ] AC-2: Downloaded file opens in Excel with correct headers.

### Priority
**Must:** AC-1, AC-2 | **Should:** — | **Could:** —

### Approach
Add export button in `src/reports/ReportTable.tsx` and GET /reports/export in API.

### Implementation allowlist
- src/reports/**
- src/api/reports.ts
"""

QA_SPEC_FAIL = """## QA spec review

### Verdict
Fail

### Blockers
- B-1: AC-2 lacks measurable header column definition.

### Standards checklist
| Standard | Status | Notes |
|----------|--------|-------|
| Testable ACs | Fail | AC-2 vague |
"""

QA_DEV_FAIL = """## QA dev review

### Verdict
Fail

### Blockers
- B-1: Export button not visible to admin role.

### Spec mismatches
- AC-1: Button missing from ReportTable for admin users.
"""

DEV_OK = """## Dev handoff

### Changes
- `src/reports/ReportTable.tsx` — added Export CSV button
- `src/api/reports.ts` — added export endpoint

### AC mapping
| AC | How implemented |
|----|-----------------|
| AC-1 | Button in ReportTable |
| AC-2 | CSV headers match grid columns |

### Verify
Run `npm test` and click Export on /reports as admin.

### Known gaps
None.
"""

QA_OK = """## QA report

### Summary
Pass with notes

### Acceptance criteria
| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | Pass | Button visible in UI |
| AC-2 | Pass | CSV opens in Excel |

### Issues
| Severity | Issue | Action taken |
|----------|-------|--------------|

### Regression & edge cases
- Login flow unchanged.
- Empty report returns headers-only CSV.
"""


class StateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.store = SessionStore(self.workspace)
        self.machine = DevTeamMachine(self.store)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @contextmanager
    def _human_operator(self):
        with patch.dict(os.environ, {HUMAN_ACK_ENV: "1"}, clear=False):
            yield

    def _scope_and_start(self, mode: str = "full", text: str = TASK_SCOPE_OK, name: str = "test") -> None:
        self.machine.scope_begin(name)
        self.machine.scope_propose(text)
        time.sleep(0.02)  # ack must be strictly after scope_proposed_at
        self._chat_ack("scope_confirm")
        self.machine.scope_confirm()
        self.machine.start(mode)

    def _chat_ack(self, action: str, *, phase: str = "", target: str = "") -> None:
        session = self.machine.session
        intent = ParsedIntent(action, phase=phase, target=target)
        record_intent(self.store, session, intent)

    def _human_approve(self, phase: str) -> None:
        self._chat_ack("approve", phase=phase)
        self.machine.approve(phase)

    def _through_spec_qa(self) -> None:
        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        self.machine.qa_pass("spec")

    def _through_dev_qa(self) -> None:
        self.store.write_artifact("dev-handoff.md", DEV_OK)
        self.machine.record_checks("pytest: 10 passed")
        self.machine.submit()
        self.machine.qa_pass("dev")

    def test_task_scope_validation(self) -> None:
        bad = validate_task_scope("Too short.")
        self.assertFalse(bad.ok)
        good = validate_task_scope(TASK_SCOPE_OK)
        self.assertTrue(good.ok)

    def test_work_directory_layout(self) -> None:
        self.machine.scope_begin("combat")
        work = self.store.work
        self.assertIsNotNone(work)
        assert work is not None
        self.assertIn("combat-", work.slug)
        self.assertTrue((work.artifacts_dir).is_dir())
        self.assertTrue((work.logs_dir / "events.jsonl").exists() or (work.logs_dir).is_dir())

    def test_start_requires_scope_confirm(self) -> None:
        self.machine.scope_begin("test")
        self.machine.scope_propose(TASK_SCOPE_OK)
        with self.assertRaises(TransitionError):
            self.machine.start("full")

    def test_scope_confirm_blocked_without_chat_ack(self) -> None:
        self.machine.scope_begin("test")
        self.machine.scope_propose(TASK_SCOPE_OK)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(HUMAN_ACK_ENV, None)
            with self.assertRaises(TransitionError) as ctx:
                self.machine.scope_confirm()
        self.assertIn("approval in chat", str(ctx.exception).lower())

    def test_approve_blocked_without_chat_ack(self) -> None:
        self._scope_and_start("skip-research")
        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        self.machine.qa_pass("spec")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(HUMAN_ACK_ENV, None)
            with self.assertRaises(TransitionError) as ctx:
                self.machine.approve("spec")
        self.assertIn("approval in chat", str(ctx.exception).lower())
        self.assertEqual(self.machine.session.state, "SPEC_GATE")

    def test_approve_works_after_chat_ack(self) -> None:
        self._scope_and_start("skip-research")
        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        self.machine.qa_pass("spec")
        self._chat_ack("approve", phase="spec")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(HUMAN_ACK_ENV, None)
            self.machine.approve("spec")
        self.assertEqual(self.machine.session.state, "DEV")

    def test_full_happy_path(self) -> None:
        self._scope_and_start("full")
        self.store.write_artifact("research.md", RESEARCH_OK)
        self.machine.submit()
        self._human_approve("research")

        self._through_spec_qa()
        self.assertEqual(self.machine.session.state, "SPEC_GATE")
        self._human_approve("spec")

        self._through_dev_qa()
        self.assertEqual(self.machine.session.state, "DEV_GATE")
        self._human_approve("dev")

        self.store.write_artifact("qa-report.md", QA_OK)
        self.machine.submit()
        self._human_approve("qa")
        self.assertEqual(self.machine.session.state, "DONE")

    def test_spec_qa_reject_loop(self) -> None:
        self._scope_and_start("skip-research")
        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        self.assertEqual(self.machine.session.state, "QA_SPEC_REVIEW")

        self.store.write_artifact(SessionStore.ARTIFACT_SPEC_FEEDBACK, QA_SPEC_FAIL)
        self.machine.qa_reject("spec")
        self.assertEqual(self.machine.session.state, "SPEC")
        self.assertTrue(self.store.artifact_path(SessionStore.ARTIFACT_SPEC_FEEDBACK).exists())

        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        self.machine.qa_pass("spec")
        self.assertEqual(self.machine.session.state, "SPEC_GATE")

    def test_spec_qa_loop_limit(self) -> None:
        self._scope_and_start("skip-research")
        for _ in range(MAX_QA_LOOPS):
            self.store.write_artifact("spec.md", SPEC_OK)
            self.machine.submit()
            self.store.write_artifact(SessionStore.ARTIFACT_SPEC_FEEDBACK, QA_SPEC_FAIL)
            self.machine.qa_reject("spec")

        self.store.write_artifact("spec.md", SPEC_OK)
        with self.assertRaises(TransitionError):
            self.machine.submit()

    def test_cannot_skip_gate(self) -> None:
        self._scope_and_start("full")
        self.store.write_artifact("research.md", RESEARCH_OK)
        self.machine.submit()
        with self._human_operator():
            with self.assertRaises(TransitionError):
                self.machine.approve("spec")

    def test_cannot_human_approve_spec_without_qa_pass(self) -> None:
        self._scope_and_start("skip-research")
        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        with self._human_operator():
            with self.assertRaises(TransitionError):
                self.machine.approve("spec")

    def test_invalid_research_rejected(self) -> None:
        result = validate_research("## Research brief\n\n### Request\nHi\n")
        self.assertFalse(result.ok)

    def test_spec_requires_research_approval_in_full_mode(self) -> None:
        result = validate_spec(SPEC_OK, research_approved=False, mode="full")
        self.assertFalse(result.ok)

    def test_reject_invalidates_artifacts(self) -> None:
        self._scope_and_start("full")
        self.store.write_artifact("research.md", RESEARCH_OK)
        self.machine.submit()
        self._human_approve("research")
        self._through_spec_qa()
        self._chat_ack("reject", target="research")
        self.machine.reject("research")
        self.assertFalse(self.store.artifact_path("spec.md").exists())
        self.assertEqual(self.machine.session.state, "RESEARCH")

    def test_scope_begin_requires_name(self) -> None:
        with self.assertRaises(TransitionError):
            self.machine.scope_begin("")

    def test_submit_blocked_without_artifact(self) -> None:
        self._scope_and_start("skip-research")
        with self.assertRaises(TransitionError):
            self.machine.submit()

    def test_submit_blocked_tiny_artifact(self) -> None:
        self._scope_and_start("skip-research")
        self.store.write_artifact("spec.md", "too small")
        with self.assertRaises(TransitionError):
            self.machine.submit()

    def test_legacy_session_blocks_transitions(self) -> None:
        legacy = self.workspace / ".dev-team" / "session.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text('{"state": "SPEC_GATE", "session_id": "bad"}', encoding="utf-8")
        with self.assertRaises(TransitionError):
            self.machine.scope_begin("x")

    def test_check_reports_blockers_at_gate(self) -> None:
        self._scope_and_start("skip-research")
        self.store.write_artifact("spec.md", SPEC_OK)
        self.machine.submit()
        self.machine.qa_pass("spec")
        self.store.artifact_path("spec.md").unlink()
        report = self.machine.check()
        self.assertFalse(report["ok"])
        self.assertTrue(report["blocked"])

    def test_spec_without_allowlist_fails_validation(self) -> None:
        self._scope_and_start("skip-research")
        spec_no_list = SPEC_OK.replace(
            "### Implementation allowlist\n- src/reports/**\n- src/api/reports.ts\n", ""
        )
        self.store.write_artifact("spec.md", spec_no_list)
        result = validate_spec(spec_no_list, research_approved=True, mode="skip-research")
        self.assertFalse(result.ok)
        self.assertTrue(any("allowlist" in e.lower() for e in result.errors))

    def test_submit_spec_requires_allowlist(self) -> None:
        self._scope_and_start("skip-research")
        spec_no_list = SPEC_OK.replace(
            "### Implementation allowlist\n- src/reports/**\n- src/api/reports.ts\n", ""
        )
        self.store.write_artifact("spec.md", spec_no_list)
        with self.assertRaises(TransitionError) as ctx:
            self.machine.submit()
        self.assertIn("validation failed", str(ctx.exception).lower())

    def test_approve_clears_pending_human_gate(self) -> None:
        self._scope_and_start("skip-research")
        self._through_spec_qa()
        self.assertEqual(self.machine.session.pending_human_gate, "spec")
        self._human_approve("spec")
        self.assertEqual(self.machine.session.state, "DEV")
        self.assertEqual(self.machine.session.pending_human_gate, "")

    def test_suggest_at_gate_stops(self) -> None:
        self._scope_and_start("skip-research")
        self._through_spec_qa()
        suggestion = self.machine.suggest()
        self.assertTrue(suggestion["stop"])
        self.assertEqual(suggestion["state"], "SPEC_GATE")

    def test_reset_clears_legacy(self) -> None:
        legacy = self.workspace / ".dev-team" / "session.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text('{"state": "SPEC_GATE"}', encoding="utf-8")
        removed = self.machine.reset()
        self.assertTrue(any("session.json" in r for r in removed))
        self.machine.scope_begin("fresh")

    def test_implementation_lock_in_check(self) -> None:
        self._scope_and_start("skip-research")
        st = self.machine.status()
        self.assertTrue(st["implementation_lock"])

    def test_log_clear_and_works_remove(self) -> None:
        self.machine.scope_begin("logtest")
        slug = self.store.work.slug
        self.store.log("test_event", detail="hello")
        self.assertTrue((self.store.work.logs_dir / "audit.log").exists())
        self.store.clear_logs()
        self.assertFalse((self.store.work.logs_dir / "audit.log").exists())
        self.store.remove_work(slug)
        self.assertFalse((self.workspace / ".dev-team" / "works" / slug).exists())

    def test_cli_status_json(self) -> None:
        import dev_team_cli

        w = str(self.workspace)
        buf = io.StringIO()
        with redirect_stdout(buf):
            dev_team_cli.main(["--workspace", w, "scope", "begin", "--name", "cli"])
            dev_team_cli.main(["--workspace", w, "scope", "propose", "--text", TASK_SCOPE_OK])
            from dev_team.human_approval import process_user_prompt

            time.sleep(0.02)
            process_user_prompt(SessionStore(Path(w)), "confirm scope")
            dev_team_cli.main(["--workspace", w, "scope", "confirm"])
            dev_team_cli.main(["--workspace", w, "start", "--mode", "full"])
            rc = dev_team_cli.main(["--workspace", w, "status"])
        self.assertEqual(rc, 0)
        active = json.loads((self.workspace / ".dev-team" / "active.json").read_text())
        session_path = self.workspace / ".dev-team" / active["path"] / "session.json"
        data = json.loads(session_path.read_text())
        self.assertEqual(data["state"], "RESEARCH")
        self.assertEqual(data["task"], TASK_SCOPE_OK)


if __name__ == "__main__":
    unittest.main()
