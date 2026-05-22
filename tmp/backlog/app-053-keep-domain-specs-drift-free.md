# APP-053: Keep domain specs drift-free

| Field | Value |
|-------|-------|
| **ID** | APP-053 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-master-spec.md`](../app-master-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Ongoing: every domain spec checklist matches code.

## Acceptance criteria

- [ ] Every domain spec reflects current code; update on each merged ticket.

## Expected files

- `tmp/app-*-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-master-spec.md`](../app-master-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
