# Spec — App Economy & Inventory Play

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress (engine layer shipped)  
**Owns:** economy/inventory tools in orchestrator, stats UI for gold/pack

**Engine contract:** [`build/docs/engine-integration.md`](../build/docs/engine-integration.md) § Inventory v3 — not a separate tmp spec.

---

## Spec

App exposes engine inventory v3 + hub economy through tools and narration.

### Player actions (via GM tools)

| Action | Tool / bridge |
|--------|----------------|
| List pack | `list_inventory` |
| Equip / unequip | `equip_item`, `unequip_item` |
| Use consumable | future `use_item` tool (engine: `inventory use`) |
| Loot on search/combat | `grant_loot` — **never narrate items without it** |
| Stash at hub | `list_stash` (surface + `services.stash` cell) |
| Buy / sell | `list_vendor`, `buy_item`, `sell_item` |
| Death | account stash + stashGp persist; body loot on corpse |

### Hub gates

- Stash / vendor / fence only when `party_state.mode === "surface"` and AV-GRID cell has matching `services.*`.

### Engine status (app-relevant)

| Milestone | Shipped | App touchpoint |
|-----------|---------|----------------|
| M1 Equip 14-slot + AC | ✅ | bridge equip tools, system_prompt |
| M2 Loot persists | ✅ | `grant_loot` tool |
| M3 Account stash | ✅ | `list_stash`, hub gates in prompt |
| M4 Vendor buy/sell | ✅ | buy/sell tools |
| M5 Extraction loop | ✅ | vertical slice test in engine |

### Deferred (engine — document in engine-integration, not a separate tmp spec)

- Encumbrance (TD-023/TD-057)
- Composable loot-table v2 JSON (v1 adapter active)
- Ammo auto-decrement on ranged attacks (manual `inventory use` for now)
- Biome/monster lootTableRef content pass

### UI (future)

- Pack summary in sidebar; equip state reflected in stats.

---

## Task checklist

- [x] Bridge: list/equip/unequip/grant_loot/buy/sell/stash/vendor
- [x] Tools + system_prompt stash/grant_loot rules
- [x] Creation kit cost deducted in `_auto_finalize`
- [ ] UI inventory strip (pygame-ui spec)
- [ ] GM tool for `use_item` / consumable use
- [ ] Playtest: buy → equip → delve → die → stash persists on new character

---

## Tests

```bash
python -m pytest play/tomb_gm/tests/test_stash.py test_economy.py test_loot.py test_extraction_slice.py -q
```

| Scenario | Asserts |
|----------|---------|
| Sell equipped | blocked until unequip |
| Fence sale | Registry tax + ash tithe (engine) |
| `grant_loot` | pack persists; `list_inventory` matches |
| Hub stash | blocked when `mode=site` |

---

## File map

| File | Role |
|------|------|
| `gm/bridge.py` | Economy/inventory methods |
| `gm/tools.py` | Tool schemas |
| `gm/system_prompt.py` | Economy rules for LLM |
| `gm/orchestrator.py` | `_auto_finalize` kit cost |
| `ui/panels/stats.py` | Gold display |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; engine status merged from retired inventory-economy spec |
| 2026-05-19 | Engine Phases 0–6 complete (historical — see engine-integration.md) |
