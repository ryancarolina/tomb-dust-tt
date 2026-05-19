from __future__ import annotations

from typing import Any


def build_suggest(
    status: dict[str, Any],
    check: dict[str, Any],
    *,
    pending_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if pending_gate:
        return {
            "ok": True,
            "awaiting": "HUMAN_GATE",
            "stop": True,
            "gate": pending_gate,
            "commands": ["gate resolve --id <id> --approve", "gate resolve --id <id> --reject"],
            "prompts": [
                f"Resolve gate {pending_gate.get('gate_type')}: host must approve or reject in chat"
            ],
        }
    if check.get("blocked"):
        return {
            "ok": True,
            "awaiting": "BLOCKED",
            "stop": True,
            "blockers": check.get("blockers", []),
            "commands": ["check"],
            "prompts": ["Resolve blockers before play"],
            "gate": None,
        }

    awaiting = status.get("awaiting", "SETUP")
    commands = ["status", "check", "suggest"]
    prompts: list[str] = []
    stop = False
    gate = None

    if awaiting == "SETUP":
        commands.extend(["init", "campaign new", "session start"])
        prompts.append("No active play session — create or resume a campaign")
    elif awaiting == "SESSION_ENDED":
        commands.extend(["session resume", "session start", "memory recap"])
        prompts.append("Last session ended — resume or start new")
    elif awaiting == "CHARACTER_CREATION":
        commands.extend(
            [
                "character create --full --race <id> ...",
                "roll attributes",
                "roster set --slot 1 --id <char>",
            ]
        )
        prompts.append("GM rolls all dice — never ask players to roll")
        prompts.append(
            "Use character create --full --race human --human-bonus STR,INT for full canon pipeline"
        )
    elif awaiting == "ROSTER_SETUP":
        commands.extend(["character list", "roster set --slot N --id <char>"])
        prompts.append("Assign created characters to slots 1–4 with roster set")
    elif awaiting == "PLAYER_ACTIONS":
        commands.extend(
            [
                "beat",
                "world where",
                "world exits",
                "narrate push --file .local/latest-narration.txt",
                "speak --last",
                "speak --stop",
            ]
        )
        prompts.append("Collect [P1]…[P4] actions then run beat")
        prompts.append(
            "After narration: write .local/latest-narration.txt then narrate push --file (required unless tts.mode text_only)"
        )
    elif awaiting == "BLOCKED":
        stop = True

    return {
        "ok": True,
        "awaiting": awaiting,
        "stop": stop,
        "commands": commands,
        "prompts": prompts,
        "gate": gate,
        "status": status.get("active"),
    }
