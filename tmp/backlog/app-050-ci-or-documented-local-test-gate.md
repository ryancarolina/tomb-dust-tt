# APP-050: CI or documented local test gate

| Field | Value |
|-------|-------|
| **ID** | APP-050 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |
| **Created** | 2026-05-20 |

## Summary

No CI workflow for app tests.

## Acceptance criteria

- [ ] CI workflow or documented local gate per logging-qa spec.

## Expected files

- `.github/workflows/`
- `app/README.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
