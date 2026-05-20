# Equipment slots

Fourteen slots. One item per slot. Equipping displaces the incumbent to pack (unequipped).

## Slot IDs

| Slot | Typical items |
|------|----------------|
| `mainHand` | weapons, torches |
| `offHand` | weapons, shields, bucklers |
| `helm` | helmets, hoods |
| `shoulders` | pauldrons, cloaks (often +0–1 AC) |
| `chest` | body armor |
| `bracers` | bracers, vambraces |
| `gloves` | gauntlets, gloves |
| `legs` | greaves, leggings |
| `boots` | boots |
| `ring1`, `ring2` | rings |
| `trinket1`, `trinket2` | holy symbols, foci, charms |

**Legacy:** v2 used `body` — engine migrates to `chest`.

## Displacement

| Action | Result |
|--------|--------|
| Equip to occupied slot | Unequip incumbent to pack |
| Equip `two-hand` weapon | Unequip `offHand` |
| Equip shield / off-hand | Block if `mainHand` has `two-hand` property |
| Bow / crossbow | `mainHand` only; `offHand` free |
| Versatile weapon | One-hand default; two-hand mode occupies both when declared |

## AC

Sum `acBonus` from all equipped armor-slot items + shield. AGI cap from **heaviest** worn armor category. See [armor.md](armor.md) and [../combat/calculations.md](../combat/calculations.md).

## Kind → slot

| Kind | Slots |
|------|-------|
| `weapon` | `mainHand`, `offHand` |
| `armor` | `helm`, `shoulders`, `chest`, `bracers`, `gloves`, `legs`, `boots` |
| `shield` | `offHand` |
| `jewelry` | `ring1`, `ring2`, `trinket1`, `trinket2` |
| `gear`, `ammo`, `consumable`, `material` | not equippable |

Catalog `allowedSlots[]` overrides defaults when present.
