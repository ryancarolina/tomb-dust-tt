# Drift Check: APP-018-continue-creation-state

**backlog_ticket:** APP-018  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Creation restore on continue / relaunch (APP-018) | no | G1–G3, merge order, non-regression notes match `orchestrator.py`; checklist `[x]` APP-018; AC `[x]`; changelog **APP-018 done** row added |
| Run `spec.md` R1–R7, T-018a–f | no | Verified against `app/gm/orchestrator.py`, `app/tests/test_creation_restore.py` |
| [`tmp/backlog/app-018-continue-restores-creation-state.md`](../../app-018-continue-restores-creation-state.md) | no | AC checked; **Status** → `done`; **Closed** 2026-05-21 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry | no | Session persistence row unchanged — APP-018 additive on existing owner |

## Code ↔ domain spec (APP-018)

| Requirement | Code | Match |
|-------------|------|-------|
| **G1a** Saved `engine_status.awaiting == CHARACTER_CREATION` when present; else live | `_creation_restore_gate` L429–436 | yes |
| **G1b** `creation_state.active == true` + valid step in `CREATION_STEPS` | L442–447 | yes |
| **G1c** Empty roster in snapshot when present | L437–438 | yes |
| **G1d** Live roster non-empty → no restore | L426–427 | yes |
| **G2** `import_creation_state`; ensure active; no post-import NAME clobber | `_restore_creation_from_session_state` L467–470; resume path L752–757 uses `_force_creation_active_if_reconcile_needed` not `CreationState(..., step="NAME")` | yes |
| **G2** `_sync_creation_from_status` after import; WORLD_INTRO → NAME only | L182–201; L747 calls sync after restore | yes |
| **G3a** First non–`new game` `process_turn` restores when G1 passes | L710–711 | yes |
| **G3b** Resume fail — restore before `_resume_failure_message` | L717–718 | yes |
| **G3c** Resume success — restore before sync / CHARACTER_CREATION branch | L745–757 | yes |
| Once-only guard per relaunch | `_creation_disk_restore_done`; reset in `_reset_creation_for_new_game` L473–475 | yes |
| `_restore_history` — narration + combat only (no creation import) | L132–147 | yes |
| **Batch** APP-018 restore before APP-017 force-active | `_sync_creation_from_status` calls restore at entry L184–186, then `_force_creation_active_if_reconcile_needed` L187 | yes |
| **Non-goal** No `ui/app.py` / APP-064 boot changes | Diff scope: `orchestrator.py`, tests only | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| When `awaiting == CHARACTER_CREATION`, restore creation from save | **PASS** — G1 gate + G3a–c; `import_creation_state` hydrates step/fields from disk |

## Tests ↔ domain spec § Tests APP-018

| Spec ID | Test | Result |
|---------|------|--------|
| **T-018a** | `test_t018a_continue_fail_restores_race_from_disk` | **PASS** |
| **T-018b** | `test_t018b_relaunch_desk_input_restores_saved_awaiting` | **PASS** |
| **T-018c** | `test_t018c_resume_success_preserves_race_not_name` | **PASS** |
| **T-018d** | `test_t018d_legacy_save_live_awaiting_restores_skills` | **PASS** |
| **T-018e** | `test_t018e_post_finalize_does_not_restore_stale_creation` (×2) | **PASS** |
| **T-018f** | `test_t018f_new_game_wipe_blocks_skills_restore_on_continue` | **PASS** |

```bash
cd app; python -m pytest tests/test_creation_restore.py -q
cd app; python -m pytest tests -q -k "creation_restore or continue_creation or app018"
```

**Result:** 7 passed (1.01s); 7 passed, 60 deselected (0.93s)

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § Creation restore + checklist + changelog aligned with code
- [x] Ticket **Status** → `done` / **Closed** 2026-05-21
- [ ] `python tmp/backlog/claim_ticket.py release APP-018 --done` — orchestrator (clears active session)

## Ancillary notes (non-blocking)

1. **G1d live roster only:** T-018e covers saved snapshot roster; no isolated test for live non-empty roster when snapshot roster empty — low risk (G1d L426–427 implemented).
2. **T-018b:** Asserts FSM state after desk input, not `_creation_turn` spy — sufficient per plan; restore + `creation.active` implies routing at L772–773.
3. **`_sync_creation_from_status`** redundant restore call at entry — safe via once-only flag; preserves canonical restore-before-force-active order with APP-017.
4. Domain spec header **Status: In progress** reflects broader session backlog (APP-014–APP-020), not APP-018 regression.
5. Manual mid-creation relaunch / continue playtest — deferred Stage 7 `human-test-plan.md`.
