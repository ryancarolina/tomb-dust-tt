# Epic E1 — QA checklist

Run from repo root after TD-001 through TD-006. All checks should pass before starting Wave 2 parallel tracks.

## Grep gates (expect zero matches)

```powershell
rg -i "Each level provides" systems/skills/
rg -i "physical defense" systems/
rg -i "Magical Attack Score" systems/
rg -i "percentile" systems/skills/
rg -i "Dodge roll" systems/skills/
rg -i "hit_chance|evasion score|1d12 \+" systems/
```

## Canon trace (manual)

| Test | Expected path |
|------|----------------|
| Tier 3 Warrior, Swordsmanship 6, STR +3, PB +3, longsword | Attack d20+8 vs AC; damage 1d8+5 |
| Thief Lockpicking 4, AGI +2, PB +2, DC 14 | d20+4; success awards XP (DC ≥ 13 band) |
| Mage spell attack, INT +3, Spellcasting 5, PB +3 | d20+8 vs AC; save DC 14 |
| Cleric Magical Defense 5, SPI +2, PB +3 vs DC 14 spell | Save d20+7; AC +2 vs spell attacks only |
| Fortune spend | Advantage (default); pool max(1, 1+LUC mod) per session |

## Files touched (E1)

- `systems/core/README.md`, `resolution.md`
- `systems/combat/calculations.md`
- `systems/skills/README.md`, all six category files
- `AGENTS.md`

## Sign-off

- [x] TD-001 Canonical skill bonus declared
- [x] TD-002 Combat skill damage aligned
- [x] TD-003 Obsolete mechanics removed from skills
- [x] TD-004 Magical Defense in calculations.md
- [x] TD-005 Fortune default = advantage
- [x] TD-006 This checklist complete

**E1 status:** DONE (2026-05-18)
