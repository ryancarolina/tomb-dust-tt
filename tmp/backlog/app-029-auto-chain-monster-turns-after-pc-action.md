# APP-029: Auto-chain monster turns after PC action

| Field | Value |
|-------|-------|
| **ID** | APP-029 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-combat-play-spec.md`](../app-combat-play-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Monster turns should follow PC action automatically.

## Acceptance criteria

- [x] After PC combat action, auto-run monster turns until PC turn again.

## Expected files

- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-combat-play-spec.md`](../app-combat-play-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

Implemented in `Orchestrator._combat_auto_chain()` — calls `bridge.run_combat_monster_turns()` after PC `combat_action` until PC turn or combat end. Wired from `_combat_turn` and `_combat_llm_loop_inner`.
