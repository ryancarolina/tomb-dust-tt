#!/usr/bin/env python3
"""Cursor hooks: enforce backlog ticket claiming for app/ and scoped edits."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR.parents[1] / "tmp" / "backlog"))

from backlog_ticket_lib import (  # noqa: E402
    PROJECT_ROOT,
    load_active_batch,
    load_active_ticket,
    list_in_progress_tickets,
    normalize_path,
    path_allowed,
)
from pipeline_manifest import (  # noqa: E402
    active_dev_team_manifest,
    format_missing_gates,
    load_manifest,
    stop_incomplete,
    stop_incomplete_lanes,
    subagent_impl_blocked,
)

TICKET_ID_IN_TEXT = re.compile(r"APP-\d{3}")


def _read_stdin() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _emit(payload: dict) -> None:
    print(json.dumps(payload))


def _extract_edit_path(data: dict) -> str | None:
    tool_input = data.get("tool_input") or data.get("arguments") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            return None
    if not isinstance(tool_input, dict):
        return None
    for key in ("path", "file_path", "target_file", "filePath"):
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            return normalize_path(val)
    return None


def _focus_manifest() -> dict | None:
    active = load_active_ticket()
    if active and active.get("run_dir"):
        manifest = load_manifest(PROJECT_ROOT / normalize_path(active["run_dir"]))
        if manifest:
            return manifest
    return active_dev_team_manifest()


def handle_session_start(_data: dict) -> int:
    lines = [
        "## Backlog ticket enforcement",
        "- **No ticket, no change** under `app/` (and scoped `play/` / `build/` paths).",
        "- Claim: `python tmp/backlog/claim_ticket.py claim-batch APP-XXX ...` (≤3) or single `APP-XXX --task <name>`",
        "- Search: `python tmp/backlog/claim_ticket.py search --open-only`",
        "- Schedule: `python tmp/backlog/claim_ticket.py schedule APP-XXX APP-YYY`",
        "- Session: `tmp/.active-batch.json` + `tmp/.active-ticket.json` (focus)",
        "- Index: `tmp/backlog/README.md` · dev-team runs: `tmp/backlog/runs/`",
    ]
    batch = load_active_batch()
    active = load_active_ticket()
    if batch and batch.get("tickets"):
        lines.append(f"- **Active batch ({len(batch['tickets'])}/3):**")
        for row in batch["tickets"]:
            lines.append(f"  - `{row.get('id')}` focus={'*' if row.get('id') == batch.get('focus') else ''}")
        if batch.get("schedule", {}).get("impl_waves"):
            lines.append(
                "- **Impl waves:** "
                + ", ".join("/".join(w.get("parallel", [])) for w in batch["schedule"]["impl_waves"])
            )
    elif active:
        lines.append(f"- **Active ticket:** `{active.get('id')}` → `{active.get('ticket_path')}`")
        if active.get("run_dir"):
            lines.append(f"- **Run folder:** `{active.get('run_dir')}`")
    else:
        lines.append("- **Active ticket:** none — claim before editing `app/`")

    manifest = _focus_manifest()
    if manifest and manifest.get("dev_team"):
        stage = manifest.get("stage", "claim")
        lines.append(f"- **Dev-team stage:** `{stage}` · manifest `{manifest.get('ticket_id')}`")
        missing = format_missing_gates(manifest)
        if missing:
            lines.append(f"- **Missing gates:** {', '.join(missing)}")

    in_prog = list_in_progress_tickets()
    if in_prog:
        lines.append("- **In progress tickets:**")
        for row in in_prog[:8]:
            lines.append(f"  - `{row['id']}` {row['title']}")
    _emit({"additional_context": "\n".join(lines)})
    return 0


def handle_pre_tool_use(data: dict) -> int:
    tool_name = data.get("tool_name") or data.get("tool") or ""
    if tool_name not in {"Write", "StrReplace", "ApplyPatch", "EditNotebook"}:
        _emit({"permission": "allow"})
        return 0

    path = _extract_edit_path(data)
    if not path:
        _emit({"permission": "allow"})
        return 0

    ok, reason = path_allowed(path)
    if ok:
        _emit({"permission": "allow"})
        return 0

    _emit(
        {
            "permission": "deny",
            "user_message": reason,
            "agent_message": (
                f"{reason} Then retry the edit. "
                "For @dev-team work, complete Stage 0 (claim ticket + run folder) first."
            ),
        }
    )
    return 0


def handle_subagent_start(data: dict) -> int:
    subagent_type = data.get("subagent_type") or data.get("type") or ""
    if subagent_type == "explore":
        _emit({"permission": "allow"})
        return 0

    prompt = (
        data.get("prompt")
        or data.get("task")
        or data.get("user_message")
        or data.get("message")
        or ""
    )
    if not isinstance(prompt, str):
        prompt = str(prompt)

    manifest = _focus_manifest()
    blocked, reason = subagent_impl_blocked(prompt, manifest)
    if blocked:
        _emit({"permission": "deny", "user_message": reason, "agent_message": reason})
        return 0

    batch = load_active_batch()
    active = load_active_ticket()
    ticket_in_prompt = TICKET_ID_IN_TEXT.search(prompt)

    if batch or active or ticket_in_prompt:
        _emit({"permission": "allow"})
        return 0

    msg = (
        "Subagent blocked: prompt must include backlog ticket ID (APP-XXX) and "
        "parent must claim ticket via `python tmp/backlog/claim_ticket.py APP-XXX --task <name>`."
    )
    _emit({"permission": "deny", "user_message": msg})
    return 0


def handle_stop(_data: dict) -> int:
    batch = load_active_batch()
    active = load_active_ticket()

    incomplete_lanes = stop_incomplete_lanes()
    if incomplete_lanes:
        if len(incomplete_lanes) == 1:
            tid, missing = incomplete_lanes[0]
            msg = (
                f"Dev-team pipeline incomplete for `{tid}`: "
                f"missing {', '.join(missing)}. "
                "Run the missing pipeline stages via Task subagents — do not backfill gates. "
                f"Or waive via `release {tid} --done --waive-pipeline` with user approval."
            )
        else:
            parts = [
                f"`{tid}` ({', '.join(missing)})" for tid, missing in incomplete_lanes
            ]
            msg = (
                "Dev-team batch has uncommitted app/build/play changes with incomplete pipelines: "
                + "; ".join(parts)
                + ". Close each lane through Stages 1–7 (real subagents) or ask the user about waivers."
            )
        _emit({"followup_message": msg})
        return 1

    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        changed = [normalize_path(line) for line in proc.stdout.splitlines() if line.strip()]
    except (subprocess.SubprocessError, OSError):
        changed = []

    app_touched = [p for p in changed if p.startswith("app/")]
    if app_touched and not active and not batch:
        files = ", ".join(f"`{p}`" for p in app_touched[:5])
        _emit(
            {
                "followup_message": (
                    f"Backlog gate: {files} changed without an active ticket in "
                    "`tmp/.active-ticket.json`. Claim or create a ticket, sync domain spec, "
                    "then mark ticket done."
                )
            }
        )
        return 0

    _emit({})
    return 0


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    data = _read_stdin()
    handlers = {
        "sessionStart": handle_session_start,
        "preToolUse": handle_pre_tool_use,
        "subagentStart": handle_subagent_start,
        "stop": handle_stop,
    }
    handler = handlers.get(event)
    if not handler:
        _emit({})
        return 0
    return handler(data)


if __name__ == "__main__":
    raise SystemExit(main())
