# APP-022: Hint enter_dungeon on failed set_phase(delve)

| Field | Value |
|-------|-------|
| **ID** | APP-022 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Failed set_phase(delve) should guide correct tool usage.

## Acceptance criteria

- [x] On failed set_phase(delve), orchestrator hints enter_dungeon + compass_exits.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_exploration_set_phase_delve_hint.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-022-hint-enterdungeon-on-failed-setphasedelve`

_Add implementation notes, blockers, or PR links here._
