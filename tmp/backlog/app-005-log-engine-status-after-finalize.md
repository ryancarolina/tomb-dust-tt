# APP-005: Log engine status after finalize

| Field | Value |
|-------|-------|
| **ID** | APP-005 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Finalize success/failure hard to diagnose without status snapshot.

## Acceptance criteria

- [x] After character_create / finalize, log engine status() snapshot.

## Expected files

- `app/gm/logger.py`
- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
