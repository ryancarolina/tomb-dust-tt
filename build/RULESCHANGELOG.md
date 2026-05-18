# Rules changelog

Semver for **rulesVersion** on mechanical JSON exports. AV-GRID topology uses `av-grid.json` **`version`** separately.

## 1.1.0 — 2026-05-18 (Wave 6)

**Content expansion — no combat math changes.**

- Tier 4–5 spells (+12) and wild magic table (TD-032)
- Divine casting documented; five divine spells (TD-034)
- Magic item identify/craft rules (TD-035)
- Wilderness encounter tables HL / WM / SF (TD-064)
- Registry ledger JSON examples (TD-065)
- NPC services catalog (TD-074)
- Game-ready gate: [backlog/game-ready-checklist.md](backlog/game-ready-checklist.md)

**Bump rationale:** minor content semver — new spell IDs and data files; attack/save formulas unchanged from 1.0.0.

## 1.0.0 — 2026-05-18

**Baseline game-ready bundle** after Waves 1–5 backlog execution.

- d20 canon: skill bonus tier table, gritty crits, Fortune = advantage, Magical Defense
- Combat loop: initiative, surprise, conditions, dying, rest
- Equipment: 17 weapons JSON, armor, starting kits, encumbrance
- Magic: 6 schools, 18 starter spells JSON
- Progression: deed promotions JSON, tier-1 creation
- Extraction: 5-phase loop, 6-segment threat clock, claims, stash, faction rep, loot tables
- World: MVP corridor AV-GRID, Breley site graph, reference rules engine + tests

**Bump policy:** patch for typo/clarification; minor for new content without math change; **major** for attack/save/AC formula changes.
