# Dev Implementation Reflection: APP-019 WS2

**Ticket:** APP-019 — Surface new game failure errors  
**Workstream:** WS2 — `test_setup_new_game_failure.py` (T-019a–f)  
**Date:** 2026-05-21

## What was done

- Added `app/tests/test_setup_new_game_failure.py` with six tests covering plan/spec T-019a–f.
- Followed APP-071 style: `orchestrator` fixture, monkeypatch `gm.orchestrator.log_gm_narration` / `log_error` / `log_creation_drift`, monkeypatch `orchestrator.setup_new_game` (and bridge mocks where needed).
- **T-019a/b:** Command failure via `process_turn("new game")` — R2 copy, mapped/default cause, dual JSONL, no legacy `Could not start game:` prefix.
- **T-019c:** Direct `_handle_player_death` with mocked bridge death path + failed `setup_new_game`; `_simulate_combat_death_emit` asserts caller skips `_emit_narration` when `already_emitted=True`.
- **T-019d:** Mocked `session_resume` (`run_ended=True`) + failed setup — R4 copy, no NAME desk.
- **T-019e:** Command + death failure paths — no `creation_drift` with `awaiting_mismatch`.
- **T-019f:** Real isolated workspace — `process_turn("new game")` reaches `creation.active` + step `NAME`.

## Test results

| Command | Result |
|---------|--------|
| `python -m pytest app/tests/test_setup_new_game_failure.py -q` | **6 passed** (2.14s) |
| `python -m pytest app/tests -q -k "setup_new_game_failure or setup_new_game"` | **10 passed** (1.69s) |
| `python -m pytest app/tests/test_session_resume_failure.py -q` | **3 passed** (1.86s) |

## Deviations from plan

- None — test IDs, mocks, and assertions match plan.md §7 and spec.md test plan.

## Risks / follow-ups

- WS1 orchestrator implementation was prerequisite; tests assume WS1 helpers/branches are present.
- Optional R6 UI status bar and domain spec changelog remain for ticket close.
- Death/run_ended **success** paths still rely on manual TC-D / existing lifecycle tests (not new in WS2).

## Files changed

1. `app/tests/test_setup_new_game_failure.py` — **new** (WS2 only)
