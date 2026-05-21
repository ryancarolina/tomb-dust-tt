# APP-018: Continue restores creation state

| Field | Value |
|-------|-------|
| **ID** | APP-018 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-21 |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Continue when awaiting CHARACTER_CREATION must restore creation FSM.

## Acceptance criteria

- [x] When awaiting==CHARACTER_CREATION, restore creation from save.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_session_resume_failure.py`
- `app/tests/test_creation_restore.py` (new or merged into the above — Dev choice; T-018a–f must land in at least one listed file)

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Consumer:** uses saved `engine_status` + `creation_state` when `awaiting == CHARACTER_CREATION` (APP-016 snapshot; APP-015 clears stale snapshot on **`new game`**). See domain spec § Engine status snapshot on save (APP-016) — Consumers.
