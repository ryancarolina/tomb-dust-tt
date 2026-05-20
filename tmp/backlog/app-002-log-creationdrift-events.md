# APP-002: Log creation_drift events

| Field | Value |
|-------|-------|
| **ID** | APP-002 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Closed** | 2026-05-20 |
| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Session logs showed UI phase diverging from engine creation step without a structured alert.

## Acceptance criteria

- [x] Emit creation_drift JSONL event when narration phase != engine creation.step.
- [x] Event includes step, roster_len, awaiting, creation.active.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/logger.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-002-log-creation-drift-events`

_Add implementation notes, blockers, or PR links here._
