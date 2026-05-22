# APP-055: tomb_gm tests pytest green

| Field | Value |
|-------|-------|
| **ID** | APP-055 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-master-spec.md`](../app-master-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Master release gate: engine tests.

## Acceptance criteria

- [ ] python -m pytest play/tomb_gm/tests green.

## Expected files

- `play/tomb_gm/tests/`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-master-spec.md`](../app-master-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Grooming 2026-05-20:** `python -m pytest play/tomb_gm/tests -q` → **1 failed** (`test_foundation.py::test_init_status_check_suggest`). Fix failure before closing.
