# Skill check system

## Skill check formula

**d20 + ability modifier + proficiency bonus (if class-relevant) + skill bonus** vs **DC**

- **Skill bonus** by skill level: see [combat/calculations.md](../combat/calculations.md) ( +0 at levels 1–2 up to +4 at 9–10 ).
- **Ability modifier** for the skill’s governing attribute (see each skill file). Use **AGI mod** instead of “AGI / 2”; use **SPI mod** for willpower and spiritual skills, etc.

Untrained use: **d20 + ability modifier** only (no skill bonus, no PB unless the GM rules the class covers it).

## Difficulty Class (DC)

| Difficulty | DC | Typical challenge |
|------------|-----|-------------------|
| Easy | 10–12 | Novice (skill 1–3) can succeed with luck |
| Medium | 13–15 | Trained character (skill 3–6) |
| Hard | 16–18 | Experienced (skill 5–8) |
| Very hard | 19–22 | Near master (skill 7–10) |
| Extreme | 23+ | Masterpiece tasks |

The GM sets DC from task difficulty and circumstances (cover, time pressure, tools).

## Skill XP

Each **successful** check grants **1 Skill XP** when the task DC is **appropriate for your skill level**:

| Skill level | Award XP when DC is at least |
|-------------|------------------------------|
| 1–3 | 10 |
| 3–6 | 13 |
| 5–8 | 16 |
| 7–10 | 19 |
| 9–10 | 23 |

Example: Lockpicking 4 succeeds vs DC 12 → **1 XP**. Same roll vs DC 9 → success but **no XP**.

Gold is required for advancement beyond skill level 5 (see [progression.md](progression.md)).

## Example

**Thalia** picks a lock (Medium, DC 14).

- Lockpicking **2** (+0 skill bonus)
- AGI **14** (+2 mod)
- Tier 2 Thief, PB **+2**

**Roll:** d20 + 2 + 2 + 0 = d20 + 4. She rolls **12** → total **16** → **success**, DC met for XP (14 ≥ 13 band for her level).

## Standard check line (skill files)

Skill entries use this shorthand:

**Check:** d20 + [ability] mod + PB + [Skill name] skill bonus vs DC

Attack entries use **vs AC** instead of DC. See [core/resolution.md](../core/resolution.md).
