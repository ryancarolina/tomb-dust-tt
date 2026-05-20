# Item rarity (Option A)

Each tier is a **distinct catalog SKU** (`itemId`). Rarity is not stored on pack instances (except crafted enchants — see [enchantments.md](enchantments.md)).

## Tiers

| Tier | Role |
|------|------|
| `junk` | Salvage, vendor fodder |
| `common` | Starters, general drops (no suffix on ID: `leather`, `warhammer`) |
| `uncommon` | `leather-uncommon` |
| `rare` | `leather-rare` |
| `master` | Faction / crafted rewards |
| `epic` | Boss-adjacent, designed enchant SKUs |
| `legendary` | Unique IDs (`veil-crystal-blade`) |

## ID convention

- Common: `warhammer`, `leather`
- Tiered: `{family}-{tier}` e.g. `leather-rare`
- Junk materials: `{name}-junk` e.g. `burial-goods-junk`
- Designed enchant: `leather-bracers-epic-flame-warding`

## Loot

Tables list explicit `itemId` + weight. `rarityCap` skips entries above cap. See engine `LootResolver`.

## Family field

Optional `family` groups tier ladders for authoring. Loot rolls use **explicit SKUs**, not family random rolls.
