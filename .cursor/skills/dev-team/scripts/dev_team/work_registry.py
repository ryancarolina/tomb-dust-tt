"""Per-task work directories under .dev-team/works/<slug>/."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")


def slugify_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:40] or "work"


def make_work_slug(name: str | None) -> str:
    base = slugify_name(name) if name else "work"
    return f"{base}-{_timestamp()}"


@dataclass
class WorkDir:
    slug: str
    path: Path
    name: str

    @property
    def artifacts_dir(self) -> Path:
        return self.path / "artifacts"

    @property
    def logs_dir(self) -> Path:
        return self.path / "logs"

    @property
    def session_path(self) -> Path:
        return self.path / "session.json"

    @property
    def meta_path(self) -> Path:
        return self.path / "meta.json"


class WorkRegistry:
    ACTIVE_FILE = "active.json"
    WORKS_DIR = "works"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.root = self.project_root / ".dev-team"
        self.works_root = self.root / self.WORKS_DIR
        self.active_path = self.root / self.ACTIVE_FILE
        self.works_root.mkdir(parents=True, exist_ok=True)

    def create_work(self, name: str) -> WorkDir:
        if not name or not name.strip():
            raise ValueError("Work name is required. Use scope begin --name <topic>")
        slug = make_work_slug(name)
        work = WorkDir(slug=slug, path=self.works_root / slug, name=slugify_name(name))
        work.path.mkdir(parents=True, exist_ok=True)
        work.artifacts_dir.mkdir(exist_ok=True)
        work.logs_dir.mkdir(exist_ok=True)
        meta = {
            "slug": slug,
            "name": work.name,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "task_scope": "",
            "state": "TASK_SCOPING",
        }
        work.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self.set_active(slug)
        return work

    def set_active(self, slug: str) -> None:
        work_path = self.works_root / slug
        if not work_path.is_dir():
            raise FileNotFoundError(f"Work directory not found: {work_path}")
        payload = {
            "work_slug": slug,
            "path": f"{self.WORKS_DIR}/{slug}",
            "activated_at": _utc_now(),
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.active_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get_active(self) -> WorkDir | None:
        if not self.active_path.exists():
            return None
        data = json.loads(self.active_path.read_text(encoding="utf-8"))
        slug = data.get("work_slug", "")
        if not slug:
            return None
        path = self.works_root / slug
        if not path.is_dir():
            return None
        meta = {}
        meta_path = path / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return WorkDir(slug=slug, path=path, name=meta.get("name", slug))

    def update_meta(self, work: WorkDir, **fields: str) -> None:
        meta = json.loads(work.meta_path.read_text(encoding="utf-8"))
        meta.update(fields)
        meta["updated_at"] = _utc_now()
        work.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def list_works(self) -> list[dict]:
        items: list[dict] = []
        if not self.works_root.exists():
            return items
        for path in sorted(self.works_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not path.is_dir():
                continue
            meta_path = path / "meta.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            else:
                meta = {"slug": path.name, "state": "unknown"}
            items.append(
                {
                    "slug": meta.get("slug", path.name),
                    "name": meta.get("name", ""),
                    "state": meta.get("state", ""),
                    "task_scope": meta.get("task_scope", ""),
                    "created_at": meta.get("created_at", ""),
                    "path": str(path.relative_to(self.project_root)),
                }
            )
        return items

    def clear_active(self) -> None:
        if self.active_path.exists():
            self.active_path.unlink()

    def remove_work(self, slug: str) -> Path:
        """Delete a work directory and clear active pointer if it matches."""
        path = self.works_root / slug
        if not path.is_dir():
            raise FileNotFoundError(f"Work directory not found: {slug}")
        active = self.get_active()
        if active and active.slug == slug:
            self.clear_active()
        shutil.rmtree(path)
        return path
