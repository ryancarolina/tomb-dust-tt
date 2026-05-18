# Wave 4 — QA checklist

Stories: TD-030, TD-031, TD-033, TD-042, TD-043, TD-084, TD-085, TD-016, TD-060, TD-061, TD-062.

## Commands

```powershell
python tools/validate_content.py
python tools/av_grid.py validate
python tools/av_grid.py build-index
python -m pytest tools/rules_engine
```

## Track A — Magic (TD-030/031/033)

- [ ] `systems/magic/README.md` — casting rules
- [ ] `systems/magic/schools.md` — 6 schools
- [ ] `systems/magic/spells.md` — 18 starter spells
- [ ] `data/spells/spells.json` — machine-readable catalog
- [ ] `data/schemas/spell.schema.json`

## Track B — Deeds (TD-042/043/084)

- [ ] `systems/classes/deeds.md` — counter types + promotion procedure
- [ ] `data/deeds/promotions.json` — 8 tier-1→2 and tier-2→3 paths
- [ ] `data/deeds/example-character-state.json`
- [ ] `data/schemas/deed.schema.json`

## Track C — Rules engine (TD-085/016)

- [ ] `tools/rules_engine/core.py` — d20, attack, damage, conditions
- [ ] `tools/rules_engine/test_core.py` — E1 + walkthrough numbers green
- [ ] `systems/combat/walkthrough-example.md` — full round narrative

## Track D — Grid + sites (TD-060/061/062)

- [ ] MVP corridor cells 33-C → 46-C in `av-grid.json`
- [ ] Stamped delves have `dangerRating` + `links.monsters`
- [ ] `data/sites/breley-undercrypt.json` — ≥5 rooms, edges
- [ ] `data/schemas/site.schema.json`

## Sign-off

- [x] Track A Magic
- [x] Track B Deeds
- [x] Track C Rules engine
- [x] Track D Grid + sites

**Status:** DONE (2026-05-18)
