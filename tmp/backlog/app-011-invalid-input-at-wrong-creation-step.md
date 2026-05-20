# APP-011: Invalid input at wrong creation step

| Field | Value |
|-------|-------|
| **ID** | APP-011 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Player input like Yes at SPELL_SCHOOLS should not advance state.

## Acceptance criteria

- [x] Re-show table + error message on invalid input at wrong step.

## Expected files

- `app/gm/creation.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
