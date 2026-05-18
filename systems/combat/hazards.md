# Hazards — poison and disease

Poison and disease extend [conditions.md](conditions.md). Saves use `d20 + ability mod + PB + skill bonus` ([core/resolution.md](../core/resolution.md)).

**Medicine** treats poison and disease; **Endurance** and **Iron Stomach** (Endurance 6+) grant advantage on STA saves vs poison and disease ([skills/physical-skills.md](../skills/physical-skills.md)). **Treat Disease** (Medicine 6+) grants advantage on treatment checks ([skills/mental-skills.md](../skills/mental-skills.md)).

---

## Poison

### Poisoned condition

While **Poisoned** ([conditions.md](conditions.md)): disadvantage on attack rolls and ability checks. Duration and extra effects come from the poison entry.

### Poison procedure

| Step | Rule |
|------|------|
| **Exposure** | Ingest, injury, contact, or inhaled — per poison |
| **Initial save** | Usually **STA** vs poison DC on exposure |
| **On fail** | Apply damage stage and/or **Poisoned** |
| **Ongoing** | Many poisons repeat save at end of each turn or every N minutes |
| **Cure** | Medicine vs poison DC (action); antidote auto-success if matched; **Treat Disease** grants advantage |

### Damage stages (typical)

| Stage | Effect |
|-------|--------|
| **Mild** | 1d4 poison damage; Poisoned 10 minutes |
| **Standard** | 1d6 poison damage per failed interval; Poisoned 1 hour |
| **Strong** | 2d6 poison damage per interval; Poisoned until cured; STA save each hour |

**Example — tomb needle (Ash needle lock):** DC 12 STA or Poisoned 1 hour; no repeating damage.

**Example — gloom matriarch venom:** DC 14 STA or 2d6 poison + Poisoned 24 hours; repeat STA save at end of each hour, success ends poison damage (condition may linger until Medicine DC 14).

---

## Disease

### Procedure

| Step | Rule |
|------|------|
| **Exposure** | Contact, bite, foul water, corpse dust — per disease |
| **Incubation** | 1–7 days hidden; GM notifies on first symptom |
| **Symptoms** | Usually **disadvantage** on one ability domain or −1 max HP per day until treated |
| **Progression** | Each long rest without treatment: STA save vs disease DC; fail → stage +1 |
| **Contagion** | Optional; document per disease (e.g. fen rot: contact with weeping sores) |
| **Treatment** | Medicine vs DC (1 hour); **Treat Disease** = advantage; magical healing may grant one free success |

### Disease stages (template)

| Stage | Effect |
|-------|--------|
| **1** | Disadvantage on Endurance and Medicine checks |
| **2** | −2 effective STA (not score); max HP −5 |
| **3** | Disadvantage on all ability checks; cannot benefit from short rest HP recovery |
| **4** | Death in 1d6 days unless cured (Medicine DC +3) |

### Example — fen rot (Shadowfen)

**Exposure:** wading untreated fen water (DC 12 STA or contract). **Incubation:** 3 days. **Progression:** STA save DC 13 each long rest. **Contagion:** none (environmental). **Cure:** Medicine DC 14, or consecrate + Medicine DC 12.

---

## Link to extraction

Poison and disease during a delve do not pause the **threat clock**. Collapse at 6/6 may expose survivors to environmental poison (fen gas) as a secondary consequence ([world/extraction.md](../world/extraction.md)).

**See also:** [traps.md](traps.md), [conditions.md](conditions.md)
