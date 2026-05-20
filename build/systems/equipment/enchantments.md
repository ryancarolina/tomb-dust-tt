# Enchantments

## Pattern 1 — designed SKU

Full `itemId` embeds enchant (e.g. `leather-bracers-epic-flame-warding`). Catalog row has `enchantments: ["flame-warding"]`, `immutable: true`. Pack instance has no `enchantIds`.

## Pattern 2 — crafted

Base SKU + instance `enchantIds: ["flame-warding"]`. Catalog `enchantable: true`, `maxEnchants: 1`.

## Display

Pattern 1: catalog `displayName`. Pattern 2: base name + enchant `displaySuffix` values in stable order.

## Immutable

No disenchant or add/remove enchants. Sell at catalog `costGp` (enchant value baked in).

Data: `build/data/enchantments/enchantments.json`.
