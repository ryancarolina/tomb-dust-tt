# QA PASS: Implementation

**Task:** APP-014-setupnewgame-session-lifecycle  
**backlog_ticket:** APP-014  
**ticket_path:** tmp/backlog/app-014-setupnewgame-session-lifecycle.md  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; domain spec § setup_new_game lifecycle (APP-014) already drafted)

## Verdict

**PASS** — `setup_new_game` implements L1/L1b → L2 → L3 → L4 → L5 → L6 → L7 per domain spec; ticket AC satisfied; T-014a–c green; regression `-k` filters green.

## Automated tests

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_setup_new_game_lifecycle.py -q` | **3 passed** in 1.00s |
| `cd app && python -m pytest tests -q -k "setup_new_game or session_lifecycle or creation_flow"` | **9 passed**, 14 deselected in 1.95s |
| `python -m pytest play/tomb_gm/tests -q -k session` | **5 passed**, 131 deselected in 1.76s |

## Ticket AC → implementation

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| `setup_new_game()`: session end → wipe_all_data → campaign new → session start | `orchestrator.py` L370–380: `end_session()`; L371–372 `force_close_all_sessions()` when L1 `not ok`; L373 `wipe_all_data()`; L375 `campaign_new`; L380 `session_start` | ✓ |
| Domain spec updated on close | `tmp/app-session-persistence-spec.md` § setup_new_game lifecycle (APP-014) drafted; checklist `[ ]` APP-014 and impl **done** changelog — **Stage 6 drift / release** | Deferred (non-blocking for impl QA) |
| Stuck partial creation → `new game` → clean NAME | T-014a: mid-creation `SKILLS` → `setup_new_game()` → `creation.step == "NAME"`, active session | ✓ (pytest); manual APP-064 follow-on in Stage 7 |

## Domain L1–L7 → code

| Step | Requirement | Evidence | Result |
|------|-------------|----------|--------|
| **L1** | `bridge.end_session()` before wipe | L370 | ✓ |
| **L1b** | `force_close_all_sessions()` when L1 `not ok` | L371–372 (orchestrator-owned; bridge only falls back on exception) | ✓ |
| **L2** | `wipe_all_data()` after L1/L1b | L373 | ✓ |
| **L3** | `init()` | L374 | ✓ |
| **L4** | `campaign_new`; early return on hard failure | L375–379; `"already exists"` swallow unchanged | ✓ |
| **L5** | `session_start` | L380 | ✓ |
| **L6** | `history.clear()`; `CreationState(NAME)` | L381–382 (also C1 reset at entry L368) | ✓ |
| **L7** | `_delete_save_file()` on success | L383 | ✓ |
| **L5 inv.** | `world_corpses` survive wipe | T-014c; bridge wipe table list (plan-verified) | ✓ |
| **L6 callers** | Single hub — no duplicate lifecycle | `process_turn` L518; `_handle_player_death` L406; `run_ended` L540 | ✓ |

## Spec tests T-014a–c → pytest

| ID | Test | Result |
|----|------|--------|
| **T-014a** | `test_setup_new_game_from_mid_creation` | PASS — `ok`, `step == NAME`, `count_open_sessions == 1` |
| **T-014b** | `test_setup_new_game_closes_prior_session` | PASS — prior row ended or wiped; new `current`; one open session |
| **T-014c** | `test_setup_new_game_preserves_corpses` | PASS — corpse count unchanged after `process_delver_death` + `setup_new_game` |

## Diff scope reviewed

| Path | Role |
|------|------|
| `app/gm/orchestrator.py` | L1/L1b prepend; docstring; `_session_state_path` refactor; **APP-015 batch bleed:** `_reset_creation_for_new_game`, `_clear_creation_block_on_disk` at entry (C1–C2 before L1) |
| `app/tests/test_setup_new_game_lifecycle.py` | **New** — T-014a–c (untracked in git; present on disk) |

**Not edited (per plan):** `app/gm/bridge.py`, `app/ui/app.py`.

## Independent traces (adversarial)

| Claim | Post-impl evidence | Result |
|-------|-------------------|--------|
| Pre-fix bug: wipe-first | Diff shows `end_session` / `force_close` inserted **before** `wipe_all_data` | Fixed |
| L1b not optional | `end_session` returns `ok: false` for missing session; orchestrator still calls `force_close` then wipe | Correct |
| Failure path skips L6–L7 | `campaign_new` / `session_start` early `return` unchanged | Correct |
| Death path no `ok` check | `_handle_player_death` L406 — still narrates success without checking return | Known — **APP-019**; plan non-blocking |
| UI autosave race on failed setup | `app/ui/app.py` `finally` `_save_session` — **APP-015** C3; upfront disk clear at L368–369 mitigates stale block on attempt | Improved by batch merge; APP-015 owns full AC |

## Scope gate

| Path | Ticket Expected? | Delivered? |
|------|------------------|------------|
| `app/gm/orchestrator.py` | Yes | Yes |
| `app/main flow` | Yes (vague) | Traced via `process_turn` / UI; no UI diff |
| `app/tests/test_setup_new_game_lifecycle.py` | **No** (metadata gap) | Yes — required by domain spec § Tests APP-014 |

Recommend updating ticket **Expected files** before release (qa-plan-pass note).

## Notes (non-blocking)

1. **APP-015 overlap:** Entry calls `_reset_creation_for_new_game()` and `_clear_creation_block_on_disk()` before L1 — satisfies domain § APP-015 C1–C2 when batched; separate APP-015 impl QA should confirm C3 failure paths and T-015 tests if that ticket is in flight.
2. **`_clear_creation_block_on_disk`:** bare `except Exception: pass` — silent disk failure; acceptable for APP-014 L1–L5; flag for APP-015 hardening if needed.
3. **T-014b:** assertion `after_prior is not None or current_row["id"] == "current"` — second clause tautological if `current_row` exists; test still validates ≤1 open session and new `current` row.
4. **Domain spec / ticket close:** APP-014 checklist still `[ ]`; no dated “APP-014 done” changelog line — orchestrator **release + drift-check** stage.
5. **Human playtest:** APP-064 partial-creation → `new game` chip — not run in this round (Stage 7).

## Handoff

**Ready for:** Stage 6 drift check, `release APP-014 --done`, domain spec checklist + changelog, `human-test-plan.md` / manual playtest.  
**Do not block on:** APP-015 code in same function if batch landed 015 first — verify APP-015 ticket separately.
