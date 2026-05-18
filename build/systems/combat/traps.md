# Traps

Traps use **Trap Handling** ([skills/subterfuge-skills.md](../skills/subterfuge-skills.md)): `d20 + INT mod + PB + Trap Handling skill bonus` vs trap **DC**. **Complexity** = trap tier (1–10); a handler may attempt traps with complexity ≤ Trap Handling **skill level**.

## Trap definition

| Field | Meaning |
|-------|---------|
| **Detect DC** | Passive Perception or active Search/Investigation to notice before trigger |
| **Disarm DC** | Trap Handling vs this DC; failure may trigger |
| **Trigger** | What sets it off (pressure, tripwire, magic, proximity) |
| **Effect** | Damage, save, condition, or clock tick |
| **Reset** | Manual, automatic after 1 min, or none (one-shot) |

### Complexity by skill level

| Trap Handling level | Max complexity | Typical sites |
|---------------------|----------------|---------------|
| 1–2 | 1–2 | Obvious snares, rusted tripwires |
| 3–4 | 3–4 | Needle locks, counterweights |
| 5–6 | 5–6 | Multi-stage vault traps |
| 7–8 | 7–8 | Ether-linked wards |
| 9–10 | 9–10 | Registry-sealed tomb engines |

**Trap Sense (level 3):** advantage on saves vs traps. **Quick Disarm (level 6):** disarm in half time (one action instead of two for standard traps).

### Procedure

1. **Notice:** passive Perception vs Detect DC, or Search action.
2. **Disarm:** action, Trap Handling vs Disarm DC. Nat 1 or fail by 5+ → trigger unless technique says otherwise.
3. **Bypass:** GM may allow Acrobatics/Athletics to avoid trigger without disarm (same DC as Disarm −2).

Failed disarm on a **stamped delve** often **+1 threat clock** segment ([world/extraction.md](../world/extraction.md)).

---

## Example traps

### Ash needle lock (tomb — Breley undercrypt)

| | |
|--|--|
| **Complexity** | 3 |
| **Detect DC** | 13 (Investigation or Perception) |
| **Disarm DC** | 14 |
| **Trigger** | Opening sealed ossuary drawer without bypass |
| **Effect** | +5 to hit, 1d6 piercing + poison (DC 12 STA or **Poisoned** 1 hour) |
| **Reset** | One-shot; mechanism jams after fire |

*Site:* `32-C-UG-1` marshal tomb ([data/sites/breley-undercrypt.json](../../data/sites/breley-undercrypt.json))

### Fen snare and sink (marsh — Shadowfen)

| | |
|--|--|
| **Complexity** | 2 |
| **Detect DC** | 12 |
| **Disarm DC** | 12 |
| **Trigger** | Step in mud hex with concealed loop |
| **Effect** | Target **Restrained**; DC 13 STR to escape; at start of each turn, 1d6 bludgeoning (sinking) |
| **Reset** | Automatic when victim escapes or drowns |

*Site:* `47-B-UG-1` flooded halls

### Vault pressure plate (Iron Pact vault)

| | |
|--|--|
| **Complexity** | 5 |
| **Detect DC** | 15 |
| **Disarm DC** | 16 |
| **Trigger** | Weight on central plate (≥ 20 lb) |
| **Effect** | Ceiling spears: +6 to hit, 2d6 piercing, Dex save DC 14 for half; **+1 Delve clock** on trigger |
| **Reset** | 1 minute; plate re-arms |

*Site:* `32-C-UG-2` lower vaults

---

## Linking traps to sites

Site graph nodes may tag `"hazard"` edges or room traps. AV-GRID `links` and location docs reference trap DCs by name. Engine IDs: use slug keys matching trap names above (`ash-needle-lock`, etc.) in future `data/traps/` export.

**See also:** [combat/hazards.md](hazards.md) (poison), [encounter.md](encounter.md) (action economy)
