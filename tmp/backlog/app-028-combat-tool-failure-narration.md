# APP-028: Combat tool failure narration

| Field | Value |
|-------|-------|
| **ID** | APP-028 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-21 |
| **Domain spec** | [`app-combat-play-spec.md`](../app-combat-play-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Success fiction emitted when combat tools return ok:false.

## Acceptance criteria

- [x] Enforce failure narration for all combat tools.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_combat_failure_narration.py`
- `tmp/app-combat-play-spec.md` (§ Combat tool failure narration + changelog on close)

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-combat-play-spec.md`](../app-combat-play-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-028-combat-failure-narration`

_Add implementation notes, blockers, or PR links here._
