# APP-014: setup_new_game session lifecycle

| Field | Value |
|-------|-------|
| **ID** | APP-014 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

New game must cleanly end prior session before wipe.

## Acceptance criteria

- [x] setup_new_game(): session end → wipe_all_data → campaign new → session start.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_setup_new_game_lifecycle.py`
- `app/main flow` (traced: `process_turn` / `_handle_player_death` / `run_ended` — no UI diff)

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-014-setupnewgame-session-lifecycle`

**Drift (2026-05-20):** PASS — `tmp/backlog/runs/app-014-setupnewgame-session-lifecycle/drift-check.md`. L1/L1b prepend before wipe; T-014a–c green. Batch entry includes APP-015 C1–C2 helpers (documented in domain spec). Orchestrator: `release APP-014 --done`.
