#!/usr/bin/env python3
"""Cursor hooks: enforce dev-team implementation lock and shell safety."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Project root = parent of .cursor/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = PROJECT_ROOT / ".cursor" / "skills" / "dev-team" / "scripts"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from dev_team.guards import assert_repo_edit_allowed, legacy_session_present  # noqa: E402
from dev_team.human_gate import shell_gate_deny_reason  # noqa: E402
from dev_team.session import SessionStore  # noqa: E402


def _read_stdin_json() -> dict:
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}
    return {}


def _active_session(store: SessionStore):
    if legacy_session_present(store):
        return None, "legacy session at .dev-team/session.json — run reset"
    work = store.work
    if not work:
        return None, "no active dev-team work"
    session = store.load()
    if session.state in ("IDLE", "DONE", "ABORTED"):
        return None, f"session {session.state}"
    return session, ""


def hook_shell() -> int:
    data = _read_stdin_json()
    command = data.get("command", data.get("cmd", ""))
    if not command:
        return 0
    if " && " in command and sys.platform == "win32":
        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": "PowerShell does not support &&. Use ; or separate commands.",
                    "agent_message": "Use: Set-Location <path>; python .cursor\\skills\\dev-team\\scripts\\dev_team_cli.py ...",
                }
            )
        )
        return 2

    store = SessionStore(PROJECT_ROOT)
    deny = shell_gate_deny_reason(store, command)
    if deny:
        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": deny,
                    "agent_message": (
                        "Wait for the human to approve in chat (hook records gate-acks.jsonl), "
                        "then run the CLI command. Run: python .cursor/skills/dev-team/scripts/dev_team_cli.py suggest"
                    ),
                }
            )
        )
        return 2
    return 0


def hook_file_edit() -> int:
    data = _read_stdin_json()
    paths: list[str] = []
    for key in ("file_path", "path", "filePath"):
        if data.get(key):
            paths.append(str(data[key]))
    if "edits" in data and isinstance(data["edits"], list):
        for edit in data["edits"]:
            if isinstance(edit, dict) and edit.get("path"):
                paths.append(str(edit["path"]))
    if not paths:
        return 0

    store = SessionStore(PROJECT_ROOT)
    session, skip = _active_session(store)
    if session is None:
        return 0

    denied: list[str] = []
    for p in paths:
        rel = str(p).replace("\\", "/").lower()
        if "gate-acks.jsonl" in rel or ".gate-secret" in rel:
            denied.append(f"{p}: gate acknowledgments cannot be edited by the agent")
            continue
        file_path = Path(p)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path
        allowed, reason = assert_repo_edit_allowed(PROJECT_ROOT, file_path, session, store)
        if not allowed:
            denied.append(f"{p}: {reason}")

    if denied:
        msg = "dev-team implementation_lock: " + "; ".join(denied)
        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": msg,
                    "agent_message": (
                        "Repo edits are blocked until approve spec. "
                        "Write only under .dev-team/works/<slug>/artifacts/. "
                        "Run: python .cursor/skills/dev-team/scripts/dev_team_cli.py check"
                    ),
                }
            )
        )
        return 2
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "shell":
        return hook_shell()
    if mode in ("file-edit", "file"):
        return hook_file_edit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
