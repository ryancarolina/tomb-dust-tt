# Dev implementation reflection — WS2 (APP-017 tests)

**backlog_ticket:** APP-017  
**stream:** WS2 — `app/tests/test_reconcile_empty_roster_on_load.py`  
**date:** 2026-05-21

## Delivered

- New module `app/tests/test_reconcile_empty_roster_on_load.py` covering T-017a–f and T-017c2 per `plan.md`.
- Reused `save_path`, `headless_app`, `read_save` from `test_engine_status_on_save.py`.
- Local helpers: `_patch_session_state_path`, `_write_session_state`, `_patch_live_status`, `_roll_attributes_patch`.
- All disk tests patch `orchestrator._session_state_path` → `tmp_path/session_state.json` (never dev `app/session_state.json`).

## Test results

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_reconcile_empty_roster_on_load.py -q` | **7 passed** (6.33s) |
| `cd app && python -m pytest tests -q -k "reconcile or empty_roster or app_017"` | **7 passed**, 60 deselected |
| `cd app && python -m pytest tests -q -k "engine_status or load_session or inactive_creation or session_resume"` | **11 passed**, 56 deselected |

### Cases

| ID | Function | Status |
|----|----------|--------|
| T-017a | `test_t017a_force_active_when_inactive_and_disk_mid_creation` | pass |
| T-017b | `test_t017b_force_active_from_disk_when_live_setup` | pass |
| T-017c | `test_t017c_post_finalize_non_empty_roster_no_reactivate` | pass |
| T-017c2 | `test_t017c2_live_empty_roster_wins_over_stale_saved_roster` | pass |
| T-017d | `test_t017d_legacy_without_engine_status_unchanged` | pass |
| T-017e | `test_t017e_suggestions_nonempty_after_reconcile` | pass |
| T-017f | `test_t017f_roster_setup_orphan_rows_no_force_active` | pass |

## Notes

- WS2 assumes WS1 reconcile helpers in `app/gm/orchestrator.py` are present (`_read_saved_engine_status`, `_force_creation_active_if_reconcile_needed`, sync prelude). All tests green against current tree.
- T-017d mirrors T4c legacy fixture from `test_engine_status_on_save.py` to preserve “no engine_status → no reconcile side effect” contract.
- T-017e drives creation to `EQUIPMENT_GOLD` via `INPUTS` (stops before `WORLD_INTRO`), then asserts `get_player_suggestions()` chips after `_sync_creation_from_status()`.

## Out of scope (this stream)

- `tmp/app-session-persistence-spec.md` changelog — ticket close / separate stream.
- No edits outside ticket Expected files.
