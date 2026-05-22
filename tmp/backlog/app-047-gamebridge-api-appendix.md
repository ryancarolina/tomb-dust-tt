# APP-047: GameBridge API appendix

| Field | Value |
|-------|-------|
| **ID** | APP-047 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-gamebridge-spec.md`](../app-gamebridge-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Bridge method ok/error shapes not documented.

## Acceptance criteria

- [ ] Document each bridge method ok/error shapes in spec appendix.

## Expected files

- `app/gm/bridge.py`
- `tmp/app-gamebridge-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-gamebridge-spec.md`](../app-gamebridge-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

- Defer full appendix pass until after [APP-086](app-086-inventory-quest-item-bridge.md) + [APP-085](app-085-quest-system-key-npc-quests-ui.md) land (new bridge methods).
- Inventory/quest methods documented in economy + quest specs first; APP-047 sweeps all bridge shapes.
