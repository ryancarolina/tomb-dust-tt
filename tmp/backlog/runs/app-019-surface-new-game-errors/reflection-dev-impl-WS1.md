# Dev Implementation Reflection: APP-019 WS1

**Ticket:** APP-019 — Surface new game failure errors  
**Workstream:** WS1 — Failure helpers + contexts A/B/C + combat callers  
**Date:** 2026-05-20

## What was done

- Added module-level `PlayerDeathResult` dataclass (`message`, `already_emitted=False`).
- Added `_map_setup_new_game_cause` and `_setup_new_game_failure_message` after `_emit_recovery_narration` (R5 substring map; R2/R3/R4 copy variants with `[Awaiting: new game]` footer).
- **Context A:** `process_turn` new-game branch — `log_error` → failure message → `_emit_recovery_narration` → return (replaces `Could not start game: …`).
- **Context B:** `_handle_player_death` captures `setup_result`; on failure emits recovery narration inside handler and returns `PlayerDeathResult(..., already_emitted=True)`; success unchanged with `already_emitted=False`.
- **Context C:** `run_ended` resume branch checks `setup_result.get("ok")` before success `death_msg` + `_emit_narration`.
- **Combat callers** (~1766, ~1861): `death_result is not None` guard; skip `_emit_narration` when `already_emitted`; preserve history append shapes.

## Verification

| Check | Result |
|-------|--------|
| `python -m py_compile gm/orchestrator.py` | pass |
| `from gm.orchestrator import Orchestrator, PlayerDeathResult` | import ok |
| Grep helpers / contract symbols | present in `orchestrator.py` |

## Deviations from plan

- None — line numbers shifted slightly from plan (~1586/~1680 → ~1766/~1861) due to helper block insertion; behavior matches workstreams § WS1.

## Risks / follow-ups

- **WS2** owns `test_setup_new_game_failure.py` (T-019a–f) and regression filters.
- Death/run_ended **success** paths unchanged; no new automated coverage for B/C success (manual TC-D per plan).
- Optional R6 UI status bar deferred until manual smoke.
- Domain spec changelog + `release APP-019 --done` after WS2 green.

## Files changed

1. `app/gm/orchestrator.py` — WS1 only

## Out of scope (per WS1)

- `app/tests/test_setup_new_game_failure.py` (WS2)
- `app/ui/app.py`, `bridge.py`, `play/tomb_gm/**`
- `tmp/app-session-persistence-spec.md` checklist (ticket close)
