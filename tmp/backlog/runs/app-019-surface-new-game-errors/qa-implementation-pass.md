# QA PASS: Implementation

**Task:** APP-019-surface-new-game-errors  
**backlog_ticket:** APP-019  
**ticket_path:** tmp/backlog/app-019-surface-new-game-failure-errors.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Round:** 1 (implementation review)  
**Verdict:** **PASS**

## Diff scope reviewed

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `PlayerDeathResult`; `_map_setup_new_game_cause`, `_setup_new_game_failure_message`; failure branches contexts A/B/C; combat callers honor `already_emitted` |
| `app/tests/test_setup_new_game_failure.py` | T-019a–f; `_simulate_combat_death_emit` caller contract helper |

**Not changed (per R6 / ticket):** `app/ui/app.py` — orchestrator narration + `[Awaiting: new game]` footer only; optional status bar deferred.

## Tests run

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_setup_new_game_failure.py -v` | **6 passed** (0.99s) |
| `cd app && python -m pytest tests -q -k "setup_new_game_failure or setup_new_game"` | **10 passed**, 57 deselected (1.53s) |
| `cd app && python -m pytest tests -q` | **67 passed** (22.14s) |

## Ticket acceptance criteria

| AC | Status | Evidence |
|----|--------|----------|
| Show clear error with cause + retry hint when new game fails | **PASS** | R2/R3/R4 copy via `_setup_new_game_failure_message`; mapped `{cause_line}` + “Type **new game** to try again”; footer `[Awaiting: new game]`; dual JSONL (`log_error` + `_emit_recovery_narration`) in T-019a–d |

## Spec requirements (R0–R7)

| Req | Status | Evidence |
|-----|--------|----------|
| **R0** Three failure contexts; no success desk on `not ok` | **PASS** | A: `process_turn` ~701–707; B: `_handle_player_death` ~587–594; C: resume `run_ended` ~730–737; T-019a/c/d/f assert no NAME / “new game has started” on failure |
| **R1** Drift-safe dual JSONL; no `_emit_narration` on failure | **PASS** | `_emit_recovery_narration` = `log_gm_narration` only; failure paths never call `_emit_narration`; T-019a–d assert single narration + `log_error("setup_new_game", …)` |
| **R1a** Contexts A/C inline emit | **PASS** | Same `process_turn` function builds message, emits, returns; T-019a/b/d |
| **R1b** Context B `already_emitted` contract | **PASS** | Handler emits on failure, returns `PlayerDeathResult(..., already_emitted=True)`; combat callers ~1766, ~1861 skip `_emit_narration` when set; T-019c + `_simulate_combat_death_emit` |
| **R2** Context A copy | **PASS** | R2 lead + relaunch hint + footer; T-019a/b |
| **R3** Context B copy | **PASS** | Corpse line preserved + failure tail; T-019c |
| **R4** Context C copy | **PASS** | run_ended lead + failure tail; T-019d |
| **R5** Engine error mapping | **PASS** | `_map_setup_new_game_cause` matches spec table; T-019a (`campaign not found`), T-019b (default); verbatim engine error not in player copy |
| **R6** UI optional | **PASS** | No required UI diff; closes on orchestrator + tests |
| **R7** Success non-regression | **PASS** | T-019f reaches `creation.active` + step `NAME`; death/run_ended success paths unchanged in orchestrator |

## Automated test mapping (T-019a–f)

| Spec case | Test | Result |
|-----------|------|--------|
| T-019a — command failure mapped | `test_t019a_command_failure_mapped_cause` | **PASS** |
| T-019b — command default map | `test_t019b_command_failure_default_map` | **PASS** |
| T-019c — death + caller contract | `test_t019c_death_failure_caller_contract` | **PASS** |
| T-019d — run_ended failure | `test_t019d_run_ended_failure` | **PASS** |
| T-019e — drift silence A+B | `test_t019e_drift_silence_on_setup_failure` | **PASS** |
| T-019f — NAME regression | `test_t019f_success_regression_reaches_name` | **PASS** |

## Code review notes (non-blocking)

1. **T-019d cause line:** Uses `permission denied` mock but does not assert mapped DB-write `{cause_line}` — R4 structure covered; mapping exercised in T-019c (`database is locked`).
2. **Success path B/C:** No new automated test for death restart success or `run_ended` + setup success (plan manual TC-D / existing lifecycle tests).
3. **Resume synonyms:** `continue` / `resume` / `load` share the `run_ended` branch; only `load game` pytest’d (same branch as spec action).
4. **Domain spec close gate:** § New game failure behavior matches code; checklist `[ ]` and impl changelog row remain for `release APP-019 --done` (not impl drift).
5. **Manual smoke:** Injected L4/L5 failure + death failure still Stage 7 (`human-test-plan.md` pending).

## Gate outcome

Implementation matches approved spec/plan, ticket AC, and domain spec § New game failure (APP-019). **Ready for:** drift check (`drift-check.md`), domain spec checklist/changelog on close, Stage 7 manual playtest, `release APP-019 --done`.
