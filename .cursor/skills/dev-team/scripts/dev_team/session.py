"""Persistent dev-team session stored per work directory under .dev-team/works/."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dev_team.work_log import WorkLogger
from dev_team.work_registry import WorkDir, WorkRegistry

MAX_QA_LOOPS = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Session:
    state: str = "IDLE"
    work_slug: str = ""
    session_id: str = ""
    task_scope: str = ""
    task_scope_proposed_at: str = ""
    task_scope_confirmed: bool = False
    task: str = ""
    mode: str = "full"
    research_approved: bool = False
    spec_qa_passed: bool = False
    spec_approved: bool = False
    dev_qa_passed: bool = False
    dev_approved: bool = False
    qa_approved: bool = False
    spec_qa_cycle: int = 0
    dev_qa_cycle: int = 0
    revision_notes: list[str] = field(default_factory=list)
    checks_run: list[str] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    implementation_allowlist: list[str] = field(default_factory=list)
    pending_human_gate: str = ""
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    history: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> Session:
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def save(self, path: Path) -> None:
        self.updated_at = _utc_now()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def record_transition(self, from_state: str, to_state: str, event: str) -> None:
        self.history.append(
            {
                "at": _utc_now(),
                "from": from_state,
                "to": to_state,
                "event": event,
            }
        )


class SessionStore:
    ARTIFACT_SPEC_FEEDBACK = "qa-spec-feedback.md"
    ARTIFACT_DEV_FEEDBACK = "qa-dev-feedback.md"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.registry = WorkRegistry(self.project_root)
        self._work: WorkDir | None = None
        self._logger: WorkLogger | None = None
        self._bind_active()

    def _bind_active(self) -> None:
        self._work = self.registry.get_active()
        self._logger = (
            WorkLogger(self._work.logs_dir, self._work.slug) if self._work else None
        )

    @property
    def work(self) -> WorkDir | None:
        return self._work

    @property
    def root(self) -> Path:
        return self.registry.root

    @property
    def session_path(self) -> Path:
        if self._work:
            return self._work.session_path
        return self.registry.root / "session.json"

    @property
    def artifacts_dir(self) -> Path:
        if self._work:
            return self._work.artifacts_dir
        return self.registry.root / "artifacts"

    def begin_work(self, name: str) -> WorkDir:
        self._work = self.registry.create_work(name)
        self._logger = WorkLogger(self._work.logs_dir, self._work.slug)
        self.log("work_created", detail=self._work.slug, extra={"name": self._work.name})
        return self._work

    def log(
        self,
        event: str,
        *,
        level: str = "info",
        role: str = "",
        command: str = "",
        ok: bool | None = None,
        detail: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        if self._logger:
            self._logger.event(
                event,
                level=level,
                role=role,
                command=command,
                ok=ok,
                detail=detail,
                extra=extra,
            )

    def sync_meta(self, session: Session) -> None:
        if self._work:
            self.registry.update_meta(
                self._work,
                state=session.state,
                task_scope=session.task_scope or session.task,
            )

    def load(self) -> Session:
        return Session.load(self.session_path)

    def save(self, session: Session) -> None:
        if not self._work and session.state not in ("IDLE",):
            raise RuntimeError("No active work directory. Run scope begin --name <topic> first.")
        session.work_slug = self._work.slug if self._work else session.work_slug
        session.save(self.session_path)
        self.sync_meta(session)

    def artifact_path(self, name: str) -> Path:
        return self.artifacts_dir / name

    def write_artifact(self, name: str, content: str) -> Path:
        path = self.artifact_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.log("artifact_write", detail=name)
        return path

    def read_artifact(self, name: str) -> str | None:
        path = self.artifact_path(name)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def invalidate_from(self, phase: str) -> list[str]:
        order = [
            "research.md",
            "spec.md",
            self.ARTIFACT_SPEC_FEEDBACK,
            "dev-handoff.md",
            self.ARTIFACT_DEV_FEEDBACK,
            "qa-report.md",
        ]
        start = {"research": 0, "spec": 1, "dev": 3, "qa": 5}.get(phase, 0)
        removed: list[str] = []
        for name in order[start:]:
            path = self.artifact_path(name)
            if path.exists():
                path.unlink()
                removed.append(name)
        if removed:
            self.log("artifacts_invalidated", detail=",".join(removed), extra={"phase": phase})
        return removed

    def tail_log(self, lines: int = 30) -> list[dict[str, Any]]:
        if not self._logger:
            return []
        return self._logger.tail(lines)

    def clear_logs(self) -> None:
        """Clear log files for the active work instance."""
        if not self._logger:
            raise RuntimeError("No active work. Nothing to clear.")
        self._logger.clear()

    def remove_work(self, slug: str) -> str:
        """Delete a work directory (artifacts, logs, session). Returns removed slug."""
        self.registry.remove_work(slug)
        if self._work and self._work.slug == slug:
            self._work = None
            self._logger = None
        else:
            self._bind_active()
        return slug

    def purge_legacy(self) -> list[str]:
        """Remove root-level session/artifacts from pre-work-dir layout."""
        removed: list[str] = []
        for rel in ("session.json", "artifacts"):
            path = self.registry.root / rel
            if path.is_file():
                path.unlink()
                removed.append(str(path.relative_to(self.project_root)))
            elif path.is_dir():
                import shutil

                shutil.rmtree(path)
                removed.append(str(path.relative_to(self.project_root)))
        self.registry.clear_active()
        self._work = None
        self._logger = None
        return removed

    def show_work(self, slug: str | None = None) -> dict | None:
        work = self._work
        if slug:
            path = self.registry.works_root / slug
            if not path.is_dir():
                return None
            meta_path = path / "meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            work = WorkDir(slug=slug, path=path, name=meta.get("name", slug))
        if not work:
            return None
        artifacts = {}
        for name in (
            "research.md",
            "spec.md",
            self.ARTIFACT_SPEC_FEEDBACK,
            "dev-handoff.md",
            self.ARTIFACT_DEV_FEEDBACK,
            "qa-report.md",
        ):
            p = work.artifacts_dir / name
            artifacts[name] = {
                "exists": p.exists(),
                "bytes": p.stat().st_size if p.exists() else 0,
            }
        session = Session.load(work.session_path) if work.session_path.exists() else None
        return {
            "slug": work.slug,
            "path": str(work.path.relative_to(self.project_root)),
            "name": work.name,
            "state": session.state if session else "unknown",
            "artifacts": artifacts,
        }
