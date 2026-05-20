# Spells

**Tier** gates availability: spell **tier ≤ class tier** (1–6). **MP** paid on cast. See [README.md](README.md) for timing, concentration, and [tier gating](README.md#tier-gating-td-032).

Format: **Tier · MP · Time · Range · Effect**

---

## Starter catalog (tier 1–3)

### Pyromancy (arcane)

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Ember Touch** | 1 | 1 | action | touch | Spell attack; **1d8** fire on hit |
| **Ash Veil** | 2 | 2 | action | 30 ft | 10 ft radius; creatures DC 12 STA or **Poisoned** 1 round |
| **Firebolt** | 2 | 2 | action | 60 ft | Spell attack; **1d10** fire on hit |

### Ward (arcane)

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Aegis Spark** | 1 | 1 | action | self | +2 AC vs spells until start of your next turn |
| **Seal Threshold** | 2 | 2 | action | touch | Lock a door; DC 14 Lockpicking or spell to open |
| **Ward Circle** | 3 | 3 | action | 10 ft | 10 ft radius; undead have disadvantage entering until end of next turn |

### Biomancy (arcane)

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Thorn Prick** | 1 | 1 | action | 30 ft | Spell attack; **1d6** piercing on hit |
| **Sap Mend** | 1 | 1 | action | touch | Restore **1d4 + INT mod** HP |
| **Entangle** | 2 | 2 | action | 60 ft | 10 ft patch; DC 12 STR or **Restrained** until end of next turn |

### Necromancy (arcane)

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Grave Chill** | 1 | 1 | action | 30 ft | Spell attack; **1d8** necrotic; target speed −10 ft until end of next turn |
| **Corpse Speak** | 1 | 1 | action | touch | Ask one dead creature one question; DC 12 SPI or lies |
| **Fear Gasp** | 2 | 2 | action | 15 ft cone | DC 12 SPI or **Frightened** until end of next turn |

### Ether (arcane)

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Static Lash** | 1 | 1 | action | 30 ft | Spell attack; **1d6** force |
| **Veil Peek** | 1 | 1 | action | self | See EP-touched creatures within 30 ft for 1 minute |
| **Disrupt Weave** | 2 | 2 | reaction | 30 ft | Target casting spell: DC 12 INT save or spell fails (MP still spent) |

### Divine (SPI tradition)

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Mend Light** | 1 | 1 | action | touch | Restore **1d6 + SPI mod** HP |
| **Consecrate Ground** | 1 | 1 | action | 5 ft | 5 ft square holy until rest; undead disadvantage to enter |
| **Turn Ash** | 2 | 2 | action | 30 ft | One undead DC 12 SPI or **Frightened** 1 round |

---

## Expert / master catalog (tier 4–5, TD-032)

Requires **class tier ≥ spell tier**. Two spells per school at expert (tier 4) and master (tier 5) bands.

### Pyromancy

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Inferno Wave** | 4 | 4 | action | 30 ft cone | **3d6** fire; DC 14 STA half |
| **Phoenix Mantle** | 5 | 5 | action | self | **Concentration** 1 min; +2 fire on your spell attacks; resist cold |

### Ward

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Banish Unlife** | 4 | 4 | action | 30 ft | Undead DC 14 SPI or **Frightened** 1 minute |
| **Fortress Sigil** | 5 | 5 | action | touch | **Concentration** 10 min; target **+4 AC** |

### Biomancy

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Overgrowth** | 4 | 4 | action | 60 ft | 15 ft radius difficult terrain; **2d6** piercing, DC 14 STR half |
| **Heartwood Bark** | 5 | 5 | action | self | 10 min; **+3 AC** (natural); resist piercing |

### Necromancy

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Wither** | 4 | 4 | action | 60 ft | Spell attack; **3d8** necrotic |
| **Army of Ash** | 5 | 5 | action | 30 ft | 1 min; summon 2 hazard ash shades |

### Ether

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Veil Tear** | 4 | 4 | action | 30 ft | Spell attack; **2d10** force; **+1 threat clock** on thin-veil sites |
| **Wild Surge** | 5 | 5 | bonus action | self | Roll [wild magic table](#wild-magic-table); Sorcerer deed hook |

### Divine

| Spell | Tier | MP | Time | Range | Effect |
|-------|------|-----|------|-------|--------|
| **Sun Smite** | 4 | 4 | action | touch | Spell attack; **2d8** radiant; **+2d8** vs undead |
| **Sanctuary Hymn** | 5 | 5 | action | 30 ft | 1 min; one ally **+4** on saves vs magical effects |

---

## Wild magic table

Roll **d6** when casting **Wild Surge**, failing a high-Ether save, or on Sorcerer **wild magic deed** scenes:

| d6 | Effect |
|----|--------|
| 1 | **Backlash:** 2d6 force to caster; spell fails |
| 2 | **Flare:** All creatures within 10 ft DC 12 STA or blinded until end of next turn |
| 3 | **Surge:** Reroll spell damage dice; use higher total |
| 4 | **Veil bleed:** +1 threat clock segment if in a delve |
| 5 | **Fortune spark:** Refresh 1 Fortune point (max normal pool) |
| 6 | **Controlled:** Spell resolves normally; count as `survived_magical_mishap` deed |

---

## Sample cast

**Mage (tier 4)** INT 16 (+3), Spellcasting 7 (+3), PB +3, **Inferno Wave**:

- Save DC: 8 + 3 + 3 = **14** STA; damage **3d6** fire.

**Priest (tier 5)** SPI 16 (+3), **Sun Smite**: attack d20 + 3 + 3 + 3 vs AC; **2d8** radiant (+ **2d8** vs undead).

## Adept catalog (tier 3)

| Spell | School | Tier | MP | Notes |
|-------|--------|------|-----|-------|
| **Cinder Lance** | pyromancy | 3 | 3 | 2d6 fire spell attack |
| **Root Snare** | biomancy | 3 | 3 | STR save or Restrained (conc) |
| **Bone Tap** | necromancy | 3 | 3 | Question corpse |
| **Phase Step** | ether | 3 | 3 | Bonus action teleport 15 ft |
| **Ward of Dawn** | divine | 3 | 3 | Allies +2 vs fear |

(Ward school also has **Ward Circle** at tier 3.)

## Archmage catalog (tier 6)

| Spell | School | Tier | MP |
|-------|--------|------|-----|
| **Sunstorm** | pyromancy | 6 | 6 |
| **Adamant Ward** | ward | 6 | 6 |
| **World-Tree Shelter** | biomancy | 6 | 6 |
| **Lich Gate** | necromancy | 6 | 6 |
| **Rift Sever** | ether | 6 | 6 |
| **Avatar of Aven** | divine | 6 | 6 |

JSON mirror: [`data/spells/spells.json`](../../data/spells/spells.json) (41 spells, `rulesVersion` 1.1.0) · schools: [`data/spells/schools.json`](../../data/spells/schools.json)
