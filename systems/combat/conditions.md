# Conditions

Conditions modify AC, movement, actions, attacks, and saves. They stack unless the same condition would apply twice from one source—in that case, use the strictest duration or DC the GM assigns.

**Escape checks** use the standard form: `d20 + ability mod + PB + skill bonus` vs the listed **DC**. When a stat block gives an escape DC without naming the ability, use **STR** or **AGI** (delver’s choice) unless the effect specifies otherwise.

**Saving throws** against ongoing effects use the same d20 rules as [core/resolution.md](../core/resolution.md). Repeating saves are noted per condition.

---

## Summary table

| Condition | AC | Movement | Actions / attacks | Saves | End / escape |
|-----------|-----|----------|-------------------|-------|--------------|
| **Grappled** | Normal | Speed **0**; cannot move away from grappler | Attacks at **disadvantage** except vs grappler | — | Action: STR or AGI vs escape DC |
| **Restrained** | Normal | Speed **0** | **Disadvantage** on attacks; **advantage** vs you | **Disadvantage** on STR/AGI saves | Action: STR vs DC (or as stated) |
| **Paralyzed** | **Flat-footed** | **0** | Cannot move or act | Auto-**fail** STR/AGI saves | Duration or save at end of turn |
| **Frightened** | Normal | Cannot move **closer** to source | **Disadvantage** while source in line of sight | SPI save vs new fear | Duration or save at end of turn |
| **Stunned** | Normal | **0** | Cannot move, act, or react | Auto-**fail** STR/AGI saves | Duration or save at end of turn |
| **Prone** | Normal | Crawl only (half speed) or stand (half speed) | Melee vs you **advantage**; ranged vs you **disadvantage**; your attacks **disadvantage** | — | Stand as movement |
| **Invisible** | Normal | Normal | Attacks vs you **disadvantage**; your attacks **advantage** | — | Ends when you attack or are hit (unless ability says otherwise) |
| **Poisoned** | Normal | Normal | **Disadvantage** on attacks and ability checks | Often STA vs poison DC | Duration or antidote; see effect |
| **Dying** | Normal | **0** | Unconscious; cannot act | Auto-**fail** STR/AGI saves | Stabilize (Medicine DC 13); see [encounter.md](encounter.md) |

---

## Grappled

A creature, object, or effect holds you in place.

- **Speed 0**; you cannot move away from the grappler (you can still attack or cast if other rules allow).
- Your attack rolls have **disadvantage** unless the target is the grappler or the source of the grapple.
- The grappler can drag you when it moves if it is your size or larger and has speed remaining, moving you into the nearest available space at no extra cost to you.

**Escape (action):** STR or AGI check vs **escape DC**. Use the DC on the stat block when given (e.g. fen stalker **14**, mireling **13**). If no DC is listed: **8 + grappler’s STR mod + grappler’s PB**.

**Ends when:** you succeed on an escape check, the grappler is incapacitated or releases you, or an effect ends the grapple.

**Special:** Some grapples add riders (e.g. cannot breathe while grappled underwater)—apply text on the ability.

---

## Restrained

Bonds, shadow snares, nets, or magic fix you in place.

- **Speed 0.**
- **Disadvantage** on attack rolls.
- Attack rolls against you have **advantage**.
- **Disadvantage** on STR and AGI saving throws.

**Escape (action):** STR check vs DC. Shadowkin **Shadow Snare** uses **DC 13 STR** as an action. Generic fallback: **8 + restrainer’s STR mod + restrainer’s PB** (or effect DC).

**Ends when:** escape succeeds, bonds are destroyed, or duration expires.

---

## Paralyzed

Muscles lock; mind may be aware (GM).

- **Flat-footed** ([core/resolution.md](../core/resolution.md) — no AGI to AC, no Dodge).
- **Speed 0**; cannot take **actions**, **bonus actions**, or **reactions**.
- **Auto-fail** STR and AGI saves.
- Attack rolls against you have **advantage**.
- Any **hit** from an attacker within **1 square** (5 ft) is a **critical hit** (extra weapon damage die) even if the attack total would not normally meet the gritty rule ([core/resolution.md](../core/resolution.md)). Natural 1 still misses if total < AC.

**Ends when:** duration ends (e.g. grave ghoul claw — until end of **next** turn), you succeed on a save at the end of your turn if the effect allows, or a dispel/end condition applies.

---

## Frightened

Overwhelming dread toward a **source** (creature, object, or locale).

- While the source is in **line of sight**, you have **disadvantage** on ability checks and attack rolls.
- You cannot willingly **move closer** to the source (you can still move away or sideways).
- If the source is not visible, you are still frightened but not disadvantaged until you see it again.

**Ends when:** duration ends (e.g. etherwraith **Chill Touch** — until end of **next** turn), you succeed on a **SPI save** at the end of your turn if the effect allows a repeat save, or the source is removed.

---

## Stunned

Concussion, magic, or shock shuts down your turn.

- **Speed 0**; cannot take **actions**, **bonus actions**, or **reactions**.
- **Auto-fail** STR and AGI saves.
- Attack rolls against you have **advantage**.

**Ends when:** duration ends (e.g. **until end of next turn**, or **1 round** for crystal stalker **Shatter** fail), you succeed on a save at end of turn if allowed, or an effect ends the stun.

Crushing Blow / Stunning Fist and similar techniques reference this condition—use the duration on the technique or save line.

---

## Prone

Knocked down or deliberately dropped.

- You are on the ground. **Movement:** crawl at **half speed** (round down), or spend **half your speed** (minimum 1 square) to **stand** on your turn.
- Attack rolls against you from within **1 square** have **advantage**; from farther away, **disadvantage**.
- Your attack rolls have **disadvantage**.

**Ends when:** you stand (costs movement as above) or an effect lifts you.

---

## Invisible

Cannot be seen without special senses.

- Attack rolls against you have **disadvantage** unless the attacker can perceive you (hearing, tremorsense, truesight, etc.—GM).
- Your attack rolls have **advantage**.
- You can still be **flat-footed** if surprised or unaware of an attacker ([core/resolution.md](../core/resolution.md)).

**Ends when:** you **attack** or **cast a spell that affects an enemy**, you take **damage** from an attack (unless an ability says otherwise), or duration expires. Invisible creatures still make noise and leave tracks unless a rule says they do not.

---

## Poisoned

Toxins, venom, or alchemical affliction.

- **Disadvantage** on **attack rolls** and **ability checks**.
- Many poisons also require an initial or ongoing **STA save** vs a DC; failure may add damage, the **Poisoned** condition, or both. Full procedures: [hazards.md](hazards.md).

**Ends when:** duration expires, **antidote** or magic ends the poison, or you succeed on saves noted on the effect (often one save at end of each of your turns for ongoing damage).

---

## Dying

At **0 HP** and not yet dead (see [encounter.md](encounter.md)).

- **Unconscious** and **prone** (unless a rule keeps you standing).
- **Speed 0**; cannot take **actions**, **bonus actions**, or **reactions**.
- **Auto-fail** STR and AGI saves.
- Any **damage** while Dying causes **death**.

**Stabilize:** Medicine check DC **13** (action) or **Field Medic** (bonus action) → **Stable** at 0 HP (unconscious, no longer Dying). Healer's kit grants advantage on the check.

**Ends when:** stabilized, healed above 0 HP, or death.

---

## Conditions and alert status

| Condition | Flat-footed? |
|-----------|------------|
| Paralyzed | **Yes** |
| Unconscious / bound (not listed above) | **Yes** (see [core/resolution.md](../core/resolution.md)) |
| Grappled, Restrained, Frightened, Stunned, Prone, Invisible, Poisoned, Dying | No, unless also surprised or unaware |

**Dodge** and **AGI to AC** apply when **alert** and not denied by Paralyzed or flat-footed rules.

---

## Monster cross-reference

| Condition | Example sources |
|-----------|-----------------|
| Grappled | [fen-stalker.md](../monsters/fen-stalker.md), [mirelings.md](../monsters/mirelings.md) |
| Restrained | [shadowkin.md](../monsters/shadowkin.md) |
| Paralyzed | [grave-ghoul.md](../monsters/grave-ghoul.md) |
| Frightened | [etherwraiths.md](../monsters/etherwraiths.md), [mirelings.md](../monsters/mirelings.md) |
| Stunned | [etherwraiths.md](../monsters/etherwraiths.md), [crystal-stalker.md](../monsters/crystal-stalker.md) |

New stat blocks should name conditions in **bold** and give **DC**, **duration**, or **escape** action when non-standard.
