# Dev reflection — WS2 (APP-018 tests)

**backlog_ticket:** APP-018  
**stream:** WS2 — `app/tests/test_creation_restore.py`  
**date:** 2026-05-21

## Deliverable

New module `app/tests/test_creation_restore.py` with:

| ID | Test | Status |
|----|------|--------|
| T-018a | `test_t018a_continue_fail_restores_race_from_disk` | pass |
| T-018b | `test_t018b_relaunch_desk_input_restores_saved_awaiting` | pass |
| T-018c | `test_t018c_resume_success_preserves_race_not_name` | pass |
| T-018d | `test_t018d_legacy_save_live_awaiting_restores_skills` | pass |
| T-018e | `test_t018e_post_finalize_does_not_restore_stale_creation` (param: `PLAYER_ACTIONS`, non-empty roster) | pass ×2 |
| T-018f | `test_t018f_new_game_wipe_blocks_skills_restore_on_continue` | pass |

**Patterns:** `_patch_session_state_path` → `tmp_path/session_state.json`; `seed_session_state` helper; headless `orchestrator` fixture from `conftest.py`; `session_resume` / `bridge.status` monkeypatch per case (aligned with `test_creation_block_on_new_game.py` and `test_session_resume_failure.py`).

## Test run

```text
cd app && python -m pytest tests/test_creation_restore.py -q
.......                                                                  [100%]
7 passed in 1.03s
```

## Notes

- T-018c spies `_creation_turn` to avoid full LLM path while asserting step stays `RACE` after successful resume.
- T-018e uses `@pytest.mark.parametrize` for roster-non-empty vs `awaiting=PLAYER_ACTIONS` (single plan row, two gate failures).
- T-018f reuses APP-015 pattern: `setup_new_game()` + `_delete_save_file` noop; asserts disk NAME-only and variant B stays in NAME flow.
- No changes to `test_session_resume_failure.py` — T-018a disk-seed coverage lives in the new module per plan W2.3.

## Dependencies

Assumes WS1 landed in `app/gm/orchestrator.py` (`_restore_creation_from_session_state`, G3a–c, NAME clobber removed). All tests green against current tree.

## Out of scope (this stream)

- `tmp/app-session-persistence-spec.md` changelog (WS3 / ticket close)
- `release APP-018 --done`
