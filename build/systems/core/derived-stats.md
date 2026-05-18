# Derived stats

## Health and mana

### Base HP

**Base HP = 10** for every character at creation. It does not change when you advance class tier; only **STA** and magic items / techniques modify total HP afterward.

**HP = Base HP + (STA × 5)**

### Base MP

**Base MP** depends on your **Tier-1 (base) class** at creation. Changing to a higher tier class does not alter Base MP unless the table below says otherwise (GM may rule a full re-origin story).

| Tier-1 class | Base MP |
|--------------|---------|
| Peasant | 5 |
| Laborer | 4 |
| Urchin | 6 |
| Apprentice | 12 |
| Militia | 5 |
| Novice | 10 |

**Mana (MP) = Base MP + (INT × 3)**; regeneration per turn from SPI (+ skill bonuses where noted). See [skills/magic-skills.md](../skills/magic-skills.md) for Mana Control and other modifiers.

### Worked examples (creation)

Assume standard **1d10** attribute rolls with no racial adjustments. Skill bonuses at creation are +0.

**Peasant** — STA 10, INT 10, Base MP 5  
- **HP:** 10 + (10 × 5) = **60**  
- **MP:** 5 + (10 × 3) = **35**

**Militia** — STA 12, INT 8, Base MP 5  
- **HP:** 10 + (12 × 5) = **70**  
- **MP:** 5 + (8 × 3) = **29**

**Apprentice** — STA 8, INT 14, Base MP 12  
- **HP:** 10 + (8 × 5) = **50**  
- **MP:** 12 + (14 × 3) = **54**

### Monsters

Player characters use the formulas above. **Monsters use flat HP** (and explicit move, AC, and attacks) from their stat blocks — not Base HP + (STA × 5). See [monsters/README.md](../monsters/README.md).

### Rest recovery (summary)

Full rules: [combat/encounter.md](../combat/encounter.md#rest-and-recovery).

| Rest | Where | HP | MP | Other |
|------|-------|----|----|-------|
| **Short** (~1 hr) | Hidden, no active threat (GM); mid-delve OK | SPI mod + Endurance level, once per character per short rest | SPI mod + Mana Control level, once per character per short rest | **Stable** at 0 HP → **1 HP** after full short rest |
| **Long** (8 hr) | Safe hub only; not mid-delve | To maximum | To maximum | Once-per-day abilities refresh; **Fortune** refreshes at **session start**, not long rest |

---

## Movement

**Movement:** AGI score in grid spaces per turn, minus **armor movement penalty** (minimum 2). See [equipment/armor.md](../equipment/armor.md).

## Armor Class (AC)

**AC = 10 + armor AC + agility bonus + shield bonus + Dodge bonus (if alert) + misc**

**Agility bonus** = AGI modifier, **limited by armor category** when wearing armor:

| Armor category | AGI to AC |
|----------------|-----------|
| None / clothes | Full AGI mod |
| Light | Full AGI mod |
| Medium | AGI mod **capped at +2** |
| Heavy | **No** AGI mod |

When **flat-footed**, agility bonus and Dodge benefits do not apply (armor and shield still apply).

## Carrying capacity

**Capacity = STR × 10** encumbrance units. Full weight table, over-cap penalties, and extract-phase rules: [equipment/gear.md](../equipment/gear.md#encumbrance-td-023).

| Load | Effect (summary) |
|------|------------------|
| **At or under cap** | Normal movement and checks |
| **Over cap** | Speed −2 (min 2); disadvantage on Stealth and Acrobatics |
| **Extract over cap** | Each extract scene: drop 1 cargo item **or** +1 Extract threat clock segment ([world/extraction.md](../world/extraction.md)) |

Coin weight: **1 unit per 50 gp** carried.

## Attribute quick reference

| Attribute | Combat / exploration |
|-----------|----------------------|
| STR | Melee damage; STR checks (Athletics, lift, break) |
| AGI | Ranged attacks; AC (if armor allows); movement; DEX-style checks |
| STA | HP; CON-style saves and Endurance checks |
| INT | Spell attacks; arcane DC; knowledge checks |
| SPI | Spell save DC defense; willpower; Perception-style spiritual senses |
| LUC | Fortune pool only |

## Checks (standard form)

**d20 + ability modifier + proficiency bonus (if applicable) + skill bonus**

Set DC by difficulty (see [skills/skill-checks.md](../skills/skill-checks.md)). Attacks and saves use the same modifier logic; attacks compare to **AC**, saves compare to an effect **DC**.

Resolution flow: [resolution.md](resolution.md).
