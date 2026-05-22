"""Game session logger — writes all input/output to timestamped log files."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REDACTED = "[REDACTED]"
_SK_OR_RE = re.compile(r"sk-or-[A-Za-z0-9_-]+", re.I)
_BEARER_RE = re.compile(r"Bearer\s+\S+", re.I)
_SECRET_KEYS = frozenset({"api_key", "authorization", "openrouter_api_key"})

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


def log_exploration_drift(data: dict):
    """Structured alert when stripped exploration prose disagreed with engine status."""
    log_entry("exploration_drift", data)


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


def _redact_string(s: str) -> str:
    s = _SK_OR_RE.sub(REDACTED, s)
    return _BEARER_RE.sub("Bearer " + REDACTED, s)


def redact_secrets(value: Any) -> Any:
    """Recursively redact API keys and bearer tokens; never raises."""
    try:
        if isinstance(value, str):
            return _redact_string(value)
        if isinstance(value, dict):
            out = {}
            for k, v in value.items():
                key_str = str(k)
                if key_str.casefold() in _SECRET_KEYS or key_str == "OPENROUTER_API_KEY":
                    out[k] = REDACTED
                else:
                    out[k] = redact_secrets(v)
            return out
        if isinstance(value, list):
            return [redact_secrets(v) for v in value]
        if isinstance(value, tuple):
            return tuple(redact_secrets(v) for v in value)
        return value
    except Exception:
        return value


def summarize_messages_for_log(messages: list[dict]) -> list[dict]:
    """Compact per-message snapshot for api_error JSONL; never mutates input."""
    summary: list[dict] = []
    for msg in messages:
        try:
            if not isinstance(msg, dict):
                continue
            row: dict[str, Any] = {}
            role = msg.get("role")
            if role is not None:
                row["role"] = role
            content = msg.get("content")
            if isinstance(content, str):
                redacted = redact_secrets(content)
                row["content_len"] = len(content)
                row["content_preview"] = redacted[:200]
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                tc_rows: list[dict] = []
                for tc in tool_calls:
                    try:
                        fn = tc.get("function") or {}
                        name = fn.get("name")
                        args_raw = fn.get("arguments")
                        if isinstance(args_raw, dict):
                            args_str = json.dumps(args_raw)
                        elif isinstance(args_raw, str):
                            args_str = args_raw
                        else:
                            args_str = str(args_raw) if args_raw is not None else ""
                        redacted_args = redact_secrets(args_str)
                        tc_row: dict[str, Any] = {
                            "id": tc.get("id"),
                            "name": name,
                            "arguments_len": len(args_str),
                            "arguments_preview": redacted_args[:120],
                        }
                        tc_rows.append(tc_row)
                    except Exception:
                        continue
                if tc_rows:
                    row["tool_calls"] = tc_rows
            if role == "tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id is not None:
                    row["tool_call_id"] = tool_call_id
            if row:
                summary.append(row)
        except Exception:
            continue
    return summary


def extract_tool_chain(messages: list[dict]) -> list[dict]:
    """Ordered assistant/tool rounds from transcript; never raises."""
    rounds: list[dict] = []
    current: dict | None = None
    for msg in messages:
        try:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role == "assistant":
                tool_calls = msg.get("tool_calls") or []
                if tool_calls:
                    if current is not None:
                        rounds.append(current)
                    current = {
                        "assistant_tool_calls": [
                            {
                                "id": tc.get("id"),
                                "name": (tc.get("function") or {}).get("name"),
                            }
                            for tc in tool_calls
                        ],
                        "tool_results": [],
                    }
            elif role == "tool" and current is not None:
                content = msg.get("content")
                content_len = len(content) if isinstance(content, str) else 0
                current["tool_results"].append({
                    "tool_call_id": msg.get("tool_call_id"),
                    "content_len": content_len,
                })
        except Exception:
            continue
    if current is not None:
        rounds.append(current)
    return rounds


def log_api_error(data: dict) -> None:
    log_entry("api_error", redact_secrets(data))


def log_transcript_400_retry(data: dict) -> None:
    log_entry("transcript_400_retry", redact_secrets(data))
