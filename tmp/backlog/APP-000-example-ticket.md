# APP-000: Example ticket (do not implement)

| Field | Value |
|-------|-------|
| **ID** | APP-000 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | cancelled |
| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

This file is a **filled example** of the backlog format. Copy [`TEMPLATE.md`](TEMPLATE.md) for new work; do not implement APP-000.

## Acceptance criteria

- [x] Ticket uses the standard metadata table
- [x] Ticket links to exactly one domain spec under `tmp/app-*-spec.md`
- [x] Acceptance criteria are testable checkboxes
- [x] Expected files listed before implementation starts

## Expected files

- `tmp/backlog/TEMPLATE.md`
- `tmp/backlog/README.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

Real tickets start at **APP-001**. When picking up work:

1. Set status to `in_progress`.
2. Implement only paths listed under **Expected files** (or update the ticket first).
3. Close the ticket and sync the domain spec when done.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-013 | example: APP-001 blocked until edge-type decision |
