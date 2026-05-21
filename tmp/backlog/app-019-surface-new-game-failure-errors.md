# APP-019: Surface new game failure errors

| Field | Value |
|-------|-------|
| **ID** | APP-019 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-21 |

## Summary

Silent new game failures confuse players.

## Acceptance criteria

- [x] Show clear error with cause + retry hint when new game fails.

## Expected files

- `app/gm/orchestrator.py`
- `app/ui/app.py` (optional R6 status bar only)
- `app/tests/test_setup_new_game_failure.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**QA (2026-05-20):** `load game` with no save logs `session_resume` / `no save session found` only — see [APP-071](app-071-friendly-load-game-when-no-save.md) for player-facing copy.
