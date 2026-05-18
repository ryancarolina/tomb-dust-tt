# Wave 2 fix pass — QA checklist

Run after Wave 2 review fixes. All gates should pass before Wave 3.

## Grep gates (expect zero matches)

```powershell
rg -i "Heavy Armor Use" systems/
rg -i "spell slots" systems/
rg -i "Thievery|Survival / Navigation" systems/
rg -i "Each level provides" systems/skills/
rg -i "physical defense|Magical Attack Score" systems/
```

## Content gates (expect matches)

```powershell
rg -i "Opportunity attacks" systems/combat/encounter.md
rg -i "## Dying" systems/combat/
rg -i "Armor Proficiency" systems/combat/encounter.md
rg "skillId" data/schemas/weapon.schema.json
rg "baseMpClass" data/schemas/character.schema.json
rg "MP" systems/world/extraction.md
```

## Structural

```powershell
python tools/av_grid.py validate
python -c "import json; [json.load(open(f)) for f in ['data/schemas/common.schema.json','data/schemas/weapon.schema.json','data/schemas/character.schema.json','data/schemas/monster.schema.json']]; print('schemas OK')"
```

## Manual trace

| Scenario | Doc path |
|----------|----------|
| PC drops to 0 HP in combat | `encounter.md` → Dying → `conditions.md` |
| Stabilize with Field Medic | `encounter.md` + `mental-skills.md` |
| PC dies on map | `encounter.md` Death → `meta/death-and-persistence.md` |
| Longsword damage, Swordsmanship 6, STR +3 | `weapons.md` + `calculations.md` → 1d8+5 |
| Peasant HP/MP at creation | `derived-stats.md` examples |

## Sign-off

- [x] Armor Proficiency naming fixed
- [x] Opportunity attacks defined
- [x] Dying / stabilization / death (TD-014)
- [x] Paralyzed adjacent crit clarified
- [x] Extraction skill names + MP
- [x] Weapon schema skillId required + property enum aligned
- [x] Character schema baseMpClass
- [x] Combat README cross-links

**Status:** DONE (post Wave 2 review)
