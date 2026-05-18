# Combat walkthrough (TD-016)

Full round example tracing canon from [calculations.md](calculations.md), [encounter.md](encounter.md), and [conditions.md](conditions.md). Regression numbers are tested in `tools/rules_engine/test_core.py`.

## Setup

**Site:** Breley undercrypt (`32-C-UG-1`) — see [data/sites/breley-undercrypt.json](../../data/sites/breley-undercrypt.json).

**PC — Tomas, Militia (tier 1)**

| Stat | Value |
|------|-------|
| STR 14 (+2), AGI 12 (+1), STA 12 (+2), SPI 10 (+0) | |
| PB | +2 |
| Swordsmanship | level 4 → **skill bonus +1** |
| Dodge | level 1 → **+1 AC** when alert |
| HP | 10 + (STA × 5) = **70** |
| AC (alert) | 10 + studded +3 + AGI +1 + Dodge +1 = **15** |
| AC (flat-footed) | 10 + studded +3 = **13** |
| Weapon | Longsword 1d8 + STR + skill bonus |

**Monster — Grave Ghoul (skirmisher)** — [grave-ghoul.json](../../data/monsters/grave-ghoul.json)

| Stat | Value |
|------|-------|
| AC | 13 |
| HP | 28 |
| Claw | +5 to hit (d20 + 5), 1d6+3 slashing + DC 12 STA or Paralyzed |

## Surprise

The ghoul wins Stealth vs Tomas's passive Perception. Tomas starts **surprised**: flat-footed AC **13**, no action on his first turn.

## Initiative

| Combatant | Roll | Mod | Total |
|-----------|------|-----|-------|
| Tomas | 15 | +1 AGI | **16** |
| Ghoul | 8 | +2 AGI | **10** |

Tomas acts first each round after surprise ends, but round 1 he cannot act while surprised.

## Round 1

**Ghoul (surprise round).** Claw: d20 **12** + 5 = **17** vs flat-footed AC 13 → **hit**. Damage 1d6+3 (GM rolls 4+3 = 7). STA save: d20 **7** + 2 + 2 = 11 vs DC 12 → **fail** → Tomas **Paralyzed** until end of ghoul's next turn.

**Tomas.** Surprised — no move, action, or bonus action.

## Round 2

**Tomas.** Paralysis ended at end of ghoul's prior turn; now **alert**. Attack: d20 **17** + 2 STR + 2 PB + 1 skill = **22** vs AC 13. Beats AC by 9 → **gritty crit** (extra weapon die). Longsword: 1d8(7) + 2 + 1 + crit 1d8(7) = **17** damage. Ghoul HP 28 → **11**.

**Ghoul.** Claw: d20 6 + 5 = 11 vs AC 15 → **miss**.

## Round 3

**Tomas.** Attack: d20 10 + 5 = 15 vs AC 13 → hit (not crit). Damage 1d8(5) + 2 + 1 = **8**. Ghoul HP 15 → **7**.

**Ghoul.** Claw: d20 14 + 5 = **19** vs AC 15 → hit. Damage 1d6+3 = **9**. Tomas HP 70 → **61**. STA save succeeds — no Paralyzed.

## Round 4 — drop to 0

**Tomas.** Miss (total 12 vs AC 13).

**Ghoul.** Claw hits for **9** (HP 52). Claw hits again (Multiattack not in stat block — GM adds second claw only if using elite variant). For this walkthrough, one more hit: **9** damage → HP **43**. *(Abbreviated; full attrition continues.)*

**Later in the fight:** Tomas at **6 HP**. Ghoul claw for **6** → HP **0**. Tomas gains **Dying** ([conditions.md](conditions.md)): unconscious, prone, auto-fail STR/AGI saves.

**Stabilization attempt:** Ally Field Medic (Medicine bonus action, DC 13) — d20 11 + mods = fail.

**Death:** Ghoul claw for **4** damage while Tomas is **Dying** → **death** (no further HP tracking). See [meta/death-and-persistence.md](../meta/death-and-persistence.md) for account stash and inheritance.

## Validation

The engine tests pin these key totals:

- Initiative 16 vs 10
- Surprise hit 17 vs flat-footed 13
- Round 2 crit total 22, damage 17 (fixed RNG seed 0)
- Paralyze save fail on d20 7 + 4 = 11 vs DC 12
- Dying → damage while Dying → death flag

Run: `python -m pytest tools/rules_engine`
