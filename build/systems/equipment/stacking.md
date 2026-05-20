# Stacking

| Category | Stackable | Pack shape |
|----------|-----------|------------|
| Equipment | No | One instance per row; no `quantity` |
| Ammo, materials | Yes | `quantity`; merge on `(itemId, enchantIds)` |
| Consumables (rations) | Yes | `quantity` + stack-level `uses` |

Two identical daggers = **two instances**, not one stack.

## Partial transfer / sell

Stash deposit/withdraw and fence sell accept optional `quantity` on stack rows.
