# APP-009: Finalize gate — non-empty roster

| Field | Value |
|-------|-------|
| **ID** | APP-009 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Session reached PRE_DELVE with empty roster after failed finalize.

## Acceptance criteria

- [x] After finalize, assert bridge.status().roster non-empty.
- [x] On failure stay in creation with clear error; no phase advance.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/creation.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
