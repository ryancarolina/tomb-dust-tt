# Rules changelog

Semver for **rulesVersion** on mechanical JSON exports. AV-GRID topology uses `av-grid.json` **`version`** separately.

## 1.2.0 — 2026-05-19 (Magic system)

- **41 spells** (+11 tier 3/6), `schools.json`, `starting-spells.json`, spell schema v1.1 (`effectType`, dynamic save DC)
- Casting: INT arcane / SPI divine; Spell Focus +1 DC; saves vs Magical Defense
- Engine: `SpellService`, sheet `knownSpells`, `process_beat` auto-cast, ash-shade monster
- App: known spells in GM context; creation defaults for Apprentice/Novice

**Bump rationale:** spell JSON shape and character sheet fields; engines must reload spells and migrate sheets.

## 1.1.0 — 2026-05-18 (Wave 6)

**Content expansion — no combat math changes.**

- Tier 4–5 spells (+12) and wild magic table (TD-032)
- Divine casting documented; five divine spells (TD-034)
- Magic item identify/craft rules (TD-035)
- Wilderness encounter tables HL / WM / SF (TD-064)
- Registry ledger JSON examples (TD-065)
- NPC services catalog (TD-074)
**Bump rationale:** minor content semver — new spell IDs and data files; attack/save formulas unchanged from 1.0.0.

## 1.0.0 — 2026-05-18

**Baseline game-ready bundle** (rules canon + extraction loop + reference engine).

- d20 canon: skill bonus tier table, gritty crits, Fortune = advantage, Magical Defense
- Combat loop: initiative, surprise, conditions, dying, rest
- Equipment: 17 weapons JSON, armor, starting kits, encumbrance
- Magic: 6 schools, 18 starter spells JSON
- Progression: deed promotions JSON, tier-1 creation
- Extraction: 5-phase loop, 6-segment threat clock, claims, stash, faction rep, loot tables
- World: MVP corridor AV-GRID, Breley site graph, reference rules engine + tests

**Bump policy:** patch for typo/clarification; minor for new content without math change; **major** for attack/save/AC formula changes.
