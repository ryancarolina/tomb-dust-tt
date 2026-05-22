"""APP-080: normalize and validate LLM tool args before bridge dispatch."""

from __future__ import annotations

import sqlite3
from copy import deepcopy

import pytest

from gm.tool_args import (
    _coerce_int,
    _strip_tool_markup,
    normalize_tool_args,
    validate_tool_args,
)

# Session 2026-05-20 Holt quest regression — corrupted importance with tool markup bleed.
HOLT_CORRUPTED_IMPORTANCE = (
    '4</importance>\n</invoke>\n<invoke name="enter_dungeon">'
    '<parameter name="site_address">32-C-UG-1</parameter></invoke>'
)

HOLT_REMEMBER_FACT_ARGS = {
    "fact": (
        "Marshal Holt tasked Fatty with retrieving his brother's signet ring "
        "from Breley Undercrypt."
    ),
    "entities": ["Marshal Holt", "Breley Undercrypt", "Holt signet ring"],
    "importance": HOLT_CORRUPTED_IMPORTANCE,
}


def _dispatch_like_llm_loop(orchestrator, tool_name: str, raw_args: dict) -> dict:
    """Post-WS2 contract: normalize and validate before _execute_tool."""
    args = normalize_tool_args(tool_name, raw_args)
    err = validate_tool_args(tool_name, args)
    if err:
        return {"ok": False, "error": err}
    return orchestrator._execute_tool(tool_name, args)


# --- Unit: helpers ---


def test_coerce_int_markup_prefix():
    assert _coerce_int(HOLT_CORRUPTED_IMPORTANCE, 3, min_v=1, max_v=5) == 4


def test_coerce_int_invalid():
    assert _coerce_int("abc", 3, min_v=1, max_v=5) == 3


def test_strip_tool_markup_truncates_invoke_tail():
    raw = "keep</invoke>\n<invoke name=\"enter_dungeon\">tail"
    stripped = _strip_tool_markup(raw)
    assert stripped == "keep"
    assert "<invoke" not in stripped
    assert "tail" not in stripped


# --- Unit: normalize ---


def test_normalize_remember_fact_corrupted_importance():
    out = normalize_tool_args("remember_fact", HOLT_REMEMBER_FACT_ARGS)
    assert isinstance(out["importance"], int)
    assert out["importance"] == 4
    assert out["entities"] == [
        "Marshal Holt",
        "Breley Undercrypt",
        "Holt signet ring",
    ]
    assert "Marshal Holt tasked Fatty" in out["fact"]


def test_normalize_remember_fact_no_typeerror_via_semantic():
    from tomb_gm.services.memory.semantic import remember

    args = normalize_tool_args("remember_fact", HOLT_REMEMBER_FACT_ARGS)
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE memories (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          campaign_slug TEXT NOT NULL,
          fact TEXT NOT NULL,
          entities_json TEXT NOT NULL DEFAULT '[]',
          address TEXT,
          importance INTEGER NOT NULL DEFAULT 3,
          source_event_id INTEGER,
          superseded_by INTEGER,
          created_at TEXT NOT NULL,
          last_recalled_at TEXT
        );
        """
    )
    memory_id = remember(
        conn,
        "holt-test",
        args["fact"],
        entities=args["entities"],
        importance=args["importance"],
        embed=False,
    )
    assert memory_id >= 1
    row = conn.execute(
        "SELECT importance FROM memories WHERE id = ?", (memory_id,)
    ).fetchone()
    assert row is not None
    assert row[0] == 4


def test_normalize_memory_recall_top_k_string():
    out = normalize_tool_args("memory_recall", {"query": "Holt quest", "top_k": "5"})
    assert out["top_k"] == 5
    assert out["query"] == "Holt quest"
    assert "top" not in out


def test_normalize_memory_recall_legacy_top():
    out = normalize_tool_args("memory_recall", {"query": "ring", "top": "3"})
    assert out["top_k"] == 3
    assert "top" not in out


def test_normalize_memory_recall_top_k_wins_over_top():
    out = normalize_tool_args(
        "memory_recall",
        {"query": "ring", "top": "9", "top_k": "2"},
    )
    assert out["top_k"] == 2
    assert "top" not in out


def test_normalize_fortune_spend_drops_amount():
    out = normalize_tool_args(
        "fortune_spend",
        {"character_id": "pc-1", "amount": "2"},
    )
    assert out == {"character_id": "pc-1"}


def test_normalize_enter_dungeon_site_id_alias():
    out = normalize_tool_args("enter_dungeon", {"site_id": "32-C-UG-1"})
    assert out == {"site_address": "32-C-UG-1"}
    assert "site_id" not in out


def test_normalize_clock_tick_segments_string():
    out = normalize_tool_args(
        "clock_tick",
        {"clock": "delve", "segments": "2"},
    )
    assert out["segments"] == 2
    assert out["clock"] == "delve"


# --- Unit: validate (SPEC-001) ---


def test_validate_remember_fact_missing_fact():
    args = normalize_tool_args("remember_fact", {})
    assert validate_tool_args("remember_fact", args) == "fact required"


def test_validate_memory_recall_missing_query():
    args = normalize_tool_args("memory_recall", {})
    assert validate_tool_args("memory_recall", args) == "query required"


def test_validate_fortune_spend_missing_character_id():
    args = normalize_tool_args("fortune_spend", {})
    assert validate_tool_args("fortune_spend", args) == "character_id required"


def test_normalize_start_combat_string_spec():
    out = normalize_tool_args(
        "start_combat",
        {"monster_specs": "grave-ghoul:1", "include_party": "false"},
    )
    assert out["monster_specs"] == ["grave-ghoul:1"]
    assert out["include_party"] is False


def test_validate_start_combat_empty_specs():
    args = normalize_tool_args("start_combat", {"monster_specs": []})
    assert validate_tool_args("start_combat", args) == "monster_specs required"


def test_validate_start_combat_missing_specs():
    args = normalize_tool_args("start_combat", {})
    assert validate_tool_args("start_combat", args) == "monster_specs required"


# --- Integration ---


def test_execute_tool_remember_fact_corrupted_importance_ok(orchestrator):
    assert orchestrator.setup_new_game().get("ok") is True
    orchestrator.creation.active = False
    orchestrator.combat.active = False
    raw = deepcopy(HOLT_REMEMBER_FACT_ARGS)
    result = _dispatch_like_llm_loop(orchestrator, "remember_fact", raw)
    assert result.get("ok") is True
    assert isinstance(result.get("memory_id"), int)
