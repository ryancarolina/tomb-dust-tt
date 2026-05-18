# Wave 6 — QA checklist

Stories: TD-032, TD-034, TD-035, TD-064, TD-065, TD-074, TD-091, TD-092.

## Commands

```powershell
python tools/validate_content.py
python tools/av_grid.py validate
python -m pytest tools/rules_engine
```

## Track A — Magic expansion

- [ ] `systems/magic/spells.md` — tier 4–5 catalog + wild magic d6
- [ ] `data/spells/spells.json` — 30 spells
- [ ] `systems/deities/README.md` — divine casting (SPI)
- [ ] `systems/equipment/gear.md` — magic items (TD-035)

## Track B — Encounters & ledger

- [ ] `data/encounters/wilderness.json` — HL, WM, SF tables
- [ ] `systems/world/extraction.md` — random encounter procedure
- [ ] `data/av-grid/ledger-examples.json` — 4 ledger entries
- [ ] `data/av-grid/README.md` — ledger field spec

## Track C — NPC services (TD-074)

- [ ] `systems/npcs/README.md` — service template
- [ ] All 5 NPC pages use services table

## Track D — Game-ready gate

- [ ] `backlog/game-ready-checklist.md` — M7 sign-off
- [ ] `RULESCHANGELOG.md` — 1.1.0

## Sign-off

- [x] Track A Magic
- [x] Track B Encounters
- [x] Track C NPCs
- [x] Track D Game-ready

**Status:** DONE (2026-05-18)
