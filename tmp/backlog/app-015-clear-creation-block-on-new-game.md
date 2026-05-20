# APP-015: Clear creation block on new game

| Field | Value |
|-------|-------|
| **ID** | APP-015 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-20 |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Stale creation state can survive new game.

## Acceptance criteria

- [x] On new game, explicitly clear session_state.json creation block.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_creation_block_on_new_game.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-015-clear-creation-block-on-new-game`

_Add implementation notes, blockers, or PR links here._
