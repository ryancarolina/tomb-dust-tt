# Encounters and turn order

Combat assumes a **square grid** (see [core/resolution.md](../core/resolution.md) — cover, flanking, reach). One square ≈ 5 ft unless the map notes otherwise.

## Initiative

At the **start of each round**, every **living participant** in the encounter rolls **initiative** fresh:

**Initiative = d20 + AGI mod + initiative bonuses**

| Source | Bonus |
|--------|-------|
| **Dodge** skill 9–10 (alert) | +2 |
| **Battlefield Awareness** | +1 per 2 skill levels (round down) |
| Circumstance | Per ability, trait, or GM (e.g. advantage on the roll) |

Record each total for **that round only**. **Turn order** runs from highest to lowest initiative; when a creature’s turn ends, the next creature in order acts until every living participant has acted. Then the round ends and **everyone rolls initiative again** for the next round.

The delver who reacted fastest to **start the fight** is not guaranteed to act first in later rounds — wounds, footing, spells, and pressure change who is quickest as the encounter progresses.

**Defeated** creatures (0 HP, dead, or removed from the encounter) do not roll and do not act.

### Round flow

1. **Roll initiative** for all living participants (apply tie-breakers; record order).
2. Each participant acts in order: movement → action → bonus action (if any); **reactions** may occur anytime.
3. When the last participant in order finishes, the round ends.
4. If combat continues, return to step 1 with **new initiative rolls**.

### Tie-breaking

If two or more totals match on the same round’s roll:

1. Higher **AGI modifier** acts first.
2. Still tied: higher **unmodified d20** on that round’s initiative roll.
3. Still tied: **player characters** before monsters; among NPCs, GM picks order.

## Surprise and alert status

Before **round 1** initiative is rolled, resolve **surprise**:

1. Compare **Stealth** (hiding side) to passive **Perception** (SPI mod + PB + Perception skill bonus, or a fixed passive score for monsters), or run a group Stealth vs Perception contest as the GM prefers.
2. Any creature that did **not** notice a threat it could reasonably perceive starts combat **surprised**.

**Surprised** creatures are **flat-footed** until the end of their **first turn** in the encounter (see [core/resolution.md](../core/resolution.md) — no AGI to AC, no Dodge benefits). They cannot move or take **actions** or **bonus actions** on that first turn; they may still use a **reaction** if a rule allows it before their turn ends.

When surprise ends (or if the creature was never surprised), it is **alert** for AC and Dodge unless another rule applies (unconscious, bound, unseen attacker, etc.).

Techniques such as **Alertness** (cannot be surprised while conscious) or **Uncanny Dodge** (once per long rest, act alert even if surprised) override surprise where noted.

## Action economy

On **your turn**, you normally have:

| Resource | Limit |
|----------|-------|
| **Movement** | Up to your speed in squares (see below) |
| **Action** | One |
| **Bonus action** | One (only if you have an ability, spell, or technique that uses it) |
| **Free object interaction** | One |
| **Reaction** | One per round (see glossary) |

You may **split movement** before and after your action. Unused movement does not carry over.

### Movement

**Speed (squares per turn) = AGI score − armor movement penalty** (minimum **2**).

Armor penalties: see [equipment/armor.md](../equipment/armor.md) (medium −2, heavy −4; light/none 0). **Armor Proficiency** reduces movement penalty (see [combat-skills.md](../skills/combat-skills.md)); apply trained reductions before the minimum-2 floor.

- **Difficult terrain:** each square costs **2** squares of movement.
- **Standing from prone:** costs half your speed (round down), minimum 1 square.
- **Grappled, Restrained, Paralyzed, Stunned:** see [conditions.md](conditions.md) — movement may be 0 or blocked.

### Action

Your main **action** on your turn. Common choices:

| Action | Summary |
|--------|---------|
| **Attack** | One or more weapon attacks if a rule allows (Multiattack, extra attack techniques); each attack uses the d20 vs AC formula in [calculations.md](calculations.md). |
| **Cast a spell** | Per spell timing (action, bonus action, or reaction). |
| **Dash** | Gain extra movement equal to your speed this turn. |
| **Disengage** | Your movement this turn does not provoke [opportunity attacks](#opportunity-attacks). |
| **Dodge** | Until your next turn, attacks against you have disadvantage if you can see the attacker; you gain +2 AC vs attacks you cannot see. Requires alert status for full benefit. |
| **Help** | Grant advantage on one ally’s next ability check or attack against a target within reach before your next turn. |
| **Hide** | Stealth check to become unseen (GM sets DC). |
| **Ready** | Choose an action and a trigger; use your **reaction** when the trigger occurs. |
| **Search** | Perception or Investigation check to find hidden objects or creatures. |
| **Use an object** | Interact with a second object, operate a device, drink a potion, etc. (beyond your free interaction). |

The GM may allow improvised actions at comparable cost.

### Bonus action

A **bonus action** is a smaller combat action taken on your turn **in addition** to your normal action. You have **at most one bonus action per turn**, and only when a spell, technique, trait, or item explicitly says “bonus action.”

Examples elsewhere in the rules: reload shortcuts, shield-adjacent techniques, shadow **Merge**, stabilizing a dying ally. If nothing grants a bonus action, you do not take one.

### Reaction

A **reaction** is a single response **outside your turn**, triggered by a defined event ([opportunity attack](#opportunity-attacks), **Ready**, shield block, Counterspell, etc.). You have **one reaction per round**; it refreshes at the **start of your turn**.

If you are **Stunned** or otherwise unable to act, you cannot take reactions until the condition ends.

### Free object interaction

Once per turn, you may interact with one object for free—for example draw or sheathe a weapon, open an unlocked door, pick up a dropped item, or hand an object to an adjacent ally. This can happen during movement or as part of another action. A second interaction requires the **Use an object** action.

## Glossary (frequency)

| Term | Resets when |
|------|-------------|
| **Once per round** | Start of your next turn (same encounter). |
| **Once per combat** | When the encounter ends (no further hostiles, or GM declares combat over). |
| **Once per day** | After a **long rest** in a safe hub (see [Rest and recovery](#rest-and-recovery)). |
| **Long rest** | 8 hours in a **safe hub**; restores HP and MP to max and refreshes once-per-day limits. Not available mid-delve. |
| **Short rest** | ≈ 1 hour pause; baseline HP/MP recovery and some skill limits (see [Rest and recovery](#rest-and-recovery)). |
| **Stable** | A creature at 0 HP that has been stabilized (see [Dying](#dying-and-death)); not conscious but no longer worsening. Wakes at **1 HP** after 1 hour of care or a full short rest. |

## Rest and recovery

Out-of-combat recovery uses **short rest** (~1 hour) and **long rest** (8 hours). HP and MP totals: [core/derived-stats.md](../core/derived-stats.md).

### Short rest (~1 hour)

Each character may benefit from **one short rest** per delving day (or per 24 hours in downtime) unless a technique says otherwise.

During a short rest, each **conscious** character recovers **once**:

| Resource | Recovery |
|----------|----------|
| **HP** | SPI mod + **Endurance** skill level (minimum 0) |
| **MP** | SPI mod + **Mana Control** skill level (minimum 0) |

Healing magic, potions, and out-of-combat skills (e.g. **Field Medicine**, once per target per short rest) are **separate** from this baseline.

#### Mid-delving

Inside an active site, a short rest is allowed only when the party is **hidden**, **not in combat**, and the GM agrees there is **no active threat** (no patrol en route, no collapse clock ticking down on them, etc.). If interrupted, the rest fails; the GM decides whether it counts as spent.

**Stable** creatures (see [Dying and death](#dying-and-death)) who remain unconscious through a full short rest wake at **1 HP** without spending the conscious HP recovery above.

### Long rest (8 hours)

A **long rest** requires **8 hours** of rest with light activity in a **safe hub**—a Registry town, licensed dormitory, patron manse, or anywhere the party has crossed back past the **ingress boundary** with salvage ([world/extraction.md](../world/extraction.md)). **Not available mid-delve.**

After a long rest, each character:

| Effect |
|--------|
| **HP** | Restored to maximum |
| **MP** | Restored to maximum |
| **Once-per-day** abilities and techniques | Refreshed |
| **Fortune pool** | **Does not** refresh here—refreshes at **session start** only ([core/resolution.md](../core/resolution.md)) |

## Opportunity attacks

When a creature you can see **leaves your reach** (moves from adjacent to non-adjacent without starting adjacent this turn), you may use your **reaction** to make **one melee weapon attack** against it.

- The attack uses the normal d20 vs **AC** formula ([calculations.md](calculations.md)).
- **Disengage** on the mover’s turn prevents opportunity attacks from that movement.
- Techniques such as **Tumble** (Acrobatics) allow moving through enemy spaces without provoking.
- Creatures with **0 speed** or that cannot act do not threaten reach.

## Dying and death

### Massive trauma (instant death)

If a single hit deals damage **≥ 3 × the target's current HP** (before that hit is applied), the target **dies immediately**—no 0 HP roll, no Dying state.

*Example:* at **3 HP**, **9+ damage** on one hit = instant death.

### Dropping to 0 HP (consciousness roll)

If a creature is reduced to **0 HP** and is not already dead:

1. Roll **STA save:** `d20 + STA mod` vs DC **12**.
2. **Success** → **Downed** (see [conditions.md](conditions.md)): conscious at 0 HP; may **heal self** (e.g. **Mend Light**), receive ally aid, or **Disengage** / flee—**no attacks**.
3. **Failure** → **Dying**: unconscious, prone, cannot act.

**Any damage** while at **0 HP** (Downed or Dying) causes **death** immediately.

### Stabilization (Dying only)

| Method | Action | Effect |
|--------|--------|--------|
| **Medicine check** | Action, DC **13** | Target becomes **Stable** at 0 HP (unconscious; no longer Dying) |
| **Field Medic** (Medicine 3+) | Bonus action | Same as successful Medicine stabilize |
| **Healer's kit** | — | Advantage on the Medicine check to stabilize |

**Stable:** unconscious; does not worsen. After **1 hour** of care or a **short rest**, wakes at **1 HP** unless magic says otherwise.

Healing above **0 HP** removes **Downed**, **Dying**, and **Stable**.

### Death

A creature **dies** when:

- A single hit deals **≥ 3 × current HP** (massive trauma);
- It takes **any damage** while at **0 HP** (Downed or Dying);
- It remains **Dying** when the **encounter ends** and receives no stabilization within **1 minute**;
- A monster **downed behavior** or trait kills a helpless target (see [monsters/README.md](../monsters/README.md));
- A monster dies at 0 HP by default (most monsters); or
- The GM declares fatality (environment, execution, etc.).

**Player characters:** death **ends the run**. The **corpse and all body gear** stay at the death site as a lootable world feature. The player starts a **new game** with a fresh character—**account stash and stashGp persist** for the successor; no body gear, rep, deeds, or map inheritance. See [meta/death-and-persistence.md](../meta/death-and-persistence.md).

## Rest and recovery

| Rest type | Duration | Where | Effect |
|-----------|----------|-------|--------|
| **Short rest** | ≈ 1 hour | Hidden, no active hostiles (GM); not during **collapse clock** segment 5+ | Recover **SPI mod + Endurance skill level** HP (once per character per rest); recover **SPI mod + Mana Control skill level** MP (once per rest) |
| **Long rest** | 8 hours, light activity | **Safe hub** only ([extraction.md](../world/extraction.md) — Registry town, patron vault; not inside a delve) | Restore **HP** and **MP** to max; refresh **once per day** abilities |

**Fortune (LUC):** refreshes at **session start**, not on long rest ([resolution.md](../core/resolution.md)).

**Stable (0 HP):** after stabilization, 1 hour of care or a short rest wakes the creature at **1 HP** (see [Dying](#dying-and-death)).

Mid-delve long rests are **not** allowed unless the table agrees the site is a certified safe room (rare story exception).

## Running the encounter

1. Resolve **surprise** and **flat-footed** where relevant (round 1 only, before initiative).
2. At the **start of each round**, roll **initiative** for all living participants and record turn order.
3. Each participant acts in order: movement → action → bonus action (if any); reactions may occur anytime.
4. Resolve attacks with the d20 pipeline in [core/resolution.md](../core/resolution.md) and [calculations.md](calculations.md).
5. Apply **conditions** from [conditions.md](conditions.md) as they are inflicted or end.
6. When the round ends, repeat from step 2 unless combat is over.
7. End combat when one side surrenders, flees, or is defeated; reset **once per combat** limits.

Monster stat blocks list **Move** in squares per turn and may reference conditions by name—use this file and [conditions.md](conditions.md) for the shared definitions.
