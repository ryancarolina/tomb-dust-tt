"""Human gate enforcement — chat ack (primary) or test bypass env."""

from __future__ import annotations

import os
import re
from datetime import datetime

from dev_team.human_approval import find_ack
from dev_team.session import SessionStore

HUMAN_ACK_ENV = "DEV_TEAM_HUMAN_ACK"  # tests / human terminal bypass only

GATE_STATE_TO_PHASE = {
    "RESEARCH_GATE": "research",
    "SPEC_GATE": "spec",
    "DEV_GATE": "dev",
    "QA_GATE": "qa",
}


def is_human_operator() -> bool:
    return os.environ.get(HUMAN_ACK_ENV) == "1"


def require_human_operator(
    store: SessionStore,
    command: str,
    *,
    action: str,
    phase: str = "",
    target: str = "",
) -> None:
    from dev_team.human_approval import require_chat_ack

    require_chat_ack(store, command, action=action, phase=phase, target=target)


def shell_command_is_human_only(command: str) -> bool:
    inv = parse_dev_team_cli_invocation(command)
    return inv is not None and inv.get("human_only", False)


def parse_dev_team_cli_invocation(command: str) -> dict | None:
    """Parse a shell command that invokes dev_team_cli. Returns None if not our CLI."""
    lower = command.replace("\\", "/").lower()
    if "dev_team_cli" not in lower:
        return None

    if re.search(r"\bscope\s+confirm\b", lower):
        return {"human_only": True, "action": "scope_confirm"}

    m = re.search(r"\bapprove\s+(research|spec|dev|qa)\b", lower)
    if m:
        return {"human_only": True, "action": "approve", "phase": m.group(1)}

    m = re.search(r"\brevise\s+(research|spec|dev|qa)\b", lower)
    if m:
        return {"human_only": True, "action": "revise", "phase": m.group(1)}

    m = re.search(r"\breject\s+(research|spec|dev)\b", lower)
    if m:
        return {"human_only": True, "action": "reject", "target": m.group(1)}

    return None


def shell_gate_deny_reason(store: SessionStore, command: str) -> str | None:
    """
    If this shell command is a human-only dev_team_cli invocation without a valid chat ack,
    return a deny message. Otherwise return None (allow).
    """
    if is_human_operator():
        return None

    inv = parse_dev_team_cli_invocation(command)
    if not inv or not inv.get("human_only"):
        return None

    if not store.work:
        return None

    session = store.load()
    if session.state in ("IDLE", "DONE", "ABORTED"):
        return None

    action = inv["action"]
    phase = inv.get("phase", "")
    target = inv.get("target", "")

    row = find_ack(store, action=action, phase=phase, target=target)
    if row is not None:
        if action == "scope_confirm":
            proposed_at = session.task_scope_proposed_at
            ack_at = row.get("payload", {}).get("at", "")
            if proposed_at and ack_at:
                try:
                    if datetime.fromisoformat(ack_at) <= datetime.fromisoformat(proposed_at):
                        return (
                            "scope confirm ack must be from a user message after scope propose. "
                            "End your turn after scope propose; wait for confirm scope in chat."
                        )
                except ValueError:
                    pass
        return None

    if action == "scope_confirm":
        hint = "Reply confirm scope in chat, then run scope confirm."
    elif action == "approve":
        hint = f"Reply approve {phase} or lgtm in chat, then run approve {phase}."
    elif action == "revise":
        hint = f"Reply revise {phase}: … in chat, then run revise {phase}."
    else:
        hint = f"Reply reject to {target} in chat, then run reject {target}."

    return (
        f"Human-only dev-team command blocked (no chat ack). {hint} "
        "Do not set DEV_TEAM_HUMAN_ACK in the agent shell."
    )
