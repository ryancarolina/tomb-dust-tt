# Character creation steps (class & skills)

After you have **final attribute scores** (base rolls, genetic factors, life events, racial adjustments — see [creation.md](creation.md)), complete these two steps before your first delve. **Base HP** is always **10** at creation; **Base MP** comes from your Tier-1 class ([core/derived-stats.md](../core/derived-stats.md)).

---

## Step 1 — Choose a Tier-1 (base) class

Use your final scores to see which **Tier-1 classes** you qualify for. Requirements are listed in [classes/classes.md](../classes/classes.md).

### Eligibility filter

1. Compute **final** STR, AGI, STA, INT, and SPI (LUC is not used for class gates).
2. For each Tier-1 class, check **Stat Requirements** against those scores.
3. Build the **eligible list** — every class whose requirements you meet.

| Tier-1 class | Stat requirements |
|--------------|-------------------|
| Peasant | None |
| Laborer | STR 8+ |
| Urchin | AGI 8+ |
| Apprentice | INT 8+ |
| Militia | STR 8+ **or** AGI 8+ |
| Novice | SPI 8+ |

**Peasant** is always eligible. **Militia** qualifies if **either** STR or AGI meets 8+ (not both required).

### Player choice

- Pick **one** class from your eligible list. This is your **base class** for HP/MP formulas and starting skill themes.
- Record **Base MP** from the [Tier-1 Base MP table](../core/derived-stats.md#base-mp) (Peasant 5, Laborer 4, Urchin 6, Apprentice 12, Militia 5, Novice 10).

**Starting gear:** default kits by class — [equipment/gear.md](../equipment/gear.md#starting-equipment-kits-td-022).

### If nothing fits (except Peasant)

If the only eligible class is **Peasant** and the player wanted a specialist background:

- **Default:** take **Peasant** (no stat gate failed — this is the common-folk baseline).
- **GM override:** the GM may assign another Tier-1 class that narratively fits the character’s history, even if stats are short (e.g. a frail Apprentice who studied under a hedge wizard). Document the exception on the sheet.

---

## Step 2 — Starting skills

Every new character begins with **3 skills**, each at **skill level 1**.

### Rules

| Rule | Detail |
|------|--------|
| **Count** | Exactly **3** skills at creation |
| **Level cap** | **Maximum skill level 1** at creation — no skill may start above 1 |
| **Class tie-in** | At least **1** of the 3 must match your Tier-1 class **Key Abilities** (see table below) |
| **Skill bonus** | Level 1 → **+0** on d20 tests ([combat/calculations.md](../combat/calculations.md#skill-bonus-skill-level-110)) |
| **Duplicates** | No duplicate skills; each pick must be a distinct named skill from the skill lists |

Choose skills only from the canon skill files ([skills/README.md](../skills/README.md)): combat, physical, mental, magic, social, and subterfuge entries.

### Matching Key Abilities to skills

**Key Abilities** in [classes/classes.md](../classes/classes.md) are themes, not a separate skill list. For creation, at least one starting skill must appear in the **matching skills** column for your base class:

| Tier-1 class | Key Abilities (summary) | Matching skills (pick ≥1 from this set) |
|--------------|-------------------------|----------------------------------------|
| Peasant | Farming, animal handling, crafts | Nature, Athletics, Endurance, Engineering |
| Laborer | Heavy lifting, endurance, construction | Athletics, Endurance, Engineering |
| Urchin | Stealth, pickpocketing, street smarts | Stealth, Sleight of Hand, Acrobatics, Deception, Perception, Investigation |
| Apprentice | Literacy, simple spells, craft basics | Lore, Spellcasting, Arcana, Engineering, Magical Knowledge |
| Militia | Basic combat, patrol, local knowledge | Any **combat skill** (e.g. Swordsmanship, Archery, Shield Use), Perception, Lore, Battlefield Awareness |
| Novice | Healing, blessings, religious knowledge | Medicine, Spellcasting, Magical Knowledge, Lore, Persuasion, Etiquette |

The other two starting skills may be **any** valid skills (including another class-matching skill).

### Optional — skill on tier promotion

When you **promote to a new class tier** ([classes/progression.md](../classes/progression.md)), you may gain **+1 additional skill at level 1** (GM table rule). This is optional; groups that prefer slower breadth can skip it. Promoted characters still raise existing skills through XP and gold per [skills/progression.md](../skills/progression.md).

---

## Worked example — Wood Elf Urchin

**Race:** Wood Elf (+2 AGI, +1 SPI) — [races.md](races.md)

**Final attributes**

| Step | STR | AGI | STA | INT | SPI |
|------|-----|-----|-----|-----|-----|
| Base roll (1d10) | 5 | 7 | 8 | 6 | 7 |
| Genetic (1d4) | 0 | +1 | 0 | 0 | +1 |
| Life event | 0 | +1 | 0 | 0 | 0 |
| Racial | 0 | +2 | 0 | 0 | +1 |
| **Final** | **5** | **11** | **8** | **6** | **9** |

**Step 1 — Class filter**

- Peasant — eligible (no requirement)
- Urchin — eligible (AGI 11 ≥ 8)
- Militia — eligible (AGI 11 ≥ 8; STR gate not needed)
- Novice — eligible (SPI 9 ≥ 8)
- Laborer, Apprentice — not eligible (STR/INT gates failed)

**Player choice:** **Urchin** → Base MP **6** ([derived-stats](../core/derived-stats.md#base-mp))

**Step 2 — Starting skills (level 1, skill bonus +0 each)**

| Skill | Level | Class match? |
|-------|-------|----------------|
| Stealth | 1 | Yes (Urchin Key Abilities) |
| Sleight of Hand | 1 | Yes |
| Acrobatics | 1 | No (free pick) |

**Derived stats at creation**

- **HP:** Base HP 10 + (STA 8 × 5) = **50**
- **MP:** Base MP 6 + (INT 6 × 3) = **24**
- **PB:** Tier 1 → **+2** ([combat/calculations.md](../combat/calculations.md))
- **Example check:** Stealth vs Perception → d20 + AGI mod (+0) + PB (+2) + Stealth skill bonus (+0)

---

## Quick reference

| Topic | Doc |
|-------|-----|
| Attribute rolls & races | [creation.md](creation.md) · [races.md](races.md) |
| Tier-1 requirements & Key Abilities | [classes/classes.md](../classes/classes.md) |
| Base HP / Base MP | [core/derived-stats.md](../core/derived-stats.md) |
| Skill bonus by level | [combat/calculations.md](../combat/calculations.md) |
| Skill lists & XP | [skills/README.md](../skills/README.md) |
| Class tier promotion | [classes/progression.md](../classes/progression.md) |
