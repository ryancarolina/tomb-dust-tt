# APP-086: Inventory bridge — quest item checks and delivery

| Field | Value |
|-------|-------|
| **ID** | APP-086 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-economy-inventory-play-spec.md`](../app-economy-inventory-play-spec.md) |
| **Created** | 2026-05-22 |

## Summary

The engine has **Inventory v3** (list, equip, grant_loot, stash, vendor) but no app-layer way to **query pack by item id**, **remove a specific instance on turn-in**, or treat **quest items** as a first-class catalog kind. [APP-085](app-085-quest-system-key-npc-quests-ui.md) (quest delivery) is blocked until this lands.

Domain layer already has `remove_instance` / `remove_first_by_item_id` in `play/tomb_gm/domain/inventory.py` — they are **not** exposed on `GameBridge`.

## Acceptance criteria

### Bridge + tools

- [ ] `GameBridge.has_pack_item(item_id, character_id?)` → `{ ok, found, instanceIds[], quantity }`.
- [ ] `GameBridge.remove_pack_item(instance_id | item_id, character_id?)` → `{ ok, removed }` — persists sheet; uses domain helpers.
- [ ] `GameBridge.deliver_quest_item(quest_id, item_id, npc_id, character_id?)` — validates active quest objective, removes item, advances quest (thin wrapper; quest service owns rules — or delegate entirely to quest module from APP-085).
- [ ] GM tools (or quest-only tools) documented in economy spec; orchestrator normalizes args (APP-080).

### Catalog / schema

- [ ] Align `inventory-item.schema.json` `kind` enum with content schema docs — add **`quest`** (README mentions it; pack enum today omits it).
- [ ] Add v1 quest item(s) to `build/data/gear/gear.json` (e.g. `holt-signet-ring` for Holt quest stub).
- [ ] Quest items: not sellable at vendor; not stash-depositable (engine guard or tag `quest`).

### Tests

- [ ] `grant_loot` / manual pack insert → `has_pack_item` true.
- [ ] `remove_pack_item` → absent from `list_inventory`.
- [ ] Deliver with wrong quest state → `{ ok: false, error }`.

### Spec

- [ ] Update [`app-economy-inventory-play-spec.md`](../app-economy-inventory-play-spec.md) + changelog.
- [ ] Update [`app-gamebridge-spec.md`](../app-gamebridge-spec.md) method table.

## Expected files

- `app/gm/bridge.py`
- `app/gm/tools.py` _(if deliver exposed as tool)_
- `play/tomb_gm/domain/inventory.py` _(only if guards needed)_
- `build/data/gear/gear.json`
- `build/data/schemas/inventory-item.schema.json`
- `play/tomb_gm/tests/test_inventory_quest.py` _(new)_
- `tmp/app-economy-inventory-play-spec.md`
- `tmp/app-gamebridge-spec.md`

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-085 | **blocks** — quest turn-in needs remove + has_item |
| APP-080 | related — typed tool args |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-086 --task inventory-quest-bridge
python tmp/backlog/claim_ticket.py release APP-086 --done
```
