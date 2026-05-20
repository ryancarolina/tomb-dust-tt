---
name: tomb-gm
description: >-
  LEGACY — developer reference for the tomb_gm CLI and old Cursor chat GM.
  Do NOT suggest this skill or @tomb-gm for playing Tomb Dust. Players use
  app/main.py (see app/README.md).
---

# Tomb Dust GM skill (legacy — not for play)

> **Do not use this skill to play the game.**  
> **Canonical play:** [app/README.md](../../../app/README.md) — `cd app && python main.py` → type **`new game`**.  
> Do **not** tell users to invoke `@tomb-gm`, use Cursor chat as the table, or run `python -m tomb_gm` to play.

This file remains for **engine developers** debugging `play/tomb_gm/` or maintaining historical Cursor integration. Player-facing docs must point at the **PyGame app** only.

**App specs:** [tmp/app-master-spec.md](../../../tmp/app-master-spec.md) · [tmp/app-gamebridge-spec.md](../../../tmp/app-gamebridge-spec.md)  
**Canon ↔ engine:** [build/docs/engine-integration.md](../../../build/docs/engine-integration.md)

---

## Repository layout

| Path | Role |
|------|------|
| **`app/`** | **Player client** — PyGame UI, LLM orchestrator, TTS |
| **`build/`** | Canon — `data/`, `systems/`, `tools/` (read-only during play) |
| **`play/workspace/`** | Saves, SQLite, campaigns (used by the app) |
| **`play/tomb_gm/`** | Engine — CLI for tests/debug; `GameBridge` for the app |

---

## CLI reference (developers / tests only)

From **repository root**, workspace **`play/workspace`**:

```powershell
python -m tomb_gm --workspace play/workspace status
python -m tomb_gm --workspace play/workspace check
python -m tomb_gm --workspace play/workspace suggest
```

Use these when writing pytest, debugging saves, or verifying JSON — **not** as player instructions.

---

## Mechanics CLI (developer runs these)

| Area | Commands |
|------|----------|
| Rolls | `roll d20`, `roll save`, `roll initiative`, `roll attributes`, `roll genetics`, `roll life-event` |
| Combat | `combat start`, `combat attack`, `combat cast`, `combat turn`, `combat damage`, `combat stabilize`, `combat end` |
| Site | `site enter`, `site move`, `site search` |
| World | `world travel`, `world describe`, `world search` |
| Lore | `lore search`, `lore index` |
| Economy | `economy buy/sell/stash/death` |
| Inventory | `inventory list/equip/unequip/use` |
| GM tools | `equip_item`, `unequip_item`, `grant_loot`, `buy_item`, `sell_item`, `list_stash`, `list_vendor`, `list_inventory` |
| Beat | `beat --actions '<json>'` |
| Voice | `narrate push`, `speak --last`, `speak --stop` |

**Economy rules (canon):**
- **Account stash + stashGp persist** on PC death; body pack and goldGp become corpse loot.
- Hub gates: stash/vendor/fence only when `party_state.mode === "surface"` and cell has matching `services.*`.
- Mechanical loot must use `grant_loot` — never narrate items without a tool commit.

---

## Related

- [play/README.md](../../../play/README.md)
- Content agents: [AGENTS.md](../../../AGENTS.md) + `build/`
