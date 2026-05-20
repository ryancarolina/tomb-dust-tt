# APP-003: Log creation step snapshot each turn

| Field | Value |
|-------|-------|
| **ID** | APP-003 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Closed** | 2026-05-20 |
| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Need per-turn creation telemetry for debugging drift.

## Acceptance criteria

- [x] After each creation turn, log {creation.step, roster_len, awaiting, creation.active}.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/logger.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-003-log-creation-step-snapshot`

_Add implementation notes, blockers, or PR links here._
