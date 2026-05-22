# APP-030: Combat integration test

| Field | Value |
|-------|-------|
| **ID** | APP-030 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-combat-play-spec.md`](../app-combat-play-spec.md) |
| **Created** | 2026-05-20 |

## Summary

No end-to-end combat test in app suite.

## Acceptance criteria

- [x] **I1** — `app/tests/test_combat_integration.py`: bridge golden path `start_combat` → advance to PC turn → `combat_attack` → `combat_end`; real isolated workspace + roster PC + `grave-ghoul:1`.
- [x] **V4 absorption** — remove skipped `test_bridge_valid_grave_ghoul` from `test_combat_monster_validation.py`; happy start covered by I1.
- [x] Domain spec § Combat integration golden path (APP-030) + changelog on close.

## Expected files

- `app/tests/test_combat_integration.py` — **new** (I1 + shared fixture helpers)
- `app/tests/test_combat_monster_validation.py` — remove V4 skip test
- `tmp/app-combat-play-spec.md` — § APP-030 integration tests

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-combat-play-spec.md`](../app-combat-play-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-030-combat-integration-test`

_Add implementation notes, blockers, or PR links here._
