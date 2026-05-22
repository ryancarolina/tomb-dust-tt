# APP-025: Registry hub loop integration test

| Field | Value |
|-------|-------|
| **ID** | APP-025 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Need automated test for hub preparation → ingress → delve → extract.

## Acceptance criteria

- [x] `app/tests/test_registry_hub_loop.py` exercises bridge-direct loop: bootstrap at **`32-C`** / **`preparation`** → **`enter_dungeon`** (`32-C-UG-1` or `undercrypt`) → **`exit_dungeon`** → **`set_phase("extract")`**.
- [x] Test asserts **`mode=dungeon`** + **`phase=delve`** after entry; **`mode=surface`** + **`phase=delve`** after exit; **`phase=extract`** after `set_phase`.
- [x] Test asserts **`events`** `phase.set` rows for **`preparation→ingress→delve`** during `enter_dungeon`.
- [x] Domain spec § Registry hub loop integration test (APP-025) synced; changelog entry on close.

## Expected files

- `app/tests/test_registry_hub_loop.py`
- `tmp/app-exploration-delve-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

- Extend after [APP-085](app-085-quest-system-key-npc-quests-ui.md): optional scenario — Breley hub → Holt offer → accept → undercrypt → signet turn-in.
- Depends on exploration/delve basics (APP-021/024) and ideally [APP-087](app-087-narrow-site-entry-sanitizer-quest-prose.md) for Holt Q&A on surface.
