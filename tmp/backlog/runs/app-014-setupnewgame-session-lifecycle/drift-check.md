# Drift Check: APP-014-setupnewgame-session-lifecycle

**backlog_ticket:** APP-014  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § setup_new_game lifecycle (APP-014) | no | L1–L7 match `orchestrator.py`; checklist `[x]`; changelog **APP-014 done** row added |
| Run `spec.md` / `plan.md` L1–L7, T-014a–c | no | Verified against implementation and pytest |
| [`tmp/backlog/app-014-setupnewgame-session-lifecycle.md`](../../app-014-setupnewgame-session-lifecycle.md) | no | AC checked; **Status** `done`, **Closed** 2026-05-20 |

## Code ↔ domain spec (APP-014)

| Step | Requirement | Code (`app/gm/orchestrator.py`) | Match |
|------|-------------|----------------------------------|-------|
| **L1** | `bridge.end_session()` before wipe | L370 | yes |
| **L1b** | `force_close_all_sessions()` when L1 `not ok` | L371–372 | yes |
| **L2** | `wipe_all_data()` after L1/L1b | L373 | yes |
| **L3** | `init()` | L374 | yes |
| **L4** | `campaign_new`; early return on hard failure; `"already exists"` swallow | L375–379 | yes |
| **L5** | `session_start` | L380 | yes |
| **L6** | `history.clear()`; `CreationState(NAME)` | L381–382 | yes |
| **L7** | `_delete_save_file()` on success only | L383 (after L5; not on early return) | yes |
| **Callers** | Single hub — `process_turn` new game, death, `run_ended` | L518, L406, L540 | yes |
| **Invariants** | `world_corpses` persist; ≤1 open session after success | T-014c; T-014a/b | yes |
| **Success** | `ok: true`; `creation.step == NAME` | Return `session` dict; tests assert | yes |
| **Failure** | L6–L7 skipped on L4/L5 failure | L378–379 early `return` | yes |

**Batch note (non-drift):** Entry calls `_reset_creation_for_new_game()` + `_clear_creation_block_on_disk()` (L368–369) per domain § APP-015 C1–C2 before L1. Documented batch boundary; APP-015 owns separate ticket AC (C3 failure paths, T-015).

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| `setup_new_game()`: session end → wipe_all_data → campaign new → session start | **PASS** |
| Stuck partial creation → `new game` → clean NAME (spec test + AC intent) | **PASS** (T-014a pytest) |

## Tests run

```bash
cd app && python -m pytest tests/test_setup_new_game_lifecycle.py -q
cd app && python -m pytest tests -q -k "setup_new_game or session_lifecycle or creation_flow"
python -m pytest play/tomb_gm/tests -q -k session
```

**Result:** 3 passed (T-014a–c); 9 passed, 14 deselected (app `-k`); 5 passed, 131 deselected (engine session)

**Deferred (Stage 7, non-blocking):** Manual APP-064 partial-creation → **`new game`** chip playtest per spec § Tests APP-014 manual hint.

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § APP-014 checklist + changelog aligned with code
- [x] Ticket **Status** → `done` / **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-014 --done` — orchestrator (clears active session)

## Ancillary notes (non-blocking)

- **Expected files gap:** `app/tests/test_setup_new_game_lifecycle.py` delivers T-014a–c but was not listed in ticket metadata — added in ticket **Expected files** on close.
- **APP-019:** `_handle_player_death` still narrates success without checking `setup_new_game` return `ok` — out of APP-014 scope.
- **`_clear_creation_block_on_disk`:** silent `except` on disk errors — acceptable for APP-014; APP-015 may harden.
- Domain spec header **Status: In progress** reflects open APP-015–APP-020; APP-014 slice is closed.
