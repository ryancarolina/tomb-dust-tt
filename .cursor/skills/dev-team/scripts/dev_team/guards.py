"""Defense-in-depth guards for dev-team workflow."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from dev_team.allowlist import parse_implementation_allowlist
from dev_team.session import Session, SessionStore
from dev_team.validators import ValidationResult, validate_spec_for_qa_review

# States where repo implementation is forbidden (only .dev-team/works/<slug>/artifacts/).
IMPLEMENTATION_LOCKED_STATES = frozenset(
    {
        "TASK_SCOPING",
        "RESEARCH",
        "RESEARCH_GATE",
        "SPEC",
        "QA_SPEC_REVIEW",
        "SPEC_GATE",
        "QA",
        "QA_GATE",
        "IDLE",
        "DONE",
        "ABORTED",
    }
)

MIN_ARTIFACT_BYTES = 200

PHASE_ARTIFACT = {
    "research": "research.md",
    "spec": "spec.md",
    "dev": "dev-handoff.md",
    "qa": "qa-report.md",
}

GATE_REQUIRED_ARTIFACT = {
    "RESEARCH_GATE": "research",
    "SPEC_GATE": "spec",
    "DEV_GATE": "dev",
    "QA_GATE": "qa",
}


@dataclass
class CheckReport:
    ok: bool
    blocked: bool
    implementation_lock: bool
    artifacts_ok: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "blocked": self.blocked,
            "implementation_lock": self.implementation_lock,
            "artifacts_ok": self.artifacts_ok,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def implementation_locked(state: str) -> bool:
    return state in IMPLEMENTATION_LOCKED_STATES


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_requirements_met(store: SessionStore, phase: str) -> ValidationResult:
    filename = PHASE_ARTIFACT.get(phase)
    if not filename:
        return ValidationResult(False, [f"Unknown phase {phase!r}"], [])
    path = store.artifact_path(filename)
    if not path.exists():
        return ValidationResult(False, [f"Missing artifact: {filename}"], [])
    size = path.stat().st_size
    if size < MIN_ARTIFACT_BYTES:
        return ValidationResult(
            False,
            [f"{filename} too small ({size} bytes); minimum {MIN_ARTIFACT_BYTES} bytes required."],
            [],
        )
    return ValidationResult(True, [], [])


def record_artifact_hash(session: Session, phase: str, store: SessionStore) -> None:
    filename = PHASE_ARTIFACT.get(phase)
    if not filename:
        return
    path = store.artifact_path(filename)
    if path.exists():
        if session.artifact_hashes is None:
            session.artifact_hashes = {}
        session.artifact_hashes[filename] = file_sha256(path)


def verify_artifact_hash(session: Session, phase: str, store: SessionStore) -> ValidationResult:
    filename = PHASE_ARTIFACT.get(phase)
    if not filename:
        return ValidationResult(True, [], [])
    path = store.artifact_path(filename)
    if not path.exists():
        return ValidationResult(False, [f"Missing artifact: {filename}"], [])
    expected = (session.artifact_hashes or {}).get(filename)
    if not expected:
        return ValidationResult(
            False,
            [f"No stored hash for {filename}; run submit {phase} before approve."],
            [],
        )
    actual = file_sha256(path)
    if actual != expected:
        return ValidationResult(
            False,
            [f"{filename} changed after submit/qa-pass. Re-submit or revise."],
            [],
        )
    return ValidationResult(True, [], [])


def path_allowed_for_dev(rel_path: str, allowlist: list[str]) -> bool:
    if not allowlist:
        return False
    rel = rel_path.replace("\\", "/").lstrip("./")
    for pattern in allowlist:
        pat = pattern.replace("\\", "/").strip().lstrip("./")
        if pat.endswith("/**"):
            if rel == pat[:-3] or rel.startswith(pat[:-2]):
                return True
        elif pat.endswith("/*"):
            prefix = pat[:-2]
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
        elif rel == pat or rel.startswith(pat.rstrip("/") + "/"):
            return True
    return False


def legacy_session_present(store: SessionStore) -> bool:
    legacy = store.registry.root / "session.json"
    return legacy.exists() and store.work is None


def gate_artifacts_ready(store: SessionStore, state: str) -> ValidationResult:
    phase = GATE_REQUIRED_ARTIFACT.get(state)
    if not phase:
        return ValidationResult(True, [], [])
    return artifact_requirements_met(store, phase)


def run_check(store: SessionStore, session: Session) -> CheckReport:
    report = CheckReport(
        ok=True,
        blocked=False,
        implementation_lock=implementation_locked(session.state),
        artifacts_ok=True,
    )

    if legacy_session_present(store):
        report.blockers.append(
            "Legacy .dev-team/session.json detected. Run: dev_team_cli.py reset"
        )

    if session.state not in ("IDLE", "DONE", "ABORTED") and store.work is None:
        report.blockers.append("No active work directory. Run scope begin --name <topic>")

    if store.work and not store.work.path.is_dir():
        report.blockers.append(f"Work directory missing: {store.work.path}")

    # Phase-required artifacts for human gates
    if session.state in GATE_REQUIRED_ARTIFACT:
        gate_result = gate_artifacts_ready(store, session.state)
        if not gate_result.ok:
            report.blockers.extend(gate_result.errors)
            report.artifacts_ok = False

    if session.state == "QA_SPEC_REVIEW":
        if not store.artifact_path("spec.md").exists():
            report.blockers.append("QA_SPEC_REVIEW requires artifacts/spec.md")
            report.artifacts_ok = False

    if session.state == "QA_DEV_REVIEW":
        if not store.artifact_path("dev-handoff.md").exists():
            report.blockers.append("QA_DEV_REVIEW requires artifacts/dev-handoff.md")
            report.artifacts_ok = False

    if report.blockers:
        report.blocked = True
        report.ok = False
        report.artifacts_ok = False

    return report


def assert_repo_edit_allowed(
    project_root: Path,
    file_path: Path,
    session: Session,
    store: SessionStore,
) -> tuple[bool, str]:
    """Return (allowed, reason). Used by Cursor hooks."""
    if not store.work:
        return True, "no active dev-team work"

    rel = str(file_path.resolve().relative_to(project_root.resolve())).replace("\\", "/")

    # Always allow dev-team work dir
    work_rel = str(store.work.path.relative_to(project_root)).replace("\\", "/")
    if rel.startswith(work_rel + "/") or rel == work_rel:
        return True, "inside work directory"

    if not implementation_locked(session.state):
        allowlist = session.implementation_allowlist or []
        if path_allowed_for_dev(rel, allowlist):
            return True, "on implementation allowlist"
        return (
            False,
            f"DEV state but path not on allowlist from spec: {rel}. "
            "Add to ### Implementation allowlist in spec.md and approve spec.",
        )

    return (
        False,
        f"implementation_lock active in state {session.state}. "
        f"Only edit files under {work_rel}/artifacts/ until approve spec → DEV.",
    )
