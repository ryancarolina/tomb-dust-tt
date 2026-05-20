# Combat calculations

## Proficiency bonus (class tier)

Characters add proficiency bonus (**PB**) on attacks, saves, and checks where their **class tier** applies. Progression is deed-based (see [classes/progression.md](../classes/progression.md)), not character level.

| Class tier | Examples | PB |
|------------|----------|-----|
| 1 | Peasant, Militia, Urchin | +2 |
| 2 | Footman, Scout, Thief | +2 |
| 3 | Warrior, Ranger, Rogue | +3 |
| 4 | Knight, Assassin, Cleric | +3 |
| 5 | Paladin, Shadowblade, Archmage | +4 |
| 6 | Eternal Champion, Ether Lord | +4 |

## Skill bonus (skill level 1–10)

| Skill level | Bonus on trained rolls |
|-------------|------------------------|
| 1–2 | +0 |
| 3–4 | +1 |
| 5–6 | +2 |
| 7–8 | +3 |
| 9–10 | +4 |

**Canon:** this table is the only source for **skill bonus** on d20 attack rolls, skill checks, and saving throws. Individual skill files may scale non-roll effects by **skill level** (1–10) in techniques—never substitute skill level for skill bonus on d20 tests.

Mastery at high levels is expressed through **techniques** at levels 3, 6, and 9 as much as through this bonus.

## Attack rolls

**Melee (STR weapons):**  
`d20 + STR mod + PB + weapon skill bonus` vs **AC**

**Ranged (AGI weapons):**  
`d20 + AGI mod + PB + weapon skill bonus` vs **AC**

**Spell attack:**  
`d20 + casting_mod + PB + Spellcasting skill bonus` vs **AC**

**Casting mod:** **INT** for arcane tradition; **SPI** for divine tradition (see [magic/schools.md](../magic/schools.md)).

**Spell save DC** (when the effect allows a save):  
`DC = 8 + casting_mod + PB + Spellcasting skill bonus` (+1 if **Spell Focus** matches the spell’s school)

**Save vs spell:**  
`d20 + SPI mod + PB + Magical Defense skill bonus` vs caster’s spell save DC (+2 vs one school if **Spell Resistance** matches)

## Magical Defense (SPI)

When a effect is **magical** (spells, most monster spell-like abilities):

- **Saving throw:** `d20 + SPI mod + PB + Magical Defense skill bonus` vs effect DC
- **AC vs spell attack:** your normal AC **+ Magical Defense skill bonus** (applies only to spell attacks, not weapon attacks)

Techniques such as Spell Resistance add circumstance bonuses on top. Untrained characters use `d20 + SPI mod + PB` only.

**Example:** Cleric with SPI +2, PB +3, Magical Defense 5 (skill bonus +2). SPI save vs DC 14: d20 + 2 + 3 + 2. AC vs spell attack 16 (plate) → **18** vs spells only.

## Damage

- **Melee:** weapon damage + STR + skill bonus (unless a skill says otherwise)
- **Ranged:** weapon damage + AGI mod + skill bonus (typical for bows; see skill entry)
- **Spells:** per spell description

**Power Attack** and similar techniques trade attack bonus for damage before rolling.

## AC

See [equipment/armor.md](../equipment/armor.md). Example:

- Knight in plate (+8), shield (+2), alert: AC **20** (10 + 8 + 2; no AGI in heavy)
- Ninja in studded leather (+3), AGI +4, Dodge +2 AC, alert: AC **19** (10 + 3 + 4 + 2)
- Same ninja, flat-footed: AC **13** (10 + 3; no AGI, no Dodge)

## Dodge skill (alert only)

| Dodge level | Benefit |
|-------------|---------|
| 1–2 | +1 AC |
| 3–4 | +2 AC |
| 5–6 | +2 AC; once per round, one attack against you has **disadvantage** |
| 7–8 | +3 AC; disadvantage once per round |
| 9–10 | +3 AC; disadvantage once per round; **+2 initiative** |

## Example exchange

**Attacker:** Tier 3 Warrior, STR 16 (+3), Swordsmanship 6 (+2), longsword 1d8, PB +3  
**Attack:** d20 + 3 + 3 + 2 = **d20 + 8** vs AC 18 → needs 10+ on the die to hit.

**Hit damage:** 1d8 + 3 (STR) + 2 (skill) = 1d8 + 5.

**Crit:** only if natural 20 or total ≥ 23 (beat AC 18 by 5+); then add one extra 1d8.
