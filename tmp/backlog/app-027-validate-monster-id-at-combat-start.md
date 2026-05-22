# APP-027: Validate monster id at combat start

| Field | Value |
|-------|-------|
| **ID** | APP-027 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-combat-play-spec.md`](../app-combat-play-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Unknown monster ids produce fiction instead of errors.

## Acceptance criteria

- [x] Validate monster specs at start_combat with clear error (no fiction on unknown id).

## Expected files

- `app/gm/`
- `play/tomb_gm/`
- `app/tests/test_combat_monster_validation.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-combat-play-spec.md`](../app-combat-play-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-027-validate-monster-id-combat`

_Add implementation notes, blockers, or PR links here._
