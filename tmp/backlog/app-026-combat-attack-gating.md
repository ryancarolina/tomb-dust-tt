# APP-026: Combat attack gating

| Field | Value |
|-------|-------|
| **ID** | APP-026 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-combat-play-spec.md`](../app-combat-play-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Attacks allowed outside valid combat context.

## Acceptance criteria

- [x] Before attack: require status.combat and attacker in initiative.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/tools.py` _(optional description touch only)_
- `app/tests/test_combat_attack_gating.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-combat-play-spec.md`](../app-combat-play-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-026-combat-attack-gating`

_Add implementation notes, blockers, or PR links here._
