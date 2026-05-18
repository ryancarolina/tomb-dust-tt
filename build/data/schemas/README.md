# Tomb Dust entity schemas

Machine-readable definitions for game content that complements human rules in `systems/`. **AV-GRID** remains authoritative for world coordinates in [`../av-grid/av-grid.json`](../av-grid/av-grid.json) ([`../av-grid/schema.json`](../av-grid/schema.json)).

Schemas use **JSON Schema draft 2020-12**, matching the style of `data/av-grid/schema.json`: top-level `type: object`, `additionalProperties: false`, shared patterns in `$defs`, and cross-file `$ref` to `common.schema.json`.

## Content data paths

| Path | Schema | Source docs |
|------|--------|-------------|
| [`../weapons/weapons.json`](../weapons/weapons.json) | [`weapon.schema.json`](weapon.schema.json) | [`systems/equipment/weapons.md`](../../systems/equipment/weapons.md) |
| [`../monsters/*.json`](../monsters/) | [`monster.schema.json`](monster.schema.json) | [`systems/monsters/`](../../systems/monsters/) |
| [`../spells/spells.json`](../spells/spells.json) | [`spell.schema.json`](spell.schema.json) | [`systems/magic/spells.md`](../../systems/magic/spells.md) |
| [`../deeds/promotions.json`](../deeds/promotions.json) | [`deed.schema.json`](deed.schema.json) | [`systems/classes/deeds.md`](../../systems/classes/deeds.md) |
| [`../loot/tables.json`](../loot/tables.json) | [`loot.schema.json`](loot.schema.json) | [`systems/equipment/gear.md`](../../systems/equipment/gear.md) |

Validate from repo root:

```bash
python tools/validate_content.py
```

## Files

| File | Status | Entity |
|------|--------|--------|
| [`common.schema.json`](common.schema.json) | Shared | Slug, semver, `rulesVersion`, abilities, AV address ref |
| [`monster.schema.json`](monster.schema.json) | Draft | Monster (+ embedded stat blocks) |
| [`weapon.schema.json`](weapon.schema.json) | Draft | Weapon |
| [`character.schema.json`](character.schema.json) | Draft (minimal) | Player character |
| [`../weapons/weapons.json`](../weapons/weapons.json) | **Data** | 17 weapons (rulesVersion 1.0.0) |
| [`../monsters/*.json`](../monsters/) | **Data** | Monster stat blocks (≥3 examples) |
| [`spell.schema.json`](spell.schema.json) | Draft | Spell |
| [`deed.schema.json`](deed.schema.json) | Draft | Deed promotion gate |
| [`site.schema.json`](site.schema.json) | Draft | Delve site graph |
| [`../spells/spells.json`](../spells/spells.json) | **Data** | 30 spells (rulesVersion 1.0.0) |
| [`../sites/*.json`](../sites/) | [`site.schema.json`](site.schema.json) | AV-GRID + location docs |
| [`../loot/tables.json`](../loot/tables.json) | [`loot.schema.json`](loot.schema.json) | Danger-tier loot |
| `skill.schema.json` | Planned | Skill definition |
| `item.schema.json` | Planned | Generic item |
| `armor.schema.json` | Planned | Armor / shield |
| `condition.schema.json` | Planned | Condition / status |

## `rulesVersion`

Every content record that affects mechanics should include **`rulesVersion`** (semver, e.g. `1.0.0`):

- Identifies which **rules bundle** the record was written against (d20 resolution, PB cap +4, skill bonus tier table, gritty crits, AC / flat-footed).
- Downstream **game engine** should compare `rulesVersion` to its embedded rules manifest: **warn** on minor drift, **reject or quarantine** on major mismatch (engine policy).
- Distinct from dataset **`version`** on `av-grid.json` (grid topology). Content authors bump `rulesVersion` when combat math or attribute semantics change in `systems/core/` or `systems/combat/`.

## ID convention (slug)

| Rule | Example |
|------|---------|
| Lowercase **kebab-case** | `thornwolf`, `longsword`, `magical-defense` |
| Stable across saves and refs | JSON `id` = markdown filename stem where applicable |
| Pattern | `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` |
| AV-GRID addresses | **Not slugs** — use canonical `id` strings from `av-grid.json` (e.g. `23-A-UG-1`) |

Human docs may use display names; engines resolve by **`id`**.

---

## Entities (field summary)

### Character

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | Save / roster key |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `raceId` | slug | no | → Race catalog (future) |
| `attributes` | STR, AGI, STA, INT, SPI, LUC (scores) | yes | LUC = Fortune only |
| `classTier` | integer 1–6 | yes | Deed tier → PB |
| `classId` | slug | yes | e.g. `warrior`, `knight` |
| `skills` | `{ skillId, level }[]` | yes | Level 1–10 |
| `hp` | `{ current, max, base? }` | yes | Max typically base + STA×5 |
| `mp` | `{ current, max, base? }` | yes | Max typically base + INT×3 |
| `fortune` | `{ current, max }` | no | Session LUC pool |

**Schema:** [`character.schema.json`](character.schema.json)

### Skill

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | e.g. `swordsmanship` |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `category` | enum | yes | combat / magic / mental / … |
| `ability` | STR…SPI | yes | Default check ability |
| `docPath` | string | no | `systems/skills/...` |
| `techniques` | object[] | no | Level 3 / 6 / 9 gates |

**Relationships:** referenced by Character `skills[].skillId`, Weapon `skillId`, Spell schools.

### Spell

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `school` | slug | yes | → magic school |
| `tier` | integer | yes | Spell tier for ID / counter |
| `mpCost` | integer | yes | |
| `castingTime` | string | yes | |
| `range` | string | yes | |
| `duration` | string | no | |
| `attack` | object | no | Spell attack vs AC |
| `save` | object | no | DC = 8 + INT + PB (caster) |
| `effect` | string | yes | Narrative + mechanics |

**Relationships:** cast by Character; save DC uses caster PB + INT.

### Item

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `kind` | enum | yes | gear / consumable / treasure / quest |
| `costGp` | number | no | |
| `weight` | number | no | STR × 10 carry units |
| `tags` | string[] | no | |

**Relationships:** base type; **Weapon** and **Armor** extend item semantics.

### Weapon

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `category` | simple \| martial \| ranged | yes | |
| `damage` | dice notation | yes | e.g. `1d8` |
| `ability` | STR \| AGI | yes | Attack + damage mod |
| `skillId` | slug | yes | Weapon skill for bonus |
| `costGp` | number | no | |
| `properties` | enum[] | no | thrown, versatile, … |
| `rangeFt` | `{ normal, long }` | no | Ranged only |

**Schema:** [`weapon.schema.json`](weapon.schema.json) · Rules: [`systems/equipment/weapons.md`](../../systems/equipment/weapons.md)

### Armor

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `category` | none \| light \| medium \| heavy | yes | AGI cap to AC |
| `acBonus` | integer | yes | Added to AC 10 + … |
| `movePenalty` | integer | no | 0 / −2 / −4 |
| `costGp` | number | no | |
| `shield` | boolean | no | Occupies hand |

**Relationships:** equipped on Character; Monster stat block `armorCategory` for flat-footed behavior.

### Monster

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `docPath` | string | no | `systems/monsters/{id}.md` |
| `lore` | object | no | origin, description, weaknesses |
| `habitat.regions` | string[] | no | Region slugs from av-grid |
| `habitat.addresses` | AvAddress[] | no | Grid ties |
| `statBlocks` | StatBlock[] | yes | One or more variants |
| `treasure` | string[] | no | Hooks / loot text |
| `tags` | string[] | no | |

**StatBlock** (per [`systems/monsters/README.md`](../../systems/monsters/README.md)):

| Field | Type | Required |
|-------|------|----------|
| `id` | slug | yes (variant key) |
| `tier` | hazard \| skirmisher \| elite \| boss | yes |
| `ac`, `hp`, `move`, `pb` | numbers | yes |
| `attributes` | STR…SPI **modifiers** | yes |
| `armorCategory` | enum | no |
| `traits`, `actions`, `reactions`, `legendary` | namedAbility[] | no |

**Schema:** [`monster.schema.json`](monster.schema.json)

### Condition

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | e.g. `flat-footed` |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `duration` | string | no | |
| `effects` | string | yes | Mechanical summary |

**Relationships:** applied to Character or Monster instances at runtime.

### Deed

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `fromTier` | 1–6 | yes | |
| `toClassId` | slug | yes | Unlocks class |
| `requirements` | string[] | yes | Human + engine-checkable gates |

**Relationships:** Character `classTier` / `classId` progression via completed deeds.

### Site

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | slug | yes | Delve / location bundle |
| `rulesVersion` | semver | yes | |
| `displayName` | string | yes | |
| `primaryAddress` | AvAddress | yes | → `av-grid.json` |
| `addresses` | AvAddress[] | no | Sub-areas |
| `dangerRating` | threat tier | no | Aligns with grid |
| `encounters` | `{ monsterId, weight? }[]` | no | |
| `docPath` | string | no | `systems/locations/...` |

**Relationships:** wraps one or more **AvAddress** records; links **Monster** ids for encounters.

### AvAddress

Not duplicated here — **source of truth:** [`../av-grid/av-grid.json`](../av-grid/av-grid.json), schema [`../av-grid/schema.json`](../av-grid/schema.json).

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `47-B-UG-3` |
| `column`, `row`, `surfaceRoot` | | Parsed grid coords |
| `parent`, `childAddresses` | | Tree |
| `layerStack`, `biomes`, `region` | | |
| `dangerRating` | hazard…boss | Encounter tuning |
| `links.location`, `links.monsters` | paths / slugs | Doc + content refs |

**Site** and **Monster.habitat** reference AvAddress by `id` only.

---

## Entity relationships

```mermaid
erDiagram
  AvAddress ||--o{ Site : "primaryAddress / addresses"
  Site ||--o{ Monster : "encounters.monsterId"
  Monster }o--o{ AvAddress : "habitat.addresses"
  Character ||--o{ Skill : "skills.skillId"
  Character }o--|| Deed : "progression"
  Character }o--o{ Weapon : "equipment"
  Character }o--o{ Armor : "equipment"
  Character }o--o{ Condition : "runtime"
  Character }o--o{ Spell : "known / prepared"
  Weapon }o--|| Skill : "skillId"
  Item <|-- Weapon
  Item <|-- Armor
  Monster ||--|{ StatBlock : "embedded"
```

| From | To | Cardinality | Join field |
|------|-----|-------------|------------|
| Character | Skill | N:M | `skills[].skillId` + `level` |
| Character | Deed | N:M | progression log (future) |
| Character | Weapon / Armor | N:M | inventory slots (future) |
| Weapon | Skill | N:1 | `skillId` |
| Site | AvAddress | N:1+ | `primaryAddress`, `addresses[]` |
| Site | Monster | N:M | `encounters[].monsterId` |
| Monster | AvAddress | N:M | `habitat.addresses[]` |
| AvAddress | Monster | N:M | `links.monsters[]` (grid JSON) |
| Spell | Skill | N:1 | school / spellcasting skill |

---

## Validation (local)

From repo root (minimal checks, no extra deps):

```bash
python tools/validate_content.py
```

Optional full JSON Schema validation (e.g. `pip install check-jsonschema`); `validate_content.py` runs it automatically when available:

```bash
check-jsonschema --schemafile data/schemas/monster.schema.json data/monsters/grave-ghoul.json
```

CI integration is future work (TD backlog).

## Related docs

| Topic | Path |
|-------|------|
| d20 / Fortune | `systems/core/resolution.md` |
| PB, skill bonus, attacks | `systems/combat/calculations.md` |
| Monster template | `systems/monsters/README.md` |
| AV-GRID workflow | `data/av-grid/README.md`, `AGENTS.md` |
