#!/usr/bin/env python3
"""Record human gate approvals and inject active dev-team session context."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = PROJECT_ROOT / ".cursor" / "skills" / "dev-team" / "scripts"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from dev_team.human_approval import process_user_prompt  # noqa: E402
from dev_team.machine import DevTeamMachine  # noqa: E402
from dev_team.session import SessionStore  # noqa: E402


def _extract_prompt(data: dict) -> str:
    for key in ("prompt", "text", "message", "content", "userMessage", "user_message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _active_session_context(store: SessionStore) -> str | None:
    if not store.work:
        return None
    session = store.load()
    if session.state in ("IDLE", "DONE", "ABORTED"):
        return None

    machine = DevTeamMachine(store)
    status = machine.status()
    suggestion = machine.suggest()
    cli = "python .cursor/skills/dev-team/scripts/dev_team_cli.py --workspace ."

    lines = [
        "## Dev-team session active",
        f"- **State:** `{status['state']}`",
        f"- **Work:** `{status.get('work_slug', '')}`",
        f"- **Awaiting:** {status.get('awaiting', '')}",
        f"- **Blocked:** {status.get('blocked', False)}",
    ]
    if status.get("blockers"):
        lines.append(f"- **Blockers:** {'; '.join(status['blockers'])}")
    if status.get("human_gate_pending"):
        lines.append(
            f"- **Human gate:** reply `approve {status['human_gate_pending']}` in chat before CLI approve"
        )
    if suggestion.get("stop"):
        lines.append("- **STOP:** do not advance until the human gate is satisfied.")
    lines.append(f"- **Run first:** `{cli} status` then `{cli} check`")
    if suggestion.get("commands"):
        lines.append("- **Suggested next commands:**")
        for cmd in suggestion["commands"][:5]:
            lines.append(f"  - `{cmd}`")
    lines.append("- Follow `.cursor/skills/dev-team/SKILL.md` (Orchestrator).")
    return "\n".join(lines)


def main() -> int:
    data = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                pass

    prompt = _extract_prompt(data)
    store = SessionStore(PROJECT_ROOT)

    parts: list[str] = []

    session_ctx = _active_session_context(store)
    if session_ctx:
        parts.append(session_ctx)

    if prompt:
        result = process_user_prompt(store, prompt)
        if result.get("recorded"):
            parts.append(
                f"Dev-team recorded your {result.get('action')} "
                f"for state {result.get('state')}. "
                "The orchestrator may now run the matching CLI command."
            )

    if parts:
        print(json.dumps({"additional_context": "\n\n".join(parts)}))
    else:
        print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
