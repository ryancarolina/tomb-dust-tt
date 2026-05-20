# Reflection: Dev — APP-068 WS1

**backlog_ticket:** APP-068  
**workstream:** WS1 — NAME→RACE orchestrator fix  
**date:** 2026-05-20

## What shipped

- **NAME success path** (`_handle_creation_response`, step `NAME`): replaced `return self._chain_after_creation_choice("")` with `return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")` so the same turn always runs code-owned race table + `Awaiting: RACE_INPUT` without depending on chain entry matching `step == "RACE"`.
- **Chain fallthrough guard** (`_chain_after_creation_choice`, before clerk-waits default): if `step == "RACE"` and `race` empty, call `_auto_present_race` and return combined narration — belt-and-suspenders for SPELL skip edges, resume, and other callers that reach fallthrough.

## Design choices

- **Left `_auto_present_race` unchanged** — still sets `races_table_shown = True` after `advance()` clears it on NAME→RACE (`creation.py`).
- **Kept existing RACE block** at top of `_chain_after_creation_choice` (~843–846) for non-NAME chain callers; fallthrough guard only catches paths that miss that block.
- **Invalid NAME paths unchanged** — short name, bracket prefix → `None`; equipment confirm / failed execute → `_auto_present_name` error; no race table until valid NAME.
- **No debug logging** — omitted `log_entry("chain_after", ...)` per workstreams unless QA asks post-fix.

## Verification

- Grep: NAME success branch no longer calls `_chain_after_creation_choice("")`.
- Fallthrough guard present immediately before `return prior or "The clerk waits."`.
- Smoke: `pytest tests/test_creation_flow.py::test_full_creation_apprentice_caster -q` — **1 passed** (FSM through finalize; turn-2 race-table assertions deferred to WS2).

## Handoff to WS2

- Add `test_name_advance_presents_race_table` and extend `test_full_creation_apprentice_caster` on `"Dumpy"` turn per plan §3.
- Run full `tests/test_creation_flow.py -q` before ticket release.
- Domain spec changelog + `release APP-068 --done` after WS2 and spec sync.

## Risks / notes

- Repeat name at RACE (recovery) may show duplicate tables — **non-goal** per spec.
- Session log bug (`Caddy` → clerk waits) should be fixed by direct `_auto_present_race` on NAME; guard covers residual chain fallthrough only.
