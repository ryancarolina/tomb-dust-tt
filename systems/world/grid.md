# Aventhar Grid (AV-GRID)

> **Source of truth:** [`data/av-grid/av-grid.json`](../../data/av-grid/av-grid.json)  
> Validate: `python tools/av_grid.py validate` · Docs: [`data/av-grid/README.md`](../../data/av-grid/README.md)

Every place in Tomb Dust has an **AV-GRID** address: a surface cell, then optional **layers** for depth and other planes. Delvers stamp maps with this code; the Registry tracks deaths and claims by it.

This page explains the system for humans. **Do not add canon addresses here first** — edit JSON, then update this file if needed.

## Surface cell

```
[CC]-[R]
```

| Part | Range | Meaning |
|------|-------|---------|
| **CC** | `01`–`60` | Column (west `01` → east `60`) |
| **R** | `A`–`Z` | Row (south `A` → north `Z`) |

**Scale (table default):** one cell ≈ **12 miles** on a side (~144 sq mi). A city or tower usually occupies one cell; large wilds span many cells.

**Examples**
- `23-A` — Boydon Tower (Whispering Marches, Silverlake)
- `47-B` — Shadowfen Ruins (deadly fen expanse)
- `32-C` — Breley Keep (Heartlands)

## Layers (append with hyphens)

Surface material plane is assumed when no layer is written. Add a layer when the address is not the open surface of that cell.

| Code | Name | Use |
|------|------|-----|
| **UG-**`n` | Underground | Material plane, depth level `n` (`1` = shallow cellars, higher = deeper) |
| **EP** | Ether | Coexistent Ether plane (thin-veil); same CC-R as material |
| **BV** | Black Vale | Sealed rift pocket; anchored to fen cells (see `47-B-BV`) |
| **DP-**`n` | Deep | Native underdeep stratum (use when depth is not mere basement under a surface feature) |
| **SK** | Skyreach | High-altitude layer (cliffs, serpent thermals) above surface column |

### Underground (your example)

| Address | Meaning |
|---------|---------|
| `23-A` | Boydon Tower on the surface |
| `23-A-UG-1` | First underground level under Boydon (undercroft, cisterns) |
| `23-A-UG-2` | Second level (vaulted archives, sealed labs) |
| `23-A-UG-3` | Deepest licensed delve under tower |

### Ether and rift

| Address | Meaning |
|---------|---------|
| `24-B-EP` | Thin-veil overlay in Whispering Woods (same column-row as material `24-B`) |
| `47-B-BV` | Black Vale rift space (Knights’ seal; only via ward breach or story) |
| `47-B-UG-5` | Deep fen catacombs (material underground) |

### Sky layer

| Address | Meaning |
|---------|---------|
| `18-H-SK` | Skyreach Monastery cliffs and thermals above cell `18-H` |

**Rule:** Read addresses **left to right** — surface first, then depth, then non-material planes if stacked (rare): `32-C-UG-2-EP` = deep undercrypt with active veil bleed.

## Subsites (optional)

When several marked sites share one cell, add a short tag **before** layers:

```
[CC]-[R]-[TAG]-[layers…]
```

| Tag | Site (example) |
|-----|----------------|
| `BT` | Boydon Tower (if cell `23-A` also held a hamlet) |
| `BK` | Breley Keep inner bailey |

Most famous locations **own** their cell; subsites are optional detail.

## Registry vs grid

The **Delver's Registry** may also issue a **ledger ID** (survey year + revision) for paperwork:

| Type | Example | Meaning |
|------|---------|---------|
| **AV-GRID** | `47-B-UG-3` | Real world location |
| **Registry stamp** | `REG-1204 rev.C` | Legal claim document (can be forged) |

Hooks like “forged 47-B map” mean a **false chart** for grid cell `47-B`, not a different coordinate system.

## Biome codes (cell metadata)

Record in atlases and location files — **not** part of the address string:

| Code | Biome |
|------|-------|
| HL | Heartland hills / farmland |
| WM | Whispering Marches (woods / lake) |
| SF | Shadowfen marsh |
| SK | Skyreach highlands |
| FR | Frostspire |
| UD | Underdeep (dominant underground) |
| VV | Verdant Vale (hidden) |

## Playable grid map (columns 10–50, rows A–P)

```
         10   15   20   25   30   35   40   45
    P         [Frostfall 14-P]
    N              [Skyreach 18-H / 18-H-SK]
    K
    H
    F
    D
    B    [Boydon 23-A] [Edgecombe 24-A]     [Shadowfen 47-B]
    A         [Silverlake]  [Whispering Woods 24-27, B-D]
              [Verdant Vale ~25-C]
    C              [Ealdormere] [Breley 32-C]
    E                   [Crystaline 31-C-UG-*]
```

West = lower column numbers. Exact borders are GM-flex; **registered delves** use stamped CC-R.

## Canon locations

See **`data/av-grid/av-grid.json`** (`addresses` object) or run:

```bash
python tools/av_grid.py get 47-B
python tools/av_grid.py children 23-A
```

Quick reference: [`index.json`](../../data/av-grid/index.json) lists all ids grouped by surface cell.

## Danger rating (Registry)

Optional tag on stamp: **Hazard / Skirmisher / Elite / Boss** per [monsters/README.md](../monsters/README.md). Cell `47-B` is stamped **Elite+** after repeated TPKs — Mira Ashret wants a re-survey of `47-B-UG-3`, not a rename.

## Designing new content

1. Add entry to **`data/av-grid/av-grid.json`** (parent/child links, biomes, danger, links).  
2. `python tools/av_grid.py validate` and `build-index`.  
3. Update [cell-atlas.md](cell-atlas.md) or location markdown for prose.  
4. List encounters on the location page using the stamped AV-GRID id.

See [extraction.md](extraction.md) for how delvers use stamped coordinates on runs.
