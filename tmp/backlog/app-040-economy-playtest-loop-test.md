# APP-040: Economy playtest loop test

| Field | Value |
|-------|-------|
| **ID** | APP-040 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-economy-inventory-play-spec.md`](../app-economy-inventory-play-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Buy/equip/delve/death/stash flow untested end-to-end.

## Acceptance criteria

- [ ] Playtest scenario: buy → equip → delve → die → stash persists on new character.

## Expected files

- `app/tests/`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-economy-inventory-play-spec.md`](../app-economy-inventory-play-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

- Extend after [APP-086](app-086-inventory-quest-item-bridge.md) + [APP-085](app-085-quest-system-key-npc-quests-ui.md): quest reward gold + quest item grant/remove in loop.
