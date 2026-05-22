"""Shared backlog ticket helpers for claim script and Cursor hooks."""

from __future__ import annotations

import fnmatch
import json
import re
from datetime import date
from pathlib import Path

TICKET_ID_RE = re.compile(r"^APP-\d{3}$")
ACTIVE_STATUSES = frozenset({"open", "in_progress"})
PICKABLE_STATUSES = frozenset({"open"})
CLOSED_STATUSES = frozenset({"done", "cancelled"})

_LIB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _LIB_DIR.parents[1]
BACKLOG_DIR = _LIB_DIR
RUNS_DIR = BACKLOG_DIR / "runs"
ACTIVE_TICKET_PATH = PROJECT_ROOT / "tmp" / ".active-ticket.json"
ACTIVE_BATCH_PATH = PROJECT_ROOT / "tmp" / ".active-batch.json"
MAX_BATCH_SIZE = 3
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

ALWAYS_ALLOWED_PREFIXES = (
    "tmp/backlog/",
    "tmp/app-",
    ".cursor/",
)

ALWAYS_ALLOWED_FILES = frozenset(
    {
        "tmp/.active-ticket.json",
        "tmp/.active-batch.json",
        "AGENTS.md",
    }
)


def normalize_path(path: str) -> str:
    p = path.replace("\\", "/").lstrip("./")
    return p


def find_ticket_file(ticket_id: str) -> Path | None:
    if not TICKET_ID_RE.match(ticket_id):
        return None
    prefix = ticket_id.lower()
    matches = sorted(BACKLOG_DIR.glob(f"{prefix}-*.md"))
    if not matches:
        matches = sorted(BACKLOG_DIR.glob(f"{prefix}*.md"))
    return matches[0] if matches else None


def parse_ticket_fields(ticket_path: Path) -> dict[str, str]:
    text = ticket_path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for key in ("ID", "Type", "Priority", "Status"):
        m = re.search(rf"\*\*{key}\*\* \| ([^|\n]+)", text)
        if m:
            fields[key.lower()] = m.group(1).strip()
    m_spec = re.search(r"Domain spec\*\* \| \[([^\]]+)\]\(\.\./([^)]+)\)", text)
    if m_spec:
        fields["domain_spec"] = m_spec.group(2).strip()
    title = text.split("\n", 1)[0].removeprefix("# ").strip()
    if ": " in title:
        fields["title"] = title.split(": ", 1)[1]
    else:
        fields["title"] = title
    return fields


def parse_expected_files(ticket_path: Path) -> list[str]:
    text = ticket_path.read_text(encoding="utf-8")
    section = re.search(
        r"## Expected files\s*\n(.*?)(?:\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not section:
        return []
    paths: list[str] = []
    for line in section.group(1).splitlines():
        m = re.match(r"- `([^`]+)`", line.strip())
        if m:
            paths.append(normalize_path(m.group(1)))
    return paths


def set_ticket_status(ticket_path: Path, status: str, *, closed: bool = False) -> None:
    text = ticket_path.read_text(encoding="utf-8")
    text = re.sub(
        r"(\*\*Status\*\* \| )(?:open|in_progress|done|cancelled)",
        rf"\g<1>{status}",
        text,
        count=1,
    )
    if closed and "**Closed**" not in text:
        today = date.today().isoformat()
        text = text.replace(
            "| **Created** |",
            f"| **Closed** | {today} |\n| **Created** |",
            1,
        )
    ticket_path.write_text(text, encoding="utf-8")


def run_dir_for(ticket_id: str, task_name: str) -> Path:
    slug = re.sub(r"[^a-z0-9-]+", "-", task_name.lower()).strip("-")
    return RUNS_DIR / f"{ticket_id.lower()}-{slug}"


def batch_board_basename(ticket_ids: list[str]) -> str:
    """Filename stem: batch-board-APP-001-APP-002 (sorted ticket IDs)."""
    ids = sorted({t.upper() for t in ticket_ids if TICKET_ID_RE.match(t.upper())})
    if not ids:
        return "batch-board-empty"
    return "batch-board-" + "-".join(ids)


def batch_board_path(ticket_ids: list[str]) -> Path:
    return RUNS_DIR / f"{batch_board_basename(ticket_ids)}.md"


def load_active_batch() -> dict | None:
    if not ACTIVE_BATCH_PATH.exists():
        return None
    try:
        data = json.loads(ACTIVE_BATCH_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not data.get("tickets"):
        return None
    return data


def load_active_ticket() -> dict | None:
    batch = load_active_batch()
    if batch:
        focus = batch.get("focus") or ""
        for row in batch.get("tickets", []):
            if row.get("id") == focus:
                return row
        tickets = batch.get("tickets") or []
        return tickets[0] if tickets else None
    if not ACTIVE_TICKET_PATH.exists():
        return None
    try:
        data = json.loads(ACTIVE_TICKET_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not data.get("id"):
        return None
    return data


def load_active_tickets() -> list[dict]:
    batch = load_active_batch()
    if batch:
        return list(batch.get("tickets") or [])
    single = load_active_ticket()
    return [single] if single else []


def ticket_record(
    ticket_id: str,
    ticket_path: Path,
    *,
    run_dir: Path | None = None,
    domain_spec: str = "",
    pipeline_stage: str = "claim",
) -> dict:
    fields = parse_ticket_fields(ticket_path)
    return {
        "id": ticket_id.upper(),
        "ticket_path": normalize_path(str(ticket_path.relative_to(PROJECT_ROOT))),
        "domain_spec": domain_spec or fields.get("domain_spec", ""),
        "run_dir": normalize_path(str(run_dir.relative_to(PROJECT_ROOT))) if run_dir else "",
        "priority": fields.get("priority", "P2"),
        "status": fields.get("status", ""),
        "pipeline_stage": pipeline_stage,
        "claimed_at": date.today().isoformat(),
    }


def write_active_ticket(
    ticket_id: str,
    ticket_path: Path,
    *,
    run_dir: Path | None = None,
    domain_spec: str = "",
) -> dict:
    record = ticket_record(
        ticket_id,
        ticket_path,
        run_dir=run_dir,
        domain_spec=domain_spec,
    )
    ACTIVE_TICKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_TICKET_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    write_active_batch([record], schedule=compute_schedule([ticket_id.upper()]))
    return record


def write_active_batch(
    tickets: list[dict],
    *,
    schedule: dict | None = None,
    focus: str | None = None,
) -> dict:
    ids = [t["id"] for t in tickets]
    board_path = batch_board_path(ids) if ids else None
    payload = {
        "max_parallel": MAX_BATCH_SIZE,
        "focus": focus or (ids[0] if ids else ""),
        "tickets": tickets[:MAX_BATCH_SIZE],
        "schedule": schedule or compute_schedule(ids),
        "batch_board": normalize_path(str(board_path.relative_to(PROJECT_ROOT)))
        if board_path
        else "",
        "updated_at": date.today().isoformat(),
    }
    ACTIVE_BATCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_BATCH_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if payload["tickets"]:
        ACTIVE_TICKET_PATH.write_text(
            json.dumps(payload["tickets"][0], indent=2) + "\n",
            encoding="utf-8",
        )
    return payload


def set_batch_focus(ticket_id: str) -> bool:
    batch = load_active_batch()
    if not batch:
        return False
    tid = ticket_id.upper()
    if not any(t.get("id") == tid for t in batch.get("tickets", [])):
        return False
    batch["focus"] = tid
    ACTIVE_BATCH_PATH.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    for row in batch["tickets"]:
        if row.get("id") == tid:
            ACTIVE_TICKET_PATH.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
            return True
    return False


def update_batch_ticket_stage(ticket_id: str, pipeline_stage: str) -> None:
    batch = load_active_batch()
    if not batch:
        return
    for row in batch.get("tickets", []):
        if row.get("id") == ticket_id.upper():
            row["pipeline_stage"] = pipeline_stage
    ACTIVE_BATCH_PATH.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")


def clear_active_ticket() -> None:
    if ACTIVE_TICKET_PATH.exists():
        ACTIVE_TICKET_PATH.unlink()
    if ACTIVE_BATCH_PATH.exists():
        ACTIVE_BATCH_PATH.unlink()


def remove_ticket_from_batch(ticket_id: str) -> None:
    batch = load_active_batch()
    if not batch:
        return
    tid = ticket_id.upper()
    remaining = [t for t in batch.get("tickets", []) if t.get("id") != tid]
    if not remaining:
        clear_active_ticket()
        return
    write_active_batch(remaining, schedule=compute_schedule([t["id"] for t in remaining]))


def parse_dependencies(ticket_path: Path) -> dict[str, list[str]]:
    """Return blocked_by (hard), blocks, soft_blocked_by from ## Dependencies table."""
    text = ticket_path.read_text(encoding="utf-8")
    section = re.search(
        r"## Dependencies\s*\n(.*?)(?:\n## |\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    blocked_by: list[str] = []
    blocks: list[str] = []
    soft: list[str] = []
    if not section:
        return {"blocked_by": blocked_by, "blocks": blocks, "soft_blocked_by": soft}

    for line in section.group(1).splitlines():
        m = re.match(r"\|\s*(APP-\d{3})\s*\|\s*(.+?)\s*\|", line.strip())
        if not m:
            continue
        other = m.group(1).upper()
        rel = m.group(2).lower()
        if "blocks this" in rel or "blocked by" in rel and "this ticket" in rel:
            blocked_by.append(other)
        elif "this ticket blocks" in rel or "unblocks" in rel:
            blocks.append(other)
        elif "may block" in rel or "should" in rel:
            soft.append(other)
        elif re.search(r"before", rel):
            blocked_by.append(other)

    # APP-006–APP-011 style ranges in relationship cell
    for line in section.group(1).splitlines():
        m = re.match(r"\|\s*(APP-\d{3}(?:–APP-\d{3})?)\s*\|", line.strip())
        if not m:
            continue
        cell = m.group(1)
        rng = re.match(r"APP-(\d{3})–APP-(\d{3})", cell)
        if rng:
            start, end = int(rng.group(1)), int(rng.group(2))
            rel_line = line.lower()
            targets = [f"APP-{i:03d}" for i in range(start, end + 1)]
            if "block" in rel_line or "before" in rel_line:
                soft.extend(targets)

    return {
        "blocked_by": sorted(set(blocked_by)),
        "blocks": sorted(set(blocks)),
        "soft_blocked_by": sorted(set(soft)),
    }


def iter_backlog_tickets() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(BACKLOG_DIR.glob("app-*.md")):
        fields = parse_ticket_fields(path)
        tid = fields.get("id", "")
        if not TICKET_ID_RE.match(tid):
            continue
        deps = parse_dependencies(path)
        rows.append(
            {
                "id": tid,
                "title": fields.get("title", ""),
                "type": fields.get("type", ""),
                "priority": fields.get("priority", "P2"),
                "status": fields.get("status", ""),
                "domain_spec": fields.get("domain_spec", ""),
                "path": normalize_path(str(path.relative_to(PROJECT_ROOT))),
                "blocked_by": deps["blocked_by"],
                "blocks": deps["blocks"],
                "soft_blocked_by": deps["soft_blocked_by"],
            }
        )
    return rows


def search_tickets(
    *,
    status: str | None = None,
    priority: str | None = None,
    query: str | None = None,
    open_only: bool = False,
    pickable_only: bool = False,
) -> list[dict]:
    """Search backlog tickets.

    ``open_only`` / ``pickable_only``: only ``open`` (excludes in_progress, done, cancelled).
    Dev-team uses this when auto-selecting new work — never pick closed or in-flight tickets.
    """
    rows = iter_backlog_tickets()
    out: list[dict] = []
    q = (query or "").lower()
    for row in rows:
        if (open_only or pickable_only) and row["status"] not in PICKABLE_STATUSES:
            continue
        if status and row["status"] != status:
            continue
        if priority and row["priority"] != priority:
            continue
        if q and q not in row["title"].lower() and q not in row["id"].lower():
            if q not in row.get("path", "").lower():
                continue
        out.append(row)
    out.sort(
        key=lambda r: (
            PRIORITY_ORDER.get(r.get("priority", "P2"), 9),
            r.get("id", ""),
        )
    )
    return out


def ticket_status_map() -> dict[str, str]:
    return {r["id"]: r["status"] for r in iter_backlog_tickets()}


def compute_schedule(ticket_ids: list[str]) -> dict:
    """Dependency-aware implementation waves among selected tickets."""
    meta = {r["id"]: r for r in iter_backlog_tickets()}
    ids = sorted({t.upper() for t in ticket_ids if TICKET_ID_RE.match(t.upper())})
    status = ticket_status_map()
    blocked_by: dict[str, list[str]] = {}
    edges: list[dict] = []

    for tid in ids:
        path = find_ticket_file(tid)
        if not path:
            continue
        hard = [d for d in parse_dependencies(path)["blocked_by"] if d in ids]
        blocked_by[tid] = hard
        for dep in hard:
            edges.append({"from": dep, "to": tid, "type": "blocks"})

    resolved = {tid for tid, st in status.items() if st == "done"}
    remaining = set(ids)
    impl_waves: list[dict] = []

    def prio(t: str) -> tuple[int, str]:
        return (PRIORITY_ORDER.get(meta.get(t, {}).get("priority", "P2"), 9), t)

    while remaining:
        ready = sorted(
            [t for t in remaining if all(d in resolved for d in blocked_by.get(t, []))],
            key=prio,
        )
        if not ready:
            tid = min(remaining, key=prio)
            impl_waves.append(
                {
                    "parallel": [tid],
                    "note": "dependency cycle or external blocker — verify ## Dependencies",
                }
            )
            resolved.add(tid)
            remaining.discard(tid)
            continue
        impl_waves.append({"parallel": ready, "note": ""})
        resolved.update(ready)
        remaining -= set(ready)

    warnings: list[str] = []
    for tid in ids:
        path = find_ticket_file(tid)
        if not path:
            continue
        for dep in parse_dependencies(path)["blocked_by"]:
            if dep not in ids and status.get(dep) != "done":
                warnings.append(
                    f"{tid} blocked_by {dep} — {dep} not done (add to batch or finish {dep} first)"
                )

    return {
        "selected": ids,
        "edges": edges,
        "blocked_by": blocked_by,
        "impl_waves": impl_waves,
        "warnings": warnings,
    }


def impl_stage_allowed(ticket_id: str) -> tuple[bool, str]:
    """Stage 4+ only when hard dependencies are done."""
    tid = ticket_id.upper()
    status = ticket_status_map()
    path = find_ticket_file(tid)
    if not path:
        return False, f"ticket not found: {tid}"
    for dep in parse_dependencies(path)["blocked_by"]:
        if status.get(dep) != "done":
            return False, f"implementation blocked until {dep} is done"
    return True, ""


def select_ticket_batch(
    ticket_ids: list[str],
    *,
    max_count: int = MAX_BATCH_SIZE,
) -> tuple[list[str], list[str]]:
    """Pick up to max_count tickets by priority respecting in-batch deps."""
    ids = [t.upper() for t in ticket_ids if TICKET_ID_RE.match(t.upper())]
    errors: list[str] = []
    if len(ids) > max_count:
        errors.append(f"truncated to {max_count} tickets (max parallel batch)")
        ids = ids[:max_count]
    status = ticket_status_map()
    candidates = [t for t in ids if status.get(t) in PICKABLE_STATUSES]
    # Sort by priority then id
    meta = {r["id"]: r for r in iter_backlog_tickets()}
    candidates.sort(
        key=lambda t: (PRIORITY_ORDER.get(meta.get(t, {}).get("priority", "P2"), 9), t)
    )
    return candidates, errors


def path_matches_pattern(path: str, pattern: str) -> bool:
    path = normalize_path(path)
    pattern = normalize_path(pattern)
    if pattern.endswith("/"):
        return path.startswith(pattern) or fnmatch.fnmatch(path, pattern.rstrip("/") + "/**")
    if "*" in pattern or "?" in pattern:
        return fnmatch.fnmatch(path, pattern)
    if path == pattern:
        return True
    return path.startswith(pattern + "/")


def is_always_allowed(path: str) -> bool:
    path = normalize_path(path)
    if path in ALWAYS_ALLOWED_FILES:
        return True
    for prefix in ALWAYS_ALLOWED_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def requires_ticket(path: str) -> bool:
    path = normalize_path(path)
    if is_always_allowed(path):
        return False
    if path.startswith("app/"):
        return True
    tickets = load_active_tickets()
    if not tickets:
        return path.startswith("play/") or path.startswith("build/")
    for active in tickets:
        ticket_rel = active.get("ticket_path", "")
        if not ticket_rel:
            continue
        ticket_path = PROJECT_ROOT / ticket_rel
        if not ticket_path.exists():
            continue
        for pattern in parse_expected_files(ticket_path):
            if path_matches_pattern(path, pattern):
                return False
    return path.startswith("play/") or path.startswith("build/")


def path_allowed(path: str) -> tuple[bool, str]:
    path = normalize_path(path)
    if is_always_allowed(path):
        return True, ""

    active = load_active_ticket()
    if not path.startswith("app/") and not path.startswith("play/") and not path.startswith("build/"):
        return True, ""

    tickets = load_active_tickets()
    if path.startswith("app/"):
        if not tickets:
            return False, (
                f"Edit to `{path}` blocked: no active backlog ticket. "
                f"Claim: `python tmp/backlog/claim_ticket.py claim-batch APP-XXX ...`"
            )
        for active in tickets:
            ticket_rel = active.get("ticket_path", "")
            ticket_path = PROJECT_ROOT / ticket_rel if ticket_rel else None
            if not ticket_path or not ticket_path.exists():
                continue
            fields = parse_ticket_fields(ticket_path)
            if fields.get("status") not in ACTIVE_STATUSES:
                continue
            return True, ""
        ids = ", ".join(t.get("id", "") for t in tickets)
        return (
            False,
            f"No active open/in_progress ticket in batch ({ids}) for app/ edits.",
        )

    if requires_ticket(path):
        if not tickets:
            return False, (
                f"Edit to `{path}` blocked: claim a backlog ticket whose Expected files include this path."
            )
        for active in tickets:
            ticket_rel = active.get("ticket_path", "")
            ticket_path = PROJECT_ROOT / ticket_rel if ticket_rel else None
            if ticket_path and ticket_path.exists():
                allowed_patterns = parse_expected_files(ticket_path)
                if any(path_matches_pattern(path, p) for p in allowed_patterns):
                    return True, ""
        return False, (
            f"Edit to `{path}` not listed in any active batch ticket Expected files. Update the ticket first."
        )

    return True, ""


def append_ticket_note(ticket_path: Path, note: str) -> None:
    text = ticket_path.read_text(encoding="utf-8")
    if note in text:
        return
    if "## Notes" in text:
        text = text.replace(
            "## Notes\n\n_Add implementation notes",
            f"## Notes\n\n{note}\n\n_Add implementation notes",
            1,
        )
    else:
        text = text.rstrip() + f"\n\n## Notes\n\n{note}\n"
    ticket_path.write_text(text, encoding="utf-8")


def list_in_progress_tickets() -> list[dict]:
    rows = []
    for path in sorted(BACKLOG_DIR.glob("app-*.md")):
        fields = parse_ticket_fields(path)
        if fields.get("status") == "in_progress":
            rows.append(
                {
                    "id": fields.get("id", ""),
                    "title": fields.get("title", ""),
                    "path": normalize_path(str(path.relative_to(PROJECT_ROOT))),
                }
            )
    return rows
