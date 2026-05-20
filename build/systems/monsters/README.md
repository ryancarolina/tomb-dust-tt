# Monsters

Creatures use the same **d20** resolution as characters ([core/resolution.md](../core/resolution.md), [combat/calculations.md](../combat/calculations.md)).

## Threat tiers

| Tier | Role | Typical AC | Typical HP | Attack bonus |
|------|------|------------|------------|--------------|
| **Hazard** | Swarms, vermin, weak singles | 11–13 | 5–18 | +2 to +4 |
| **Skirmisher** | Standard encounter creature | 13–15 | 22–45 | +4 to +6 |
| **Elite** | Leader, veteran, large specimen | 15–17 | 46–85 | +6 to +8 |
| **Boss** | Dungeon finale, regional terror | 17–20 | 90+ | +8 to +11 |

## Stat block template

Each entry includes **lore**, one or more **stat blocks**, **tactics**, and **treasure/hooks**.

```
### [Name] ([Tier])
| | |
| **AC** | (armor category + AGI cap per [equipment/armor.md](../equipment/armor.md)) |
| **HP** | |
| **Move** | grid squares / turn |
| **PB** | used for save DCs only |

| STR | AGI | STA | INT | SPI |
| mods |

**Traits** — passive abilities  
**Downed behavior** — how the creature treats **Downed** or **Dying** PCs (see below)  
**Actions** — attacks: +X to hit vs AC, damage on hit; saves: DC 8 + PB + ability mod
**Reactions** / **Legendary** (elite/boss only, optional)
```

**Monster attacks** list **+hit** and **damage** explicitly (e.g. *+5 to hit, 1d8+2 slashing*). **Save DC** = 8 + monster PB + relevant modifier.

**Flat-footed:** Humanoid monsters lose AGI to AC when surprised; beasts in light armor follow the same rule. Heavy natural armor (plates, shells) keeps full AC when flat-footed.

## Downed behavior

Every monster stat block declares **`downedBehavior`** in JSON (and in markdown **Tactics** when relevant). This governs target choice and fiction when PCs are **Downed** (conscious, 0 HP) or **Dying** (unconscious, 0 HP).

| Behavior | Target priority | Typical fiction |
|----------|-----------------|-----------------|
| **ignore** | Standing PCs only; skips Downed/Dying | Beasts hunting active prey; disciplined guards |
| **feast** | Prefers Downed/Dying; keeps attacking them | Ghouls, carrion feeders, hungry undead |
| **execute** | Prefers Downed/Dying; first hit on Dying often lethal | Assassins, knights finishing wounded |
| **drag** | Prefers Downed; attempts to haul prey away | Stalkers, slavers, burrowers |
| **flee** | Stops fighting if all standing PCs are down | Cowards, ambushers who got their kill |

**Damage at 0 HP** still follows PC rules: any hit on Downed or Dying kills unless already dead. **Execute** monsters prioritize helpless targets; **feast** monsters may ignore fresh threats to feed.

Author new monsters with an explicit behavior; default authored blocks use **ignore** unless the creature’s lore says otherwise.

## Index

### Ether and shadow
- [aetherial-beasts.md](aetherial-beasts.md)
- [ether-larva.md](ether-larva.md)
- [etherwraiths.md](etherwraiths.md)
- [shadowkin.md](shadowkin.md)
- [gloomspiders.md](gloomspiders.md)

### Element and environment
- [sky-serpents.md](sky-serpents.md)
- [mirelings.md](mirelings.md)
- [fen-stalker.md](fen-stalker.md)
- [crystal-stalker.md](crystal-stalker.md)
- [ash-wight.md](ash-wight.md)
- [rust-slime.md](rust-slime.md)

### Undead and constructs
- [grave-ghoul.md](grave-ghoul.md)
- [hollow-knight.md](hollow-knight.md)
- [ironbound-sentinel.md](ironbound-sentinel.md)

### Humanoids
- [humanoids.md](humanoids.md) — guard, footman, knight, cultist, bandit templates

### Beasts
- [thornwolf.md](thornwolf.md)
- [dusk-bat-swarm.md](dusk-bat-swarm.md)

## Habitat by region

| Region | Common creatures |
|--------|------------------|
| Heartlands | Grave ghoul, hollow knight, rust slime |
| Whispering Marches | Thornwolf, ether larva, aetherial beast |
| Shadowfen | Mireling, fen stalker, etherwraith, gloomspider |
| Skyreach | Sky serpent, dusk bat, ash wight |
| Underdeep | Crystal stalker, ironbound sentinel, rust slime |
| Frostspire | Ash wight (frost), etherwraith (cold) |
| Black Vale (sealed) | Shadowkin, etherwraith |

World map: [world/aventhar-overview.md](../world/aventhar-overview.md).

**Content audit (TD-072):** All index entries above include d20 stat blocks as of Wave 5; stub gaps filled for ether/shadow/fen lines used in MVP corridor and Shadowfen delves.
