# Drift Check: APP-015-clear-creation-block-on-new-game

**backlog_ticket:** APP-015  
**domain_spec:** [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md)  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § New game — creation block clear (APP-015) | no | C1–C4 match `orchestrator.py`; checklist + AC `[x]`; changelog **APP-015 done** |
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Tests APP-015 (T-015a–d) | no | Five tests in `app/tests/test_creation_block_on_new_game.py` |
| Run [`spec.md`](spec.md) C1–C5, AC | no | Run spec indexes domain; cosmetic: run spec C5 omits **T-015d** (domain owns T-015d) |
| [`tmp/backlog/app-015-clear-creation-block-on-new-game.md`](../../app-015-clear-creation-block-on-new-game.md) | no | AC checked; **Status** → `done`; **Closed** 2026-05-20 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Session persistence row unchanged; no priority-table conflict |

## Code ↔ domain spec (APP-015)

| Requirement | Code | Match |
|-------------|------|-------|
| **C1** In-memory NAME reset + disk persist **before** L1/L2 | `setup_new_game` L368–369: `_reset_creation_for_new_game()` → `_clear_creation_block_on_disk()` before `end_session` / `wipe_all_data` | yes |
| **C2** Surgical R-M-W: `creation_state` = `export_creation_state()`; remove `engine_status`; preserve other keys | `_clear_creation_block_on_disk` L301–311; T-015a preserves narration/history; T-015d clears `engine_status` | yes |
| **C3** Early return paths still NAME-fresh on disk + memory | T-015b (`campaign_new` failure); C1–C2 before L4 return | yes |
| **C4** Batch: prepend before APP-014 L1; L7 unchanged; APP-016 stale snapshot cleared via C2 | C1–C2 at entry; L383 `_delete_save_file` on success only; `data.pop("engine_status", None)` | yes |
| **File map** `_session_state_path`, `_clear_creation_block_on_disk` | L295–311, unified path in `_is_mid_creation_resume_failure` | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| On **new game**, explicitly clear `session_state.json` **creation block** | **PASS** — upfront disk write on every `setup_new_game()` entry, not only L7 success unlink |

## Tests run (drift round)

```bash
cd app
python -m pytest tests/test_creation_block_on_new_game.py -q
python -m pytest tests -q -k "creation_block or new_game_creation"
```

**Result:** 5 passed (module); 5 passed, 18 deselected (`-k` filter)

| Spec case | Test | Result |
|-----------|------|--------|
| **T-015a** | `test_t015a_setup_new_game_clears_stale_creation_on_disk` | PASS |
| **T-015b** | `test_t015b_campaign_new_failure_still_clears_creation` | PASS |
| **T-015c** | `test_t015c_load_game_after_new_game_uses_name_not_stale_disk` | PASS |
| **T-015d** (success + early return) | `test_t015d_engine_status_cleared_on_new_game_*` | PASS |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § APP-015 checklist, AC, changelog aligned with code
- [x] Ticket **Status** → `done` / **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-015 --done` — orchestrator (clears `tmp/.active-ticket.json`)

## Ancillary notes (non-blocking)

- **`_clear_creation_block_on_disk`:** missing save file → no-op; corrupt JSON → silent `except` (impl QA noted; acceptable for AC).
- **`session_start` failure:** not pytest’d; C1–C2 precede L5 — same structural guarantee as T-015b.
- **APP-014** lifecycle (L1–L7) present in same `setup_new_game` body; APP-014 ticket/checklist remains open — separate drift scope.
- **Manual playtest:** Stage 7 `human-test-plan.md` not present in run folder; deferred to orchestrator.
- **Domain header** “Status: In progress” reflects open APP-014/016/017+ backlog, not APP-015 regression.
