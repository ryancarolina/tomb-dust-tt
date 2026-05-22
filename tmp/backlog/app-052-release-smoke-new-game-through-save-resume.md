# APP-052: Release smoke: new game through save/resume

| Field | Value |
|-------|-------|
| **ID** | APP-052 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-master-spec.md`](../app-master-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Master spec release criteria not automated.

## Acceptance criteria

- [ ] Smoke: cd app && python main.py → new game → creation → one surface beat → save → resume.

## Expected files

- `app/`
- `manual or app/tests/`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-master-spec.md`](../app-master-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
