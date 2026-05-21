# Drift Check: APP-019-surface-new-game-errors

**backlog_ticket:** APP-019  
**domain_spec:** [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md)  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § New game failure (APP-019) | no | Contexts A/B/C, emit ownership, cause map, JSONL, tests table match `orchestrator.py`; checklist `[x]` APP-019; changelog **APP-019 done** row added |
| Run [`spec.md`](spec.md) R0–R7, T-019a–f | no | Verified against `app/gm/orchestrator.py`, `app/tests/test_setup_new_game_failure.py` |
| [`tmp/backlog/app-019-surface-new-game-failure-errors.md`](../../app-019-surface-new-game-failure-errors.md) | no | AC checked; **Status** → `done`; **Closed** 2026-05-21 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Session persistence row unchanged; no priority-table conflict |

## Code ↔ domain spec (APP-019)

| Requirement | Code | Match |
|-------------|------|-------|
| **Context A — command** `new game` / `start` / `new`; no NAME desk on failure | `process_turn` L701–707: `log_error` → `_setup_new_game_failure_message(context="command")` → `_emit_recovery_narration` → return | yes |
| **Context B — death** failure emit inside handler; `already_emitted=True` | `_handle_player_death` L587–594; combat callers L1766, L1861 skip `_emit_narration` when set | yes |
| **Context C — run_ended** inline emit in resume branch | `process_turn` L721–737; success path L738–744 unchanged | yes |
| **R1** Dual JSONL; no `_emit_narration` on failure | `_emit_recovery_narration` = `log_gm_narration` only (L321–323); failure paths never call `_emit_narration` | yes |
| **Player copy** R2/R3/R4 lead + `{cause_line}` + retry + `[Awaiting: new game]` | `_setup_new_game_failure_message` L344–379 | yes |
| **Engine error map** R5 table | `_map_setup_new_game_cause` L325–342 | yes |
| **Forbidden** legacy `Could not start game:` / success NAME on failure | Removed from failure paths; T-019a/b/c/d assert absent | yes |
| **R6 UI** optional status bar | No `app/ui/app.py` diff — orchestrator narration closes ticket per spec | yes |
| **R7 success** cold `new game` → NAME | T-019f; death/run_ended success copy unchanged in orchestrator | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| Show clear error with cause + retry hint when new game fails | **PASS** — mapped `{cause_line}`, “Type **new game** to try again”, footer `[Awaiting: new game]` in contexts A/B/C; dual JSONL (`log_error("setup_new_game", …)` + `_emit_recovery_narration`) |

## Tests ↔ domain spec § Tests APP-019

| Spec ID | Test | Result |
|---------|------|--------|
| **T-019a** | `test_t019a_command_failure_mapped_cause` | **PASS** |
| **T-019b** | `test_t019b_command_failure_default_map` | **PASS** |
| **T-019c** | `test_t019c_death_failure_caller_contract` | **PASS** |
| **T-019d** | `test_t019d_run_ended_failure` | **PASS** |
| **T-019e** | `test_t019e_drift_silence_on_setup_failure` | **PASS** |
| **T-019f** | `test_t019f_success_regression_reaches_name` | **PASS** |

```bash
cd app
python -m pytest tests/test_setup_new_game_failure.py -v
python -m pytest tests -q -k "setup_new_game_failure or setup_new_game"
```

**Result:** 6 passed (0.82s); 10 passed, 57 deselected (1.51s)

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § New game failure + checklist + changelog aligned with code
- [x] Ticket **Status** → `done` / **Closed** 2026-05-21
- [ ] `python tmp/backlog/claim_ticket.py release APP-019 --done` — orchestrator (clears `tmp/.active-ticket.json`, updates backlog README)

## Ancillary notes (non-blocking)

1. **T-019d cause mapping:** Uses `permission denied` mock but does not assert DB-write `{cause_line}` text — R4 structure covered; mapping exercised in T-019c (`database is locked`).
2. **R7 success B/C:** No new automated test for death restart success or `run_ended` + setup success — T-019f covers command path; manual TC-D / existing lifecycle tests.
3. **Resume synonyms:** `continue` / `resume` / `load` share the `run_ended` branch; only `load game` pytest’d (same code path).
4. **R6 UI:** Optional `_set_turn_idle("Error — try again")` deferred — narration + chips sufficient per spec.
5. **Manual playtest:** Stage 7 `human-test-plan.md` pending injected-failure smoke.
6. Domain spec header **Status: In progress** reflects open APP-014/017/018+ backlog, not APP-019 regression.
