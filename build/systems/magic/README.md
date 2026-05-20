# Magic

- [schools.md](schools.md) — six schools, divine vs arcane casting
- [spells.md](spells.md) — spell catalog (tiers 1–6; 41 spells in JSON)
- [skills/magic-skills.md](../skills/magic-skills.md) — Spellcasting, Magical Defense, Mana Control, Magical Knowledge
- [combat/calculations.md](../combat/calculations.md) — spell attack, save DC, Magical Defense
- [world/ether.md](../world/ether.md) — Ether in the setting

**Machine-readable spells:** [`data/spells/spells.json`](../../data/spells/spells.json)

## Casting (TD-033)

| Step | Rule |
|------|------|
| **Known spells** | Class + skill level gate (see spells.md); Apprentice/Novice start with 2 spells from allowed schools |
| **Cast time** | Per spell: `action`, `bonus action`, or `reaction` |
| **MP spend** | Deduct **mpCost** when the cast completes; Mana Efficiency reduces by 1 (min 1) |
| **Concentration** | Spells tagged **concentration** — only one at a time; broken by damage (DC 10 or half damage, whichever higher, STA save) or incapacitation |
| **Attack / save** | Arcane: INT mod + PB + Spellcasting bonus. Divine school: **SPI mod** instead of INT |
| **Save DC** | 8 + casting mod + PB (same mod as attack for that spell's tradition) |

## Tier gating (TD-032)

| Rule | Detail |
|------|--------|
| **Learn** | Spell **tier** must be ≤ your **class tier** (1–6) |
| **Cast** | Pay **mpCost**; tier 4–5 spells typical at class tier 4–5 (Knight, Cleric, Mage, Sorcerer paths) |
| **Expert / master** | At tier 4+, gain +1 known spell from any school you have access to; at tier 5+, may learn one **tier 5** spell |

## Wild magic (Sorcerer / Ether)

**Wild Surge** (tier 5 Ether) and high **EP** exposure use the d6 table in [spells.md](spells.md#wild-magic-table). Counts toward Sorcerer deed counters (`survived_magical_mishap`, `schools_mastered`).
