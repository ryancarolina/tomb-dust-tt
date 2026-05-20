#!/usr/bin/env python3
"""Inject active Tomb Dust GM session context from tomb_gm CLI status JSON."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLAY_DIR = PROJECT_ROOT / "play"
ACTIVE_PATH = PROJECT_ROOT / "play" / "workspace" / ".local" / "active.json"
CLI_BASE = "cd play && python -m tomb_gm --workspace workspace"


def _run_tomb_gm(command: str) -> dict[str, Any] | None:
    proc = subprocess.run(
        [sys.executable, "-m", "tomb_gm", "--workspace", "workspace", command],
        capture_output=True,
        text=True,
        cwd=str(PLAY_DIR),
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def _active_session_context() -> str | None:
    if not ACTIVE_PATH.exists():
        return None

    status = _run_tomb_gm("status")
    if not status or not status.get("ok"):
        return None

    check = _run_tomb_gm("check") or {}
    suggest = _run_tomb_gm("suggest") or {}

    lines = [
        "## Tomb Dust GM session active",
        f"- **Awaiting:** `{status.get('awaiting', 'SETUP')}`",
    ]

    active = status.get("active")
    if active:
        slug = active.get("campaign_slug") or active.get("campaign") or ""
        if slug:
            lines.append(f"- **Campaign:** `{slug}`")
        session_id = active.get("session_id")
        if session_id:
            lines.append(f"- **Session:** `{session_id}`")

    party = status.get("party")
    if party:
        address = party.get("address")
        if address:
            lines.append(f"- **Location:** `{address}`")
        phase = party.get("phase")
        if phase:
            lines.append(f"- **Phase:** `{phase}`")
        mode = party.get("mode")
        if mode:
            lines.append(f"- **Mode:** `{mode}`")
        site_id = party.get("site_id")
        if site_id:
            lines.append(f"- **Site:** `{site_id}`")
        clocks = party.get("clocks") or {}
        if clocks:
            clock_bits = [f"{name} {value}" for name, value in clocks.items()]
            lines.append(f"- **Clocks:** {', '.join(clock_bits)}")

    combat = status.get("combat")
    if combat:
        lines.append(
            f"- **Combat:** round {combat.get('round', '?')}, "
            f"turn {combat.get('turn_index', '?')}"
        )
    else:
        lines.append("- **Combat:** no")

    roster = status.get("roster") or []
    if roster:
        bits = [
            f"P{entry.get('slot', '?')} {entry.get('display_name', '?')} "
            f"({entry.get('hp', '?')})"
            for entry in roster
        ]
        lines.append(f"- **Roster:** {', '.join(bits)}")

    if check.get("blocked"):
        lines.append("- **Blocked:** true")
        blockers = check.get("blockers") or []
        if blockers:
            msgs = [b.get("message", str(b)) for b in blockers]
            lines.append(f"- **Blockers:** {'; '.join(msgs)}")

    if suggest.get("stop"):
        lines.append("- **STOP:** resolve blockers before advancing play.")

    lines.append(f"- **Run first:** `{CLI_BASE} status` then `{CLI_BASE} check`")
    if suggest.get("commands"):
        lines.append("- **Suggested next commands:**")
        for cmd in suggest["commands"][:5]:
            lines.append(f"  - `{cmd}`")
    prompts = suggest.get("prompts") or []
    if prompts:
        lines.append(f"- **Prompt:** {prompts[0]}")

    lines.append("- **Play:** users run the PyGame app (`app/main.py`) — do NOT suggest `@tomb-gm` or CLI for playing.")
    lines.append("- **CLI here is developer/debug only** — not player instructions.")
    return "\n".join(lines)


def main() -> int:
    session_ctx = _active_session_context()
    if session_ctx:
        print(json.dumps({"additional_context": session_ctx}))
    else:
        print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
