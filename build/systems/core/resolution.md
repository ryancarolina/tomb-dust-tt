# Resolution

When the outcome is uncertain, Tomb Dust uses a **d20 test**: roll 1d20, add modifiers, compare to a target number.

## D20 test steps

1. Roll **1d20**.
2. Add **ability modifier** (see [attributes.md](attributes.md)).
3. Add **proficiency bonus** when your class tier or training applies (see [combat/calculations.md](../combat/calculations.md)).
4. Add **skill bonus** when using a trained skill (see [skills/skill-checks.md](../skills/skill-checks.md)).
5. Add any **circumstance** bonuses or penalties (cover, flanking, spells, techniques).
6. Compare the total to the target:
   - **Ability check / skill check** → Difficulty Class (DC)
   - **Saving throw** → DC set by the effect
   - **Attack roll** → target **Armor Class (AC)**

## Advantage and disadvantage

- **Advantage:** roll 2d20, use the **higher** result.
- **Disadvantage:** roll 2d20, use the **lower** result.
- If you have both, they cancel; roll one d20.
- Multiple sources of advantage or disadvantage do not stack.

## Attack and damage

1. Resolve **surprise** and **alert** status (see below).
2. Roll **attack:** `d20 + ability mod + proficiency bonus + skill bonus` vs **AC**.
3. On a hit, roll **damage:** weapon die + relevant ability mod + **skill bonus** (see [combat/calculations.md](../combat/calculations.md)). Techniques may add effects keyed to **skill level**, not extra roll bonuses.
4. Apply **critical hits** (see below).

## Critical hits (gritty)

A **critical hit** applies only if the attack **hits** and either:

- the d20 is a **natural 20**, or  
- the attack total **beats AC by 5 or more**

**Critical effect:** roll **one extra weapon damage die** (or unarmed damage die) and add it to the total.

**Natural 1** does not automatically miss. If the total is still equal to or greater than AC, the attack hits (without a crit unless the gritty rule is also met).

Skill checks and saving throws do not use natural 20/1 auto-success rules unless a specific technique says otherwise.

## Alert and flat-footed

| Status | AGI to AC | Dodge skill benefits | Notes |
|--------|-----------|----------------------|-------|
| **Alert** | Per armor rules | Full | Default in combat when aware of threats |
| **Flat-footed** | **None** | **None** | Surprised, unconscious, bound, or attacker unseen (GM) |

**Light-armor** characters rely on agility and Dodge; when flat-footed, only **armor + shield + misc** count toward AC—a prepared ninja is hard to hit; a surprised one is in mortal danger.

**Heavy armor** keeps its full AC when flat-footed; knights trade mobility for staying power.

## Positioning

- **Cover:** +2 AC (half cover) or +5 AC (three-quarters cover) against attacks that go through cover.
- **Flanking:** attacker has **advantage** when an ally threatens the opposite side of the target.
- **Reach / polearms:** can attack from 2 squares away; use positioning to punish careless closes.

Heavy armor imposes **disadvantage** on Stealth checks. Light armor and high AGI favor initiative and repositioning.

## Fortune (LUC)

**Fortune** does not add to rolls. Each session, a character has a **Fortune pool** of `1 + LUC modifier` (minimum 1).

Spend **1 Fortune** to gain **advantage** on one d20 test before rolling.

**Campaign variant (optional):** spend 1 Fortune to **reroll** one d20 after seeing the result instead of advantage—pick one variant for the whole campaign and stay consistent. **Default for software and tables:** advantage.

## Test types (summary)

| Type | Roll | Target |
|------|------|--------|
| Ability / skill check | d20 + mods | DC |
| Saving throw | d20 + mods | Effect DC |
| Attack roll | d20 + mods | AC |

Full formulas: [combat/calculations.md](../combat/calculations.md). Skills: [skills/skill-checks.md](../skills/skill-checks.md). Armor and AC: [equipment/armor.md](../equipment/armor.md).
