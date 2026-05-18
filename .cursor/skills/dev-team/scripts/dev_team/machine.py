"""Dev-team state machine with enforced transitions and phase validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from dev_team import human_gate
from dev_team.guards import (
    artifact_requirements_met,
    gate_artifacts_ready,
    implementation_locked,
    legacy_session_present,
    record_artifact_hash,
    run_check,
    verify_artifact_hash,
)
from dev_team.allowlist import parse_implementation_allowlist
from dev_team.human_approval import HumanGateError, find_ack
from dev_team.session import MAX_QA_LOOPS, Session, SessionStore, _utc_now
from dev_team.validators import (
    ValidationResult,
    validate_dev_handoff,
    validate_dev_vs_spec,
    validate_qa_dev_feedback,
    validate_qa_report,
    validate_qa_spec_feedback,
    validate_research,
    validate_spec,
    validate_spec_for_qa_review,
    validate_task_scope,
)


class State(str, Enum):
    IDLE = "IDLE"
    TASK_SCOPING = "TASK_SCOPING"
    RESEARCH = "RESEARCH"
    RESEARCH_GATE = "RESEARCH_GATE"
    SPEC = "SPEC"
    QA_SPEC_REVIEW = "QA_SPEC_REVIEW"
    SPEC_GATE = "SPEC_GATE"
    DEV = "DEV"
    QA_DEV_REVIEW = "QA_DEV_REVIEW"
    DEV_GATE = "DEV_GATE"
    QA = "QA"
    QA_GATE = "QA_GATE"
    DONE = "DONE"
    ABORTED = "ABORTED"


WORK_STATES = {State.RESEARCH, State.SPEC, State.DEV, State.QA}
GATE_STATES = {State.RESEARCH_GATE, State.SPEC_GATE, State.DEV_GATE, State.QA_GATE}
QA_REVIEW_STATES = {State.QA_SPEC_REVIEW, State.QA_DEV_REVIEW}

ARTIFACT_BY_STATE = {
    State.RESEARCH: "research.md",
    State.SPEC: "spec.md",
    State.DEV: "dev-handoff.md",
    State.QA: "qa-report.md",
}

PHASE_FOR_GATE = {
    State.RESEARCH_GATE: "research",
    State.SPEC_GATE: "spec",
    State.DEV_GATE: "dev",
    State.QA_GATE: "qa",
}

NEXT_AFTER_APPROVE = {
    State.RESEARCH_GATE: State.SPEC,
    State.SPEC_GATE: State.DEV,
    State.DEV_GATE: State.QA,
    State.QA_GATE: State.DONE,
}


class TransitionError(Exception):
    def __init__(self, message: str, validation: ValidationResult | None = None) -> None:
        super().__init__(message)
        self.validation = validation


class DevTeamMachine:
    def __init__(self, store: SessionStore) -> None:
        self.store = store

    @property
    def session(self) -> Session:
        return self.store.load()

    def _state(self) -> State:
        try:
            return State(self.session.state)
        except ValueError as exc:
            raise TransitionError(f"Unknown session state: {self.session.state!r}") from exc

    def _require_human(
        self,
        command: str,
        *,
        action: str,
        phase: str = "",
        target: str = "",
    ) -> None:
        try:
            human_gate.require_human_operator(
                self.store,
                command,
                action=action,
                phase=phase,
                target=target,
            )
        except HumanGateError as exc:
            raise TransitionError(str(exc)) from exc

    def _set_state(self, session: Session, new_state: State, event: str) -> Session:
        old = session.state
        session.record_transition(old, new_state.value, event)
        session.state = new_state.value
        if new_state.value in human_gate.GATE_STATE_TO_PHASE:
            session.pending_human_gate = human_gate.GATE_STATE_TO_PHASE[new_state.value]
        elif old in human_gate.GATE_STATE_TO_PHASE:
            session.pending_human_gate = ""
        self.store.log(
            "state_transition",
            detail=f"{old} → {new_state.value}",
            extra={"from": old, "to": new_state.value, "event": event},
        )
        self.store.save(session)
        return session

    def _bump_qa_cycle(self, session: Session, kind: str) -> None:
        if kind == "spec":
            session.spec_qa_cycle += 1
            if session.spec_qa_cycle > MAX_QA_LOOPS:
                raise TransitionError(
                    f"QA↔PM loop limit reached ({MAX_QA_LOOPS} cycles). "
                    "Escalate to human at SPEC_GATE (revise) or abort."
                )
        elif kind == "dev":
            session.dev_qa_cycle += 1
            if session.dev_qa_cycle > MAX_QA_LOOPS:
                raise TransitionError(
                    f"QA↔Dev loop limit reached ({MAX_QA_LOOPS} cycles). "
                    "Escalate to human at DEV_GATE (revise) or abort."
                )

    def _ensure_no_legacy(self) -> None:
        if legacy_session_present(self.store):
            raise TransitionError(
                "Legacy .dev-team/session.json detected without active work. "
                "Run: reset (or migrate) before any transition."
            )

    def check(self) -> dict:
        report = run_check(self.store, self.session)
        return report.to_dict()

    def _ensure_not_blocked(self) -> None:
        report = run_check(self.store, self.session)
        if report.blocked:
            raise TransitionError(
                "Session is blocked. Fix blockers before continuing: "
                + "; ".join(report.blockers)
            )

    def assert_gate(self, phase: str) -> None:
        self._ensure_no_legacy()
        phase = phase.lower()
        gate_by_phase = {
            "research": State.RESEARCH_GATE,
            "spec": State.SPEC_GATE,
            "dev": State.DEV_GATE,
            "qa": State.QA_GATE,
        }
        if phase not in gate_by_phase:
            raise TransitionError(f"Unknown gate phase {phase!r}.")
        expected = gate_by_phase[phase]
        st = self._state()
        if st != expected:
            raise TransitionError(
                f"assert-gate {phase} requires {expected.value}, currently {st.value}."
            )
        result = gate_artifacts_ready(self.store, st.value)
        if not result.ok:
            raise TransitionError(f"Gate {phase} blocked: artifacts not ready.", result)
        report = run_check(self.store, self.session)
        if not report.ok:
            raise TransitionError(
                "Gate blocked: " + "; ".join(report.blockers),
            )

    def reset(self) -> list[str]:
        return self.store.purge_legacy()

    def verify_path(self, rel_path: str) -> dict:
        from dev_team.guards import assert_repo_edit_allowed

        path = self.store.project_root / rel_path
        allowed, reason = assert_repo_edit_allowed(
            self.store.project_root,
            path,
            self.session,
            self.store,
        )
        return {
            "allowed": allowed,
            "reason": reason,
            "state": self.session.state,
            "implementation_lock": implementation_locked(self.session.state),
            "allowlist": self.session.implementation_allowlist,
        }

    def status(self) -> dict:
        s = self.session
        st = self._state()
        check_report = run_check(self.store, s)
        artifacts = {
            "research.md": self.store.read_artifact("research.md") is not None,
            "spec.md": self.store.read_artifact("spec.md") is not None,
            SessionStore.ARTIFACT_SPEC_FEEDBACK: self.store.read_artifact(
                SessionStore.ARTIFACT_SPEC_FEEDBACK
            )
            is not None,
            "dev-handoff.md": self.store.read_artifact("dev-handoff.md") is not None,
            SessionStore.ARTIFACT_DEV_FEEDBACK: self.store.read_artifact(
                SessionStore.ARTIFACT_DEV_FEEDBACK
            )
            is not None,
            "qa-report.md": self.store.read_artifact("qa-report.md") is not None,
        }
        work = self.store.work
        return {
            "state": st.value,
            "work_slug": work.slug if work else s.work_slug,
            "work_dir": str(work.path.relative_to(self.store.project_root)) if work else "",
            "session_id": s.session_id,
            "task_scope": s.task_scope,
            "task_scope_confirmed": s.task_scope_confirmed,
            "task": s.task,
            "mode": s.mode,
            "qa_loops": {
                "spec": {"cycle": s.spec_qa_cycle, "max": MAX_QA_LOOPS, "remaining": max(0, MAX_QA_LOOPS - s.spec_qa_cycle)},
                "dev": {"cycle": s.dev_qa_cycle, "max": MAX_QA_LOOPS, "remaining": max(0, MAX_QA_LOOPS - s.dev_qa_cycle)},
            },
            "approvals": {
                "research": s.research_approved,
                "spec_qa": s.spec_qa_passed,
                "spec_human": s.spec_approved,
                "dev_qa": s.dev_qa_passed,
                "dev_human": s.dev_approved,
                "qa_human": s.qa_approved,
            },
            "artifacts": artifacts,
            "artifacts_ok": check_report.artifacts_ok,
            "blocked": check_report.blocked,
            "blockers": check_report.blockers,
            "implementation_lock": check_report.implementation_lock,
            "implementation_allowlist": s.implementation_allowlist,
            "human_gate_pending": s.pending_human_gate,
            "human_gate_enforced": True,
            "human_operator_required": (
                "Reply in chat with approve <phase>, lgtm, revise <phase>: …, or reject to <target>. "
                "Then the orchestrator runs the matching CLI command."
            ),
            "checks_run": s.checks_run,
            "awaiting": self._awaiting_message(st),
        }

    def _awaiting_message(self, st: State) -> str:
        s = self.session
        if st in GATE_STATES:
            phase = PHASE_FOR_GATE[st]
            return f"Human approval required. Use: approve {phase}"
        if st == State.QA_SPEC_REVIEW:
            return "QA: review spec; then qa-pass spec OR write qa-spec-feedback.md + qa-reject spec"
        if st == State.QA_DEV_REVIEW:
            return "QA: verify vs spec; then qa-pass dev OR write qa-dev-feedback.md + qa-reject dev"
        if st in WORK_STATES:
            if st == State.SPEC and self.store.read_artifact(SessionStore.ARTIFACT_SPEC_FEEDBACK):
                return "PM: read qa-spec-feedback.md, fix spec.md, then submit spec"
            if st == State.DEV and self.store.read_artifact(SessionStore.ARTIFACT_DEV_FEEDBACK):
                return "Dev: read qa-dev-feedback.md, fix code/handoff, then submit dev"
            return f"Complete {st.value} phase and run: submit {st.value.lower()}"
        if st == State.IDLE:
            return "Run scope begin; agree 1–2 sentence task with human; scope confirm; then start"
        if st == State.TASK_SCOPING:
            if not s.task_scope:
                return "Collaborate with human; then scope propose --text \"…\" (1–2 sentences)"
            if not s.task_scope_confirmed:
                return "Human must confirm scope; then run scope confirm, then start"
            return "Scope confirmed; run start --mode full|lite|…"
        if st == State.DONE:
            return "Session complete."
        return "Session aborted."

    def suggest(self) -> dict:
        """Return recommended next CLI commands for the current state."""
        st = self._state()
        s = self.session
        cli = "python .cursor/skills/dev-team/scripts/dev_team_cli.py --workspace ."
        commands = [f"{cli} status", f"{cli} check"]
        notes: list[str] = []
        stop = False

        if st in GATE_STATES:
            stop = True
            phase = PHASE_FOR_GATE[st]
            notes.append(
                f"STOP: end turn. User must reply approve {phase} (or lgtm) in chat before you run CLI approve."
            )
            commands.append(f"{cli} approve {phase}  # only after user chat + hook ack")
        elif st == State.IDLE:
            commands.append(f"{cli} scope begin --name <topic>")
        elif st == State.TASK_SCOPING:
            if not s.task_scope:
                notes.append("Collaborate with human; then scope propose. Do not scope confirm in the same turn.")
            elif not s.task_scope_confirmed:
                notes.append("End turn after scope propose. Wait for user confirm scope in chat.")
                commands.append(f"{cli} scope confirm  # after user ack only")
            else:
                commands.append(f"{cli} start --mode full")
        elif st == State.RESEARCH:
            commands.extend([f"{cli} validate", f"{cli} submit research"])
        elif st == State.SPEC:
            slug = s.work_slug or (self.store.work.slug if self.store.work else "<slug>")
            commands.extend(
                [
                    f"{cli} write spec --file .dev-team/works/{slug}/artifacts/spec.md",
                    f"{cli} validate",
                    f"{cli} submit spec",
                ]
            )
        elif st == State.QA_SPEC_REVIEW:
            commands.extend(
                [
                    f"{cli} validate",
                    f"{cli} qa-pass spec",
                    f"{cli} write-qa-feedback spec --file … ; {cli} qa-reject spec",
                ]
            )
        elif st == State.DEV:
            commands.extend([f"{cli} validate", f"{cli} submit dev"])
        elif st == State.QA_DEV_REVIEW:
            commands.extend(
                [
                    f"{cli} validate",
                    f"{cli} qa-pass dev",
                    f"{cli} write-qa-feedback dev --file … ; {cli} qa-reject dev",
                ]
            )
        elif st == State.QA:
            commands.extend([f"{cli} validate", f"{cli} submit qa"])
        elif st in (State.DONE, State.ABORTED):
            notes.append(f"Session {st.value.lower()}.")

        check = run_check(self.store, s)
        if check.blocked:
            notes.insert(0, "BLOCKED: " + "; ".join(check.blockers))

        return {
            "state": st.value,
            "stop": stop,
            "blocked": check.blocked,
            "blockers": check.blockers,
            "awaiting": self._awaiting_message(st),
            "commands": commands,
            "notes": notes,
        }

    # --- Session lifecycle ---

    def scope_begin(self, name: str) -> Session:
        self._ensure_no_legacy()
        if not name or not name.strip():
            raise TransitionError(
                "scope begin requires --name <topic> (e.g. game-docs). "
                "Creates .dev-team/works/<name>-<datetime>/"
            )
        st = self._state()
        if st not in (State.IDLE, State.DONE, State.ABORTED):
            if st == State.TASK_SCOPING and self.store.work:
                raise TransitionError("Already in TASK_SCOPING. Continue scoping or run abort.")
            raise TransitionError(
                f"Cannot scope begin from {st.value}. Run abort first if a session is in progress."
            )
        work = self.store.begin_work(name.strip())
        s = Session(state=State.TASK_SCOPING.value, work_slug=work.slug)
        s.record_transition(st.value, State.TASK_SCOPING.value, "scope:begin")
        self.store.save(s)
        return s

    def scope_propose(self, text: str) -> tuple[Session, ValidationResult]:
        st = self._state()
        if st != State.TASK_SCOPING:
            raise TransitionError(f"scope propose requires TASK_SCOPING, got {st.value}.")
        result = validate_task_scope(text)
        if not result.ok:
            raise TransitionError("Task scope validation failed.", result)
        s = self.session
        s.task_scope = text.strip()
        s.task_scope_confirmed = False
        s.task_scope_proposed_at = _utc_now()
        s.record_transition(st.value, st.value, "scope:propose")
        self.store.save(s)
        return s, result

    def scope_confirm(self) -> Session:
        st = self._state()
        if st != State.TASK_SCOPING:
            raise TransitionError(f"scope confirm requires TASK_SCOPING, got {st.value}.")
        s = self.session
        if not s.task_scope:
            raise TransitionError("No proposed scope. Run scope propose --text \"…\" first.")
        ack_row = find_ack(self.store, action="scope_confirm")
        if ack_row is None:
            self._require_human("scope confirm", action="scope_confirm")
        else:
            ack_at = ack_row.get("payload", {}).get("at", "")
            if s.task_scope_proposed_at and ack_at:
                try:
                    proposed_ts = datetime.fromisoformat(s.task_scope_proposed_at)
                    ack_ts = datetime.fromisoformat(ack_at)
                    if ack_ts <= proposed_ts:
                        raise TransitionError(
                            "scope confirm must follow a human chat message after scope propose. "
                            "End your turn after scope propose; wait for the user to reply confirm scope."
                        )
                except ValueError:
                    pass
            self._require_human("scope confirm", action="scope_confirm")
        result = validate_task_scope(s.task_scope)
        if not result.ok:
            raise TransitionError("Proposed scope is invalid.", result)
        if s.task_scope_confirmed:
            raise TransitionError("Scope already confirmed. Run start or scope propose to revise.")
        s.task_scope_confirmed = True
        s.record_transition(st.value, st.value, "scope:confirm")
        self.store.save(s)
        return s

    def start(self, mode: str = "full", task: str | None = None) -> Session:
        self._ensure_no_legacy()
        st = self._state()
        if st != State.TASK_SCOPING:
            raise TransitionError(
                f"start requires TASK_SCOPING with confirmed scope, got {st.value}. "
                "Run: scope begin → scope propose → (human confirms) → scope confirm → start"
            )

        s = self.session
        if not s.task_scope_confirmed:
            raise TransitionError(
                "Human has not confirmed task scope. Run scope confirm after the user approves the wording."
            )

        scope_text = s.task_scope
        if task and task.strip() != scope_text:
            raise TransitionError(
                "start --task must match the confirmed scope text exactly, or omit --task."
            )

        result = validate_task_scope(scope_text)
        if not result.ok:
            raise TransitionError("Confirmed task scope is invalid.", result)

        valid_modes = ("full", "lite", "skip-research", "skip-to-dev")
        if mode not in valid_modes:
            raise TransitionError(f"Invalid mode {mode!r}. Choose from: {', '.join(valid_modes)}")

        s.task = scope_text
        s.session_id = str(uuid.uuid4())
        s.mode = mode
        if mode == "full":
            target = State.RESEARCH
        elif mode in ("lite", "skip-research"):
            target = State.SPEC
            s.research_approved = True
        else:
            target = State.DEV
            s.research_approved = True
            s.spec_approved = True
            s.spec_qa_passed = True

        s.record_transition(State.TASK_SCOPING.value, target.value, f"start:{mode}")
        s.state = target.value
        self.store.save(s)
        return s

    def abort(self) -> Session:
        s = self.session
        st = self._state()
        if st in (State.DONE, State.ABORTED):
            raise TransitionError(f"Cannot abort from {st.value}.")
        s = self._set_state(s, State.ABORTED, "abort")
        self.store.registry.clear_active()
        return s

    def record_checks(self, note: str) -> Session:
        s = self.session
        if self._state() != State.DEV:
            raise TransitionError("record-checks is only allowed in DEV state.")
        s.checks_run.append(note)
        self.store.save(s)
        return s

    # --- Artifact I/O ---

    def write_artifact(self, phase: str, content: str) -> Path:
        self._ensure_not_blocked()
        phase = phase.lower()
        mapping = {
            "research": (State.RESEARCH, "research.md"),
            "spec": (State.SPEC, "spec.md"),
            "dev": (State.DEV, "dev-handoff.md"),
            "qa": (State.QA, "qa-report.md"),
        }
        if phase not in mapping:
            raise TransitionError(f"Unknown phase {phase!r}.")
        required_state, filename = mapping[phase]
        st = self._state()
        if st != required_state:
            raise TransitionError(
                f"Cannot write {phase} artifact in {st.value}. Expected {required_state.value}."
            )
        return self.store.write_artifact(filename, content)

    def write_qa_feedback(self, target: str, content: str) -> Path:
        self._ensure_not_blocked()
        target = target.lower()
        st = self._state()
        if target == "spec":
            if st != State.QA_SPEC_REVIEW:
                raise TransitionError(f"qa-feedback spec requires QA_SPEC_REVIEW, got {st.value}.")
            filename = SessionStore.ARTIFACT_SPEC_FEEDBACK
            result = validate_qa_spec_feedback(content)
        elif target == "dev":
            if st != State.QA_DEV_REVIEW:
                raise TransitionError(f"qa-feedback dev requires QA_DEV_REVIEW, got {st.value}.")
            filename = SessionStore.ARTIFACT_DEV_FEEDBACK
            result = validate_qa_dev_feedback(content)
        else:
            raise TransitionError("qa-feedback target must be 'spec' or 'dev'.")

        if not result.ok:
            raise TransitionError("QA feedback validation failed.", result)
        return self.store.write_artifact(filename, content)

    def _validate_phase(self, st: State, content: str) -> ValidationResult:
        s = self.session
        if st == State.RESEARCH:
            return validate_research(content)
        if st == State.SPEC:
            return validate_spec(
                content,
                research_approved=s.research_approved,
                mode=s.mode,
            )
        if st == State.DEV:
            return validate_dev_handoff(
                content,
                spec_approved=s.spec_approved,
                spec_content=self.store.read_artifact("spec.md"),
                checks_run=s.checks_run,
            )
        if st == State.QA:
            return validate_qa_report(
                content,
                dev_approved=s.dev_approved,
                spec_content=self.store.read_artifact("spec.md"),
            )
        raise TransitionError(f"No validator for state {st.value}.")

    def validate_current(self) -> ValidationResult:
        st = self._state()
        if st in QA_REVIEW_STATES:
            if st == State.QA_SPEC_REVIEW:
                content = self.store.read_artifact("spec.md")
                if content is None:
                    return ValidationResult(False, ["spec.md missing"], [])
                return validate_spec_for_qa_review(content)
            content = self.store.read_artifact("dev-handoff.md")
            spec = self.store.read_artifact("spec.md")
            if content is None:
                return ValidationResult(False, ["dev-handoff.md missing"], [])
            base = validate_dev_handoff(
                content,
                spec_approved=True,
                spec_content=spec,
                checks_run=self.session.checks_run,
            )
            vs = validate_dev_vs_spec(content, spec)
            return base.merge(vs)
        if st not in WORK_STATES:
            raise TransitionError(f"validate not available in {st.value}.")
        filename = ARTIFACT_BY_STATE[st]
        content = self.store.read_artifact(filename)
        if content is None:
            return ValidationResult(False, [f"Missing artifact: {filename}"], [])
        return self._validate_phase(st, content)

    def submit(self, phase: str | None = None) -> tuple[Session, ValidationResult]:
        st = self._state()
        if phase:
            phase_state = {
                "research": State.RESEARCH,
                "spec": State.SPEC,
                "dev": State.DEV,
                "qa": State.QA,
            }.get(phase.lower())
            if phase_state is None:
                raise TransitionError(f"Unknown phase {phase!r}.")
            if st != phase_state:
                raise TransitionError(f"submit {phase} requires {phase_state.value}, got {st.value}.")

        if st == State.RESEARCH:
            return self._submit_work(State.RESEARCH, State.RESEARCH_GATE)
        if st == State.SPEC:
            s = self.session
            self._bump_qa_cycle(s, "spec")
            self.store.save(s)
            return self._submit_work(State.SPEC, State.QA_SPEC_REVIEW)
        if st == State.DEV:
            s = self.session
            self._bump_qa_cycle(s, "dev")
            self.store.save(s)
            return self._submit_work(State.DEV, State.QA_DEV_REVIEW)
        if st == State.QA:
            return self._submit_work(State.QA, State.QA_GATE)

        raise TransitionError(f"submit not allowed in {st.value}.")

    def _submit_work(self, work: State, nxt: State) -> tuple[Session, ValidationResult]:
        self._ensure_no_legacy()
        self._ensure_not_blocked()
        phase = work.value.lower()
        present = artifact_requirements_met(self.store, phase)
        if not present.ok:
            raise TransitionError(
                f"Cannot submit {phase}: artifact requirements not met.",
                present,
            )
        filename = ARTIFACT_BY_STATE[work]
        content = self.store.read_artifact(filename)
        if content is None:
            raise TransitionError(
                f"No artifact at artifacts/{filename}. Write it first.",
                ValidationResult(False, ["Artifact file missing."], []),
            )
        result = self._validate_phase(work, content)
        if not result.ok:
            raise TransitionError(
                f"Phase {work.value} validation failed. Fix errors and submit again.",
                result,
            )
        s = self.session
        record_artifact_hash(s, phase, self.store)
        self.store.save(s)
        return self._set_state(s, nxt, f"submit:{work.value.lower()}"), result

    # --- QA review loops (QA ↔ PM, QA ↔ Dev) ---

    def qa_pass(self, target: str) -> tuple[Session, ValidationResult]:
        target = target.lower()
        st = self._state()

        if target == "spec":
            if st != State.QA_SPEC_REVIEW:
                raise TransitionError(f"qa-pass spec requires QA_SPEC_REVIEW, got {st.value}.")
            present = artifact_requirements_met(self.store, "spec")
            if not present.ok:
                raise TransitionError("Cannot qa-pass spec: artifact missing or too small.", present)
            content = self.store.read_artifact("spec.md") or ""
            result = validate_spec_for_qa_review(content)
            if not result.ok:
                raise TransitionError("Spec failed QA standards. Use qa-reject spec with feedback.", result)
            s = self.session
            record_artifact_hash(s, "spec", self.store)
            s.spec_qa_passed = True
            self.store.save(s)
            return self._set_state(s, State.SPEC_GATE, "qa-pass:spec"), result

        if target == "dev":
            if st != State.QA_DEV_REVIEW:
                raise TransitionError(f"qa-pass dev requires QA_DEV_REVIEW, got {st.value}.")
            present = artifact_requirements_met(self.store, "dev")
            if not present.ok:
                raise TransitionError("Cannot qa-pass dev: artifact missing or too small.", present)
            dev = self.store.read_artifact("dev-handoff.md") or ""
            spec = self.store.read_artifact("spec.md")
            base = validate_dev_handoff(
                dev,
                spec_approved=True,
                spec_content=spec,
                checks_run=self.session.checks_run,
            )
            vs = validate_dev_vs_spec(dev, spec)
            result = base.merge(vs)
            if not result.ok:
                raise TransitionError(
                    "Dev handoff does not match spec. Use qa-reject dev with feedback.",
                    result,
                )
            s = self.session
            record_artifact_hash(s, "dev", self.store)
            s.dev_qa_passed = True
            self.store.save(s)
            return self._set_state(s, State.DEV_GATE, "qa-pass:dev"), result

        raise TransitionError("qa-pass target must be 'spec' or 'dev'.")

    def qa_reject(self, target: str) -> Session:
        target = target.lower()
        st = self._state()

        if target == "spec":
            if st != State.QA_SPEC_REVIEW:
                raise TransitionError(f"qa-reject spec requires QA_SPEC_REVIEW, got {st.value}.")
            feedback = self.store.read_artifact(SessionStore.ARTIFACT_SPEC_FEEDBACK)
            if feedback is None:
                raise TransitionError(
                    "Write qa-spec-feedback.md first: write-qa-feedback spec --file …"
                )
            result = validate_qa_spec_feedback(feedback)
            if not result.ok:
                raise TransitionError("Invalid qa-spec-feedback.md.", result)
            s = self.session
            s.spec_qa_passed = False
            self.store.save(s)
            return self._set_state(s, State.SPEC, "qa-reject:spec")

        if target == "dev":
            if st != State.QA_DEV_REVIEW:
                raise TransitionError(f"qa-reject dev requires QA_DEV_REVIEW, got {st.value}.")
            feedback = self.store.read_artifact(SessionStore.ARTIFACT_DEV_FEEDBACK)
            if feedback is None:
                raise TransitionError(
                    "Write qa-dev-feedback.md first: write-qa-feedback dev --file …"
                )
            result = validate_qa_dev_feedback(feedback)
            if not result.ok:
                raise TransitionError("Invalid qa-dev-feedback.md.", result)
            s = self.session
            s.dev_qa_passed = False
            self.store.save(s)
            return self._set_state(s, State.DEV, "qa-reject:dev")

        raise TransitionError("qa-reject target must be 'spec' or 'dev'.")

    # --- Human gates ---

    def approve(self, phase: str) -> Session:
        self._ensure_no_legacy()
        self._require_human(f"approve {phase}", action="approve", phase=phase)
        phase = phase.lower()
        st = self._state()
        gate_by_phase = {
            "research": State.RESEARCH_GATE,
            "spec": State.SPEC_GATE,
            "dev": State.DEV_GATE,
            "qa": State.QA_GATE,
        }
        if phase not in gate_by_phase:
            raise TransitionError(f"Unknown approve phase {phase!r}.")

        expected_gate = gate_by_phase[phase]
        if st != expected_gate:
            raise TransitionError(
                f"approve {phase} requires {expected_gate.value}, currently {st.value}."
            )

        s = self.session
        if phase == "research":
            present = artifact_requirements_met(self.store, "research")
            if not present.ok:
                raise TransitionError("Cannot approve research: artifact not ready.", present)
            s.research_approved = True
        elif phase == "spec":
            if not s.spec_qa_passed:
                raise TransitionError("Spec must pass QA review (qa-pass spec) before human approve.")
            hash_ok = verify_artifact_hash(s, "spec", self.store)
            if not hash_ok.ok:
                raise TransitionError("Cannot approve spec: artifact changed since qa-pass.", hash_ok)
            spec_content = self.store.read_artifact("spec.md") or ""
            s.implementation_allowlist = parse_implementation_allowlist(spec_content)
            if not s.implementation_allowlist:
                raise TransitionError(
                    "spec.md must include ### Implementation allowlist with at least one path "
                    "(e.g. - docs/design/**) before approve spec."
                )
            s.spec_approved = True
        elif phase == "dev":
            if not s.dev_qa_passed:
                raise TransitionError("Dev must pass QA review (qa-pass dev) before human approve.")
            hash_ok = verify_artifact_hash(s, "dev", self.store)
            if not hash_ok.ok:
                raise TransitionError("Cannot approve dev: handoff changed since qa-pass.", hash_ok)
            s.dev_approved = True
        elif phase == "qa":
            present = artifact_requirements_met(self.store, "qa")
            if not present.ok:
                raise TransitionError("Cannot approve QA: qa-report.md not ready.", present)
            s.qa_approved = True

        next_state = NEXT_AFTER_APPROVE[expected_gate]
        return self._set_state(s, next_state, f"approve:{phase}")

    def revise(self, phase: str, feedback: str = "") -> Session:
        self._require_human(f"revise {phase}", action="revise", phase=phase)
        phase = phase.lower()
        work = {
            "research": (State.RESEARCH_GATE, State.RESEARCH),
            "spec": (State.SPEC_GATE, State.SPEC),
            "dev": (State.DEV_GATE, State.DEV),
            "qa": (State.QA_GATE, State.QA),
        }
        if phase not in work:
            raise TransitionError(f"Unknown revise phase {phase!r}.")
        gate, work_state = work[phase]
        st = self._state()
        if st != gate:
            raise TransitionError(f"revise {phase} requires {gate.value}, currently {st.value}.")

        s = self.session
        if phase == "spec":
            s.spec_qa_passed = False
            s.spec_approved = False
        elif phase == "dev":
            s.dev_qa_passed = False
            s.dev_approved = False

        if feedback:
            s.revision_notes.append(f"[{phase}] {feedback}")
        return self._set_state(s, work_state, f"revise:{phase}")

    def reject(self, target: str) -> Session:
        target = target.lower().replace("_", "-")
        self._require_human(f"reject to {target}", action="reject", target=target)
        mapping = {
            "research": (State.SPEC_GATE, State.RESEARCH),
            "spec": (State.DEV_GATE, State.SPEC),
            "dev": (State.QA_GATE, State.DEV),
        }
        if target not in mapping:
            raise TransitionError("reject target must be one of: research, spec, dev.")

        required_gate, work_state = mapping[target]
        st = self._state()
        if st != required_gate:
            raise TransitionError(f"reject to {target} requires {required_gate.value}, got {st.value}.")

        removed = self.store.invalidate_from(target)
        s = self.session

        if target == "research":
            s.research_approved = False
            s.spec_qa_passed = False
            s.spec_approved = False
            s.dev_qa_passed = False
            s.dev_approved = False
            s.spec_qa_cycle = 0
            s.dev_qa_cycle = 0
        elif target == "spec":
            s.spec_qa_passed = False
            s.spec_approved = False
            s.dev_qa_passed = False
            s.dev_approved = False
            s.spec_qa_cycle = 0
            s.dev_qa_cycle = 0
        elif target == "dev":
            s.dev_qa_passed = False
            s.dev_approved = False
            s.dev_qa_cycle = 0

        s.revision_notes.append(f"[reject] sent back to {target}; removed: {removed}")
        return self._set_state(s, work_state, f"reject:{target}")
