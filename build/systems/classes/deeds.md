# Deed-based class promotion

Machine-readable deeds: [`data/deeds/promotions.json`](../../data/deeds/promotions.json). Narrative requirements remain in [progression.md](progression.md).

## Counter types

| Type | Tracks |
|------|--------|
| `combats_survived` | Encounters ended with PC conscious |
| `weapon_mastered` | Distinct weapon skills at level 3+ |
| `spells_cast` | Successful spell resolutions |
| `traps_disarmed` | Successful Trap Handling vs trap |
| `pickpocket_success` | Successful Sleight of Hand thefts |
| `gold_held` | Peak coin on character sheet |
| `healing_rituals` | Successful Medicine or divine spell heals out of combat |
| `days_tracked` | Wilderness tracking scenes completed |
| `guild_joined` | Story flag (Thieves' guild, etc.) |

## Promotion procedure (TD-043)

1. Character meets **all** counters for a **target class** path at the next tier.
2. Narrative requirements from [progression.md](progression.md) must also be satisfied (GM or story flags).
3. **Promotion:** update `classTier`, `classId`, PB per [combat/calculations.md](../combat/calculations.md).
4. **Optional:** +1 skill at level 1 ([creation-steps.md](../character/creation-steps.md)).
5. **Deeds reset** for that tier transition only; account deeds (Registry commendations) persist separately.

## Multi-path rule

At tier 2+, only **one** class id is active. Switching paths requires GM deed for retraining; counters for the new path start at 0 unless the GM rules partial credit.

## Example

**Militia → Footman:** `combats_survived` ≥ 10, `weapon_mastered` ≥ 2, `flag:military_training` true → tier 2, class `footman`, PB stays +2 until tier 3.
