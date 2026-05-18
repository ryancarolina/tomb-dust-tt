# AV-GRID (source of truth)

**Canonical data:** [`av-grid.json`](av-grid.json)

All locations, delves, planes, biomes, and Registry metadata for the world grid live here. Markdown under `systems/world/` and `systems/locations/` is **documentation**; when they disagree with JSON, **JSON wins**.

**Agents:** see [AGENTS.md](../../AGENTS.md) for full project rules.

## Files

| File | Purpose |
|------|---------|
| `av-grid.json` | Master dataset (addresses, regions, layer types) |
| `schema.json` | JSON Schema for editors and CI |
| `index.json` | Generated lookup (`addressIds`, `bySurface`) — run `build-index` |

## Address format

```
[CC]-[R]                    surface (e.g. 23-A)
[CC]-[R]-UG-[n]             underground level n
[CC]-[R]-EP|BV|SK           plane or altitude layer
[CC]-[R]-UG-[n]-EP          stacked (example: 32-C-UG-2-EP)
```

## Tooling

From repo root:

```bash
python tools/av_grid.py validate
python tools/av_grid.py parse 47-B-UG-3
python tools/av_grid.py get 23-A
python tools/av_grid.py children 47-B
python tools/av_grid.py build-index
```

## Adding a location

1. Edit `av-grid.json` — add address object(s) with correct `parent` / `childAddresses`.
2. Run `python tools/av_grid.py validate`.
3. Run `python tools/av_grid.py build-index`.
4. Update human docs (`systems/locations/*.md`) to match `links.location` and **AV-GRID** field.

## Encounter linking (TD-061)

Stamped **delve** addresses (`registry.stamped: true`, `tags` includes `delve`) must include:

- `dangerRating` — hazard / skirmisher / elite / boss
- `links.monsters[]` — paths to `systems/monsters/*.md`

Site graphs for navigable delves live in [`../sites/`](../sites/) (e.g. `breley-undercrypt.json` for `32-C-UG-1`).

## Registry ledger format (TD-065)

Human-readable stamp copy on delver maps matches machine examples in [`ledger-examples.json`](ledger-examples.json).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | e.g. `REG-1204 rev.C` — matches `registry.ledgerExample` on address |
| `addressId` | string | yes | AV-GRID id |
| `displayName` | string | yes | Clerk-facing title |
| `stamp.primary` | string | yes | Stamped delve address |
| `stamp.surfaceEntry` | string | yes | Ingress surface cell + gate note |
| `stamp.danger` | string | yes | Hazard / Skirmisher / Elite / Boss |
| `stamp.costGp` | number | yes | Stamp fee |
| `stamp.insuranceGp` | number | no | Optional pool premium |
| `stamp.validDays` | integer | yes | Usually 30 |
| `stamp.veil` | string | no | EP / thin-veil advisory |
| `stamp.issuedAt` | string | no | Clerk or co-stamp faction |
| `notes` | string | no | UI fluff / quest hooks |

UI engines load `ledger-examples.json` by `id` or `addressId` lookup.

## Game integration

Load `av-grid.json` at startup (or embed `index.json` for fast lookups). Resolve delves with:

- `addresses[id]` — full record  
- `bySurface[root]` — all layers under a cell  
- `dangerRating`, `registry`, `links.monsters` — encounter and content paths  

Human-readable rules: [systems/world/grid.md](../../systems/world/grid.md).
