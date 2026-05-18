# Wave 3 — QA checklist

Stories: TD-040, TD-041, TD-052, TD-013, TD-081, TD-082.

## Commands

```powershell
python tools/validate_content.py
python tools/av_grid.py validate
```

## Content gates

- [ ] `systems/character/creation-steps.md` — 3 skills, class filter, worked example
- [ ] `systems/world/extraction.md` — Collapse clock section (6 segments)
- [ ] `systems/combat/encounter.md` — Rest and recovery section
- [ ] `data/weapons/weapons.json` — 17 weapons, all with skillId
- [ ] `data/monsters/` — ≥3 JSON files

## Sign-off

- [x] TD-040 Starting skills
- [x] TD-041 Base class selection
- [x] TD-052 Collapse clock
- [x] TD-013 Rest recovery
- [x] TD-081 Monster JSON (3 examples)
- [x] TD-082 Weapon JSON (17 entries)

**Status:** DONE (2026-05-18)
