# Adventuring gear

General equipment, **encumbrance weights**, **starting kits**, and **trade goods** for delves. Weapons and armor stats: [weapons.md](weapons.md), [armor.md](armor.md). Starting gold: [economy.md](economy.md).

---

## Encumbrance (TD-023)

**Carrying capacity = STR × 10** encumbrance units ([core/derived-stats.md](../core/derived-stats.md)). Count everything worn, wielded, and in packs.

### Weight table (units)

| Item | Units |
|------|-------|
| **Coin** (per 50 gp) | 1 |
| **One-handed weapon** (light, finesse, thrown) | 2 |
| **One-handed martial weapon** | 3 |
| **Two-handed / heavy weapon** | 4 |
| **Light armor** (worn) | 4 |
| **Medium armor** (worn) | 8 |
| **Heavy armor** (worn) | 12 |
| **Shield** | 3 |
| **Adventuring pack** (backpack + bedroll + basic kit) | 6 |
| **Rations** (1 day) | 1 |
| **Waterskin** (full) | 1 |
| **Rope** (50 ft) | 2 |
| **Torch** | 1 |
| **Lantern + oil** | 2 |
| **Healer's kit** | 2 |
| **Thieves' tools** / **lockpicks** | 1 |
| **Climbing kit** | 4 |
| **Spellbook** | 3 |
| **Trade good** (see below) | 1–5 by row |

**Containers:** A **sack** holds up to 10 units of loose cargo; a **chest** holds 30 (not portable during extract without a cart). Pack weight includes contents unless stored in a hub **stash** ([meta/death-and-persistence.md](../meta/death-and-persistence.md)).

### Over capacity (general)

When total carried units exceed **STR × 10**:

| Penalty | Effect |
|---------|--------|
| **Speed** | Effective movement −2 squares (minimum 2) |
| **Stealth / Acrobatics** | **Disadvantage** on checks while over-cap |
| **Extract phase** | See [extraction.md](../world/extraction.md#encumbrance-under-pressure-td-057) — forced drop or clock strain |

Dropping items to get under cap removes penalties immediately.

---

## Starting equipment kits (TD-022)

Each **Tier-1 class** gets a default kit. Costs use listed gear prices; players may swap items within the same **total kit cost** or spend [starting gold](economy.md) for upgrades.

**Formula reminder:** `(Base Class GP + Life Event Modifier) × 1d6` — minimum **0 gp**.

| Tier-1 class | Kit contents | Kit cost |
|--------------|--------------|----------|
| **Peasant** | Club, sling, backpack, bedroll, rations ×5, waterskin, flint and steel, pouch | **13 gp** |
| **Laborer** | Quarterstaff, padded armor, backpack, rope (50 ft), rations ×5, healer's kit | **20 gp** |
| **Urchin** | Dagger, leather armor, thieves' tools, backpack, rations ×3, pouch | **42 gp** |
| **Apprentice** | Quarterstaff, spellbook, ink and quill, herbalism kit, backpack, rations ×5 | **74 gp** |
| **Militia** | Spear, shortsword, studded leather, buckler, backpack, healer's kit, rations ×5, bedroll | **58 gp** |
| **Novice** | Warhammer, leather armor, holy symbol, healer's kit, backpack, rations ×5 | **39 gp** |

### Remaining gold

After taking the standard kit, **remaining gold = starting gold − kit cost**. Typical guidance:

| Remaining | Suggested spend |
|-----------|-----------------|
| **0–15 gp** | Rations, torches, or debt payment |
| **16–40 gp** | Extra healer's kit, rope, or **Registry insurance** pool (15 gp) |
| **41+ gp** | Map stamp down payment, better weapon swap, or **account stash** deposit before first ingress |

Record kit + coin separately on the sheet. Anything carried past **ingress** is body loot until extracted ([death-and-persistence.md](../meta/death-and-persistence.md)).

**Creation link:** [character/creation-steps.md](../character/creation-steps.md)

---

## Trade goods (TD-024 partial)

Salvage IDs for loot tables ([data/loot/tables.json](../../data/loot/tables.json)) and fences.

| ID | Item | Value (gp) | Units |
|----|------|------------|-------|
| `burial-goods` | Mixed grave offerings | 5–20 | 2 |
| `iron-ingot` | Smelted iron (1 lb) | 1 | 2 |
| `gloom-silk` | Gloomspider silk bundle | 50 | 1 |
| `reliquary-shard` | Frost-etched holy fragment | 10 | 1 |
| `shadow-glass` | Shadowkin trade shard | 40 | 1 |
| `tomb-map-scrap` | Partial survey sketch | 15–60 | 1 |
| `registry-seal-chip` | Broken stamp fragment (legal risk) | 0–80 | 1 |
| `fen-peat` | Alchemist peat block | 8 | 3 |
| `veil-crystal` | Thin-veil crystal (fragile) | 25–100 | 2 |

---

## General equipment

### Adventuring gear

| Item | Cost | Units |
|------|------|-------|
| Backpack | 2 gp | (in pack) |
| Bedroll | 1 gp | (in pack) |
| Rope (50 ft) | 1 gp | 2 |
| Torch | 1 gp | 1 |
| Lantern | 5 gp | 1 |
| Oil flask | 1 gp | 1 |
| Flint and steel | 1 gp | — |
| Waterskin | 1 gp | 1 |
| Rations (1 day) | 1 gp | 1 |
| Tent | 10 gp | 5 |

### Tools

| Item | Cost | Units |
|------|------|-------|
| Lockpicks | 25 gp | 1 |
| Climbing kit | 25 gp | 4 |
| Healer's kit | 5 gp | 2 |
| Herbalism kit | 5 gp | 2 |
| Thieves' tools | 25 gp | 2 |
| Holy symbol | 5 gp | 1 |
| Spellbook | 50 gp | 3 |

### Containers

| Item | Cost | Units |
|------|------|-------|
| Pouch | 1 gp | — |
| Sack | 1 gp | 1 empty |
| Barrel | 2 gp | 8 |
| Chest | 5 gp | 10 |

### Mounts (not carried)

Horse 75 gp · Donkey 8 gp · Cart 15 gp · Wagon 35 gp

---

## Magic items (TD-035)

Minor items from skills, delves, or fences. Identify with **Arcana** or **Magical Knowledge** vs item DC.

### Identification

| Item tier | Identify DC | Appraisal (fence offer) |
|-----------|-------------|-------------------------|
| **Minor** | 12 | 50–150% base value |
| **Major** | 16 | GM sets; often quest-locked |
| **Cursed** | 18 | Hidden until identify fails by 5+ |

**Magical Knowledge 3+:** advantage on identify. **Arcana** may substitute for Magical Knowledge on spell-like items.

### Crafting (skill techniques)

| Recipe | Skill | DC | Time | Output |
|--------|-------|-----|------|--------|
| **Holy water** | Medicine or divine spell | 12 | 1 hour | 3 flasks; 1d6 radiant vs undead |
| **Ether ward chalk** | Arcana + Engineering | 14 | 2 hours | 1 use; advantage on first SPI save vs fear in thin-veil |
| **Gloom silk lining** | Engineering | 14 | 4 hours | +1 Stealth in darkness (light armor) |
| **Spell scroll (tier ≤ 2)** | Spellcasting + Magical Knowledge | 12 + tier | 8 hours | One spell, destroys on use |

Costs: base materials = **25 gp × spell tier** or **10 gp × item tier** from trade goods ([trade goods](#trade-goods-td-024-partial)).

### Example minor items

| Item | Effect | Value |
|------|--------|-------|
| **+1 ward amulet** | +1 AC vs spells only | 150 gp |
| **Reliquary shard** | 1/day advantage vs shadow creatures | 10 gp |
| **Healer's charm** | 1/day stabilize as Medicine DC 13 | 25 gp |
| **Black glass shard** | Fence intel (Shadowkin routes) | 40 gp |

Major artifacts (Knight oaths, Archmage staves) are deed rewards — not catalogued here.

