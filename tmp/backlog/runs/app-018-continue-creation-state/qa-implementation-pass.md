# QA PASS: Implementation

**Task:** APP-018-continue-creation-state  
**backlog_ticket:** APP-018  
**ticket_path:** tmp/backlog/app-018-continue-restores-creation-state.md  
**domain_spec:** tmp/app-session-persistence-spec.md § Creation restore on continue / relaunch (APP-018)  
**Round:** 1 (implementation review)  
**Verdict:** **PASS**

## Summary

Orchestrator-owned **`_restore_creation_from_session_state()`** + **G1 gate** restore mid-creation FSM from `session_state.json` on relaunch (G3a), resume failure (G3b), and resume success (G3c). Post-resume **NAME clobber removed**; creation import stripped from **`_restore_history`**. New module **`test_creation_restore.py`** covers **T-018a–f** (7 tests including T-018e parametrize). All planned pytest commands and full **`app/tests`** green.

**Blocker count:** 0

---

## Tests run

| Command | Result |
|---------|--------|
| `cd app; python -m pytest tests/test_creation_restore.py -q` | **pass** — 7 passed in 1.56s |
| `cd app; python -m pytest tests/test_engine_status_on_save.py tests/test_session_resume_failure.py tests/test_creation_block_on_new_game.py -q` | **pass** — 12 passed in 4.08s |
| `cd app; python -m pytest tests -q -k "creation_restore or continue_creation or app018"` | **pass** — 7 passed, 60 deselected in 1.59s |
| `cd app; python -m pytest tests -q` | **pass** — 67 passed in 18.07s |

---

## Ticket AC → code + tests

| Ticket AC | On disk | Result |
|-----------|---------|--------|
| When `awaiting == CHARACTER_CREATION`, restore creation from save | G1 gate + G3a–c in `orchestrator.py`; T-018a–d | **PASS** |

---

## Spec R1–R7 → implementation

| Req | Status | Evidence |
|-----|--------|----------|
| **R1** Shared restore helper + G1 gate | **PASS** | `_creation_restore_gate` (G1a–d, `CREATION_STEPS` validation); `_restore_creation_from_session_state` |
| **R2** Relaunch first non–`new game` turn | **PASS** | G3a L710–711; T-018b (saved `CHARACTER_CREATION`, live `SETUP`, desk input) |
| **R3** Resume fail before variant B | **PASS** | G3b L717–718 before `_resume_failure_message`; T-018a (step + footer from disk) |
| **R4** Resume success before sync; no NAME clobber | **PASS** | G3c L745–757; no `CreationState(active=True, step="NAME")` on resume path; T-018c |
| **R5** Legacy saves without `engine_status` | **PASS** | G1 legacy branch L439–440; T-018d |
| **R6** Post-finalize / stale gate no-op | **PASS** | G1a saved awaiting, G1c snapshot roster, G1d live roster; T-018e (×2) |
| **R7** Variant B + `_creation_turn` use restored step | **PASS** | T-018a footer `[Awaiting: RACE_INPUT]` + step phrase; T-018b FSM active at RACE |

---

## G1 gate review

| Rule | Implementation | Verified by |
|------|----------------|-------------|
| **G1d** Live roster non-empty → no restore | L426–427 | T-018e (saved roster param) |
| **G1a** Saved `awaiting` precedence; stale saved blocks restore | L429–436 | T-018b, T-018e (`PLAYER_ACTIONS`) |
| **G1c** Snapshot roster empty when present | L437–438 | T-018e (non-empty roster param) |
| **G1b** Active creation block + valid step | L442–447 | T-018a–d |
| Once-only guard | `_creation_disk_restore_done`; reset in `_reset_creation_for_new_game` | T-018f; G3b second call no-op after G3a |

---

## G3 call sites

| ID | Location | Status |
|----|----------|--------|
| **G3a** | After `new game` early return, before resume / creation routing (L710–711) | **PASS** |
| **G3b** | Resume fail before `_resume_failure_message` (L717–718) | **PASS** |
| **G3c** | Success: `_restore_history` → restore → sync; `_force_creation_active_if_reconcile_needed` replaces NAME clobber (L745–757) | **PASS** |

**`_restore_history`:** narration + combat only — creation import removed (L132–147).

---

## Test plan T-018a–f → tests

| ID | Test | Result |
|----|------|--------|
| **T-018a** | `test_t018a_continue_fail_restores_race_from_disk` | **PASS** |
| **T-018b** | `test_t018b_relaunch_desk_input_restores_saved_awaiting` | **PASS** |
| **T-018c** | `test_t018c_resume_success_preserves_race_not_name` | **PASS** |
| **T-018d** | `test_t018d_legacy_save_live_awaiting_restores_skills` | **PASS** |
| **T-018e** | `test_t018e_post_finalize_does_not_restore_stale_creation` (×2) | **PASS** |
| **T-018f** | `test_t018f_new_game_wipe_blocks_skills_restore_on_continue` | **PASS** |

---

## Diff scope reviewed

| Path | Role | Verdict |
|------|------|---------|
| `app/gm/orchestrator.py` | Helper, gate, G3a–c, once-only flag, `_restore_history` trim, APP-017 merge hooks in `_sync_creation_from_status` | **PASS** |
| `app/tests/test_creation_restore.py` | T-018a–f (new) | **PASS** |
| `app/tests/test_session_resume_failure.py` | APP-071 regression unchanged; still green with restore | **PASS** |

**Out of scope (correct):** `app/ui/app.py`, APP-064 boot, domain spec changelog / ticket close.

---

## Non-blocking (release / drift stage)

- **G1d live roster:** T-018e covers saved snapshot roster; explicit live-roster-only gate case not isolated (G1c/G1d overlap — low risk).
- **T-018b:** Asserts FSM state after desk input, not `_creation_turn` spy — sufficient per plan note; restore + `creation.active` implies routing at L772–773.
- **`_sync_creation_from_status`** calls restore at entry (APP-017 batch merge) — redundant with G3 but safe via once-only flag; preserves canonical restore-before-force-active order.
- Domain spec AC checkbox, ticket **Status → done**, changelog entry — deferred to `release APP-018 --done` + drift check.
- **`human-test-plan.md`** not yet authored (Stage 7).

---

## Handoff

**Ready for:** Stage 6 drift check, `release APP-018 --done`, spec changelog sync, Stage 7 human playtest (`human-test-plan.md`).
