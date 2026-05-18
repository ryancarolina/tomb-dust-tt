# Wave 5 — QA checklist

Stories: TD-022, TD-023, TD-053, TD-054, TD-055, TD-056, TD-057, TD-063, TD-070, TD-071, TD-073, TD-090 (+ TD-024 partial, TD-091 partial).

## Commands

```powershell
python tools/validate_content.py
python tools/av_grid.py validate
python -m pytest tools/rules_engine
```

## Track A — Gear & encumbrance

- [ ] `systems/equipment/gear.md` — starting kits (6 Tier-1 classes), weight table
- [ ] `systems/core/derived-stats.md` — encumbrance summary + extract link
- [ ] `systems/character/creation-steps.md` — links to starting kits

## Track B — Extraction economics

- [ ] `systems/world/extraction.md` — claims, stash, faction rep, scoring, extract encumbrance
- [ ] `systems/factions/delvers-registry.md` — insurance + Moot
- [ ] `systems/factions/README.md` — rep track −3 to +3

## Track C — Loot

- [ ] `data/loot/tables.json` — hazard / skirmisher / elite / boss
- [ ] `data/schemas/loot.schema.json`
- [ ] Trade goods in `gear.md`

## Track D — Combat content

- [ ] `systems/combat/traps.md` — 3 example traps
- [ ] `systems/combat/hazards.md` — poison + disease
- [ ] `systems/monsters/humanoids.md` — 5 templates
- [ ] Location encounter refs: breley-keep, shadowfen-ruins

## Track E — Integration

- [ ] `docs/engine-integration.md` — repo contract
- [ ] `RULESCHANGELOG.md` — rulesVersion 1.0.0

## Sign-off

- [x] Track A Gear
- [x] Track B Extraction
- [x] Track C Loot
- [x] Track D Combat content
- [x] Track E Integration

**Status:** DONE (2026-05-18)
