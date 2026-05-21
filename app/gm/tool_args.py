"""Normalize and validate LLM tool arguments before GameBridge dispatch (APP-080)."""

from __future__ import annotations

import re
from typing import Any

_MARKUP_CUT_MARKERS = ("</invoke>", "</parameter>", "<invoke", "<parameter")
_LEADING_INT_RE = re.compile(r"^\s*(\d+)")

_ALLOWED_KEYS: dict[str, frozenset[str]] = {
    "remember_fact": frozenset({"fact", "entities", "importance"}),
    "memory_recall": frozenset({"query", "top_k"}),
    "fortune_spend": frozenset({"character_id"}),
    "clock_tick": frozenset({"clock", "segments"}),
    "enter_dungeon": frozenset({"site_address"}),
    "set_creation_choice": frozenset({"step", "value"}),
    "combat_action": frozenset(
        {"action", "actor_id", "target_id", "weapon_id", "spell_id"}
    ),
}


def _strip_tool_markup(s: str) -> str:
    """Cut at first tool/XML fragment and trim."""
    cut_at = len(s)
    for marker in _MARKUP_CUT_MARKERS:
        idx = s.find(marker)
        if idx != -1 and idx < cut_at:
            cut_at = idx
    if cut_at < len(s):
        s = s[:cut_at]
    return s.strip()


def _coerce_int(value: Any, default: int, *, min_v: int, max_v: int) -> int:
    """Coerce to int; strip markup on strings; invalid values use default; clamp."""
    if isinstance(value, bool):
        return max(min_v, min(max_v, default))
    if isinstance(value, int):
        return max(min_v, min(max_v, value))
    if isinstance(value, float):
        return max(min_v, min(max_v, int(value)))
    if isinstance(value, str):
        cleaned = _strip_tool_markup(value)
        match = _LEADING_INT_RE.match(cleaned)
        if match:
            return max(min_v, min(max_v, int(match.group(1))))
        return max(min_v, min(max_v, default))
    return max(min_v, min(max_v, default))


def _coerce_str(value: Any, default: str = "", *, strip_markup: bool = True) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return _strip_tool_markup(value) if strip_markup else value
    return str(value)


def _coerce_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def _apply_whitelist(tool_name: str, out: dict[str, Any]) -> dict[str, Any]:
    allowed = _ALLOWED_KEYS.get(tool_name)
    if allowed is None:
        return out
    return {key: out[key] for key in allowed if key in out}


def _normalize_remember_fact(args: dict[str, Any]) -> dict[str, Any]:
    out = {
        "fact": _coerce_str(args.get("fact"), "", strip_markup=False),
        "entities": _coerce_str_list(args.get("entities")),
        "importance": _coerce_int(args.get("importance", 3), 3, min_v=1, max_v=5),
    }
    return _apply_whitelist("remember_fact", out)


def _normalize_memory_recall(args: dict[str, Any]) -> dict[str, Any]:
    query = _coerce_str(args.get("query"), "")
    if "top_k" in args:
        top_k = _coerce_int(args.get("top_k"), 5, min_v=1, max_v=10_000)
    elif "top" in args:
        top_k = _coerce_int(args.get("top"), 5, min_v=1, max_v=10_000)
    else:
        top_k = 5
    out = {"query": query, "top_k": top_k}
    return _apply_whitelist("memory_recall", out)


def _normalize_fortune_spend(args: dict[str, Any]) -> dict[str, Any]:
    out = {"character_id": _coerce_str(args.get("character_id"), "")}
    return _apply_whitelist("fortune_spend", out)


def _normalize_clock_tick(args: dict[str, Any]) -> dict[str, Any]:
    out = {
        "clock": _coerce_str(args.get("clock"), ""),
        "segments": _coerce_int(args.get("segments", 1), 1, min_v=1, max_v=100),
    }
    return _apply_whitelist("clock_tick", out)


def _normalize_enter_dungeon(args: dict[str, Any]) -> dict[str, Any]:
    site_address = args.get("site_address")
    site_id = args.get("site_id")
    if not site_address and site_id is not None:
        address = _coerce_str(site_id, "")
    else:
        address = _coerce_str(site_address or site_id or "", "")
    out = {"site_address": address}
    return _apply_whitelist("enter_dungeon", out)


def _normalize_set_creation_choice(args: dict[str, Any]) -> dict[str, Any]:
    out = {
        "step": _coerce_str(args.get("step"), ""),
        "value": _coerce_str(args.get("value"), ""),
    }
    return _apply_whitelist("set_creation_choice", out)


def _normalize_combat_action(args: dict[str, Any]) -> dict[str, Any]:
    allowed = _ALLOWED_KEYS["combat_action"]
    out: dict[str, Any] = {}
    for key in allowed:
        if key in args:
            out[key] = _coerce_str(args[key], "")
    return out


_NORMALIZERS = {
    "remember_fact": _normalize_remember_fact,
    "memory_recall": _normalize_memory_recall,
    "fortune_spend": _normalize_fortune_spend,
    "clock_tick": _normalize_clock_tick,
    "enter_dungeon": _normalize_enter_dungeon,
    "set_creation_choice": _normalize_set_creation_choice,
    "combat_action": _normalize_combat_action,
}


def normalize_tool_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Coerce tool args to bridge-safe types. Never raises."""
    if not isinstance(args, dict):
        raw: dict[str, Any] = {}
    else:
        raw = dict(args)
    normalizer = _NORMALIZERS.get(tool_name)
    if normalizer is None:
        return raw
    try:
        return normalizer(raw)
    except Exception:
        return raw


def validate_tool_args(tool_name: str, args: dict[str, Any]) -> str | None:
    """Return a required-field error string, or None when args are dispatchable."""
    if tool_name == "remember_fact":
        if not _coerce_str(args.get("fact"), "", strip_markup=False).strip():
            return "fact required"
    elif tool_name == "memory_recall":
        if not _coerce_str(args.get("query"), "").strip():
            return "query required"
    elif tool_name == "fortune_spend":
        if not _coerce_str(args.get("character_id"), "").strip():
            return "character_id required"
    elif tool_name == "clock_tick":
        if not _coerce_str(args.get("clock"), "").strip():
            return "clock required"
    elif tool_name == "enter_dungeon":
        if not _coerce_str(args.get("site_address"), "").strip():
            return "site_address required"
    elif tool_name == "set_creation_choice":
        if not _coerce_str(args.get("step"), "").strip():
            return "step required"
        if not _coerce_str(args.get("value"), "").strip():
            return "value required"
    elif tool_name == "combat_action":
        if not _coerce_str(args.get("action"), "").strip():
            return "action required"
        if not _coerce_str(args.get("actor_id"), "").strip():
            return "actor_id required"
    return None
