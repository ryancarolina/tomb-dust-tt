# Death and persistence

Tomb Dust treats **character death** as expected, not exceptional. A delver who dies on a stamped map becomes **Tomb Dust**—ash scraped from the site, a name in a Registry ledger, and a **corpse** left where they fell until someone loots it or the site claims it.

**Death ends the run.** The player starts a **new game** with a fresh character. There is **no inheritance** of faction reputation, map knowledge, deeds, or stats from the dead delver.

**Exception — account stash:** `stash` pack and `stashGp` on the campaign account **persist**. A new delver may withdraw ancestor salvage at a hub with `services.stash` (e.g. Breley Keep `32-C`). Personal body gear and coin on the dead delver do not carry forward.

For in-combat **0 HP** rules (consciousness roll, stabilization), see [combat/encounter.md](../combat/encounter.md).

---

## What happens when you die

| Step | Effect |
|------|--------|
| **1. Death confirmed** | HP rules, monster behavior, or GM fatality declare the PC **dead** (not merely Downed or Dying). |
| **2. Corpse placed** | Body and **all carried gear** become a **static world feature** at the death location (**AV-GRID** + room or surface cell). |
| **3. Run ends** | Session ends; the table starts a **new game** with character creation. |
| **4. Fresh start** | New PC: Tier 1 defaults, empty personal sheet, **no** body gear from predecessor. **Account stash** (pack + gold) remains available at hub. |

**On the map:** the corpse persists across later runs. A future delver can **find and loot** it like any other feature. Looting does not revive the dead character.

---

## What resets on death

Everything tied to the **character sheet** and **current run**:

| Category | Resets |
|----------|--------|
| **Character** | Name, attributes, class tier, deeds, skill XP, HP, MP, conditions, Fortune (**LUC**) |
| **Gear on body** | Worn armor, weapons, pack, coin on person, consumables |
| **Run state** | Unextracted salvage, temporary buffs, active stamp benefits for that delver |
| **Account progress** | Faction rep, map annotations, Registry standing — **none carry forward** |
| **Account stash** | **`stash` pack + `stashGp` persist** — new delver may use at hub |

Hub **stash** is inherited across delver deaths. Other account progress (rep, deeds, map knowledge) does not carry forward.

---

## Corpses in the world

When a PC dies, the engine records a **delver corpse** at the death site:

| Field | Meaning |
|-------|---------|
| **Location** | Surface **AV-GRID** (e.g. `32-C`) or dungeon site + room (e.g. `32-C-UG-1` / `ossuary-hall`) |
| **Display** | Delver name + brief cause (e.g. *Sammy — clawed by grave ghoul*) |
| **Loot** | Snapshot of body gear, pack, and coin at death |
| **State** | `pristine` → `looted` when searched |

**Recovery fiction:** a later character who reaches the same room may **examine** or **loot** the corpse. Success transfers items to the looter; it does **not** restore the dead PC or account progress.

Corpses may be destroyed by collapse, beasts, or site events at GM discretion.

---

## Tone link

Hardcore extraction means **risk is priced and death is final for that delver**. Players learn routes on their own each run, manage loadout vs. danger, and accept that the **body** is loot on the map—the **Registry entry** is a warning, not a save file.

**See also:** [world/extraction.md](../world/extraction.md) (run phases), [combat/encounter.md](../combat/encounter.md) (0 HP and death), [world/grid.md](../world/grid.md) (stamped addresses).
