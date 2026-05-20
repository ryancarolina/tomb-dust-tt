# Reflection: Dev impl WS1 — APP-014

**backlog_ticket:** APP-014  
**workstream:** WS1 — setup_new_game L1/L1b lifecycle  
**agent:** Dev (implementation stream)

## What changed

In `app/gm/orchestrator.py`, `setup_new_game()` now:

1. **C1/C2 (APP-015, unchanged):** `_reset_creation_for_new_game()` → `_clear_creation_block_on_disk()`
2. **L1:** `end_result = self.bridge.end_session()`
3. **L1b:** if `not end_result.get("ok")`, call `self.bridge.force_close_all_sessions()`
4. **L2–L7 (unchanged):** `wipe_all_data` → `init` → `campaign_new` → `session_start` → history/creation reset → `_delete_save_file`

Docstring updated to note ending the prior session before wipe.

## Constraints honored

| Constraint | How |
|------------|-----|
| No short-circuit on L1 failure | L1b runs when `not ok`, then flow continues to L2 |
| L1b explicit for `{"ok": false}` | Orchestrator calls `force_close_all_sessions()` — bridge only auto-falls back on exception |
| APP-015 boundary | C1/C2 remain before L1; no new disk-clear logic added |
| No bridge/UI edits | Only `orchestrator.py` touched |
| No caller guards | `process_turn`, `_handle_player_death`, `run_ended` resume path unchanged — all already call `setup_new_game()` |
| No WS2 tests | `test_setup_new_game_lifecycle.py` not created |

## Caller trace (read-only)

| Caller | Location | Notes |
|--------|----------|-------|
| `process_turn` | `"new game"` branch | Calls `setup_new_game()`; existing `ok` check retained (APP-019 scope) |
| `_handle_player_death` | after corpse spawn | Calls `setup_new_game(campaign_slug)` — lifecycle now centralized |
| `process_turn` resume | `run_ended` branch | Calls `setup_new_game(campaign_slug)` — same hub |

No duplicate `end_session` / `force_close` needed at call sites.

## Verification

```bash
cd app && python -m pytest -q
```

Result: **11 passed** in ~1.6s (`python -m pytest -q` from `app/`).

Grep check: `wipe_all_data` is no longer the first statement in `setup_new_game` — preceded by C1/C2 and L1/L1b.

## Risks / handoff to WS2

- WS2 should add `test_setup_new_game_lifecycle.py` (T-014a–c) asserting L1/L1b ordering and session/corpse invariants.
- If T-014b reveals stray open sessions, fix belongs in WS1/orchestrator — not test-only workaround.
- Domain spec changelog deferred to ticket release (post WS2).
