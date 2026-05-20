# Personal inventory vs account stash

## Personal pack

On character `sheet_json`: `goldGp` + `inventory.pack[]` (v3). Carried on delve until extract or death.

## Account stash

On campaign `account_state_json`: `stashGp` + `stash.pack[]` (same v3 shape).

## Hub access

Stash deposit/withdraw, vendors, and fence only when:

- `party_state.mode === "surface"`
- Current AV-GRID address has `services.stash`, `services.vendorIds`, or `services.fence`

Block when `mode` is `site` or `dungeon`.

## Death persistence

See [../meta/death-and-persistence.md](../meta/death-and-persistence.md). **Stash survives**; body pack goes to corpse.

Engine: `play/tomb_gm/domain/inventory.py`.
