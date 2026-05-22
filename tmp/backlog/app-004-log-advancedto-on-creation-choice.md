# APP-004: Log advanced_to on creation choice

| Field | Value |
|-------|-------|
| **ID** | APP-004 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Successful creation transitions are not logged consistently.

## Acceptance criteria

- [x] Log advanced_to on every successful _execute_creation_choice.

## Expected files

- `app/gm/logger.py`
- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-004-log-advancedto-creation-choice`

_Add implementation notes, blockers, or PR links here._

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-002 | blocks this ticket |
