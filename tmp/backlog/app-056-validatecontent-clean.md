# APP-056: validate_content clean

| Field | Value |
|-------|-------|
| **ID** | APP-056 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | done |
| **Domain spec** | [`app-master-spec.md`](../app-master-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Master release gate: content validation.

## Acceptance criteria

- [x] python build/tools/validate_content.py clean.

## Expected files

- `build/tools/validate_content.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-master-spec.md`](../app-master-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
