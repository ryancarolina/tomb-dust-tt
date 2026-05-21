"""Game session logger — writes all input/output to timestamped log files."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log_path() -> Path:
    _ensure_log_dir()
    date_str = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"session-{date_str}.jsonl"


def log_entry(entry_type: str, data: dict | str):
    """Append a JSONL entry to today's log file."""
    entry = {
        "ts": datetime.now().isoformat(),
        "type": entry_type,
        "data": data,
    }
    try:
        with _log_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


def log_player_input(text: str):
    log_entry("player_input", {"text": text})


def log_gm_narration(narration: str):
    log_entry("gm_narration", {"text": narration})


def log_creation_drift(data: dict):
    """Structured alert when narration status disagrees with engine creation state."""
    log_entry("creation_drift", data)


def log_creation_step(data: dict):
    """Per-turn creation FSM snapshot for debugging drift."""
    log_entry("creation_step", data)


def log_creation_advanced(data: dict):
    """Successful creation FSM transition after set_creation_choice."""
    log_entry("creation_advanced", data)


def log_creation_finalize(data: dict):
    """Engine status snapshot after character_create / finalize."""
    log_entry("creation_finalize", data)


def parse_narration_status_line(narration: str) -> dict[str, str | None]:
    """Extract Phase and Awaiting from bracket status lines in GM narration."""
    import re

    phase = None
    awaiting = None
    phase_m = re.search(r"Phase:\s*([^|\]]+)", narration, re.I)
    if phase_m:
        phase = phase_m.group(1).strip()
    awaiting_m = re.search(r"Awaiting:\s*([^|\]]+)", narration, re.I)
    if awaiting_m:
        awaiting = awaiting_m.group(1).strip()
    return {"phase": phase, "awaiting": awaiting}


def log_tool_call(name: str, args: dict, result: dict):
    log_entry("tool_call", {"name": name, "args": args, "result": result})


def log_llm_request(messages_count: int, model: str, depth: int):
    log_entry("llm_request", {"messages": messages_count, "model": model, "depth": depth})


def log_llm_response(content: str, tool_calls: list, finish_reason: str):
    log_entry("llm_response", {
        "content_length": len(content),
        "content_preview": content[:300],
        "tool_calls": [tc["function"]["name"] for tc in tool_calls] if tool_calls else [],
        "finish_reason": finish_reason,
    })


def log_error(context: str, error: str):
    log_entry("error", {"context": context, "error": error})


def log_narration_verify_fail(data: dict):
    log_entry("narration_verify_fail", data)


def log_narration_verify_pass(data: dict):
    log_entry("narration_verify_pass", data)


def log_narration_verify_exhausted(data: dict):
    log_entry("narration_verify_exhausted", data)


def log_llm_truncation_recovery(data: dict):
    log_entry("llm_truncation_recovery", data)
