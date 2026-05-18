"""Structured logs per dev-team work instance."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkLogger:
    def __init__(self, logs_dir: Path, work_slug: str) -> None:
        self.logs_dir = logs_dir
        self.work_slug = work_slug
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = logs_dir / "events.jsonl"
        self.audit_path = logs_dir / "audit.log"

    def event(
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
        row: dict[str, Any] = {
            "at": _utc_now(),
            "work_slug": self.work_slug,
            "event": event,
            "level": level,
        }
        if role:
            row["role"] = role
        if command:
            row["command"] = command
        if ok is not None:
            row["ok"] = ok
        if detail:
            row["detail"] = detail
        if extra:
            row.update(extra)

        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

        stamp = row["at"][:19].replace("T", " ")
        parts = [stamp, level.upper(), event]
        if role:
            parts.append(f"role={role}")
        if command:
            parts.append(f"cmd={command}")
        if ok is not None:
            parts.append("ok" if ok else "FAIL")
        if detail:
            parts.append(detail)
        line = " | ".join(parts) + "\n"
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(line)

    def tail(self, lines: int = 30) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        all_lines = self.events_path.read_text(encoding="utf-8").strip().splitlines()
        tail_lines = all_lines[-lines:]
        return [json.loads(ln) for ln in tail_lines if ln.strip()]

    def clear(self) -> None:
        """Remove audit.log and events.jsonl for this work instance."""
        for path in (self.events_path, self.audit_path):
            if path.exists():
                path.unlink()
