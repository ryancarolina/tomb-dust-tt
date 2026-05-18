# Game readiness checklist (TD-092)

**Purpose:** Gate for starting **game architecture / engine UI** work. Content and reference rules in this repo should pass this checklist before the playable codebase depends on them.

**Reviewed:** 2026-05-18 (Wave 6)  
**Rules bundle:** `rulesVersion` **1.1.0** (see [RULESCHANGELOG.md](../RULESCHANGELOG.md))

---

## P0 — Rules canon (Epic E1)

| Story | Gate |
|-------|------|
| TD-001 – TD-006 | Skill bonus tier table canon; obsolete mechanics purged; Magical Defense; Fortune default |

- [x] `systems/combat/calculations.md` declared in AGENTS.md / core README
- [x] No d100 / 1d12 attack / physical defense in `systems/skills/`

---

## P0 — Combat loop (Epic E2)

| Story | Gate |
|-------|------|
| TD-010 – TD-016 | Initiative, surprise, actions, conditions, dying, walkthrough |

- [x] `systems/combat/encounter.md`, `conditions.md`, `walkthrough-example.md`
- [x] `tools/rules_engine/` tests green (`python -m pytest tools/rules_engine`)

---

## P0 — Equipment (Epic E3 partial)

| Story | Gate |
|-------|------|
| TD-020 – TD-021 | Weapons, Base HP/MP |

- [x] `systems/equipment/weapons.md` + `data/weapons/weapons.json` (17)
- [x] `systems/core/derived-stats.md`

---

## P0 — Magic (Epic E4)

| Story | Gate |
|-------|------|
| TD-030 – TD-033 | Schools, starter spells, casting rules |

- [x] `systems/magic/` + `data/spells/spells.json` (30 spells after Wave 6)
- [x] Divine vs arcane documented (TD-034)

---

## P0 — Creation & progression (Epic E5 partial)

| Story | Gate |
|-------|------|
| TD-040 – TD-043 | Creation steps, deeds JSON |

- [x] `systems/character/creation-steps.md`
- [x] `data/deeds/promotions.json` + `systems/classes/deeds.md`

---

## P0 — Extraction (Epic E6)

| Story | Gate |
|-------|------|
| TD-050 – TD-054 | Run loop, death, clock, claims, stash |

- [x] `systems/world/extraction.md`, `systems/meta/death-and-persistence.md`

---

## P0 — Data layer (Epic E9)

| Story | Gate |
|-------|------|
| TD-080 – TD-085 | Schemas, JSON content, reference engine |

- [x] `data/schemas/`, validators pass
- [x] `python tools/validate_content.py` OK
- [x] `docs/engine-integration.md` (TD-090)

---

## P1 — Vertical slice world (Epic E7)

| Story | Gate |
|-------|------|
| TD-060 – TD-063 | MVP corridor, site graph, loot |

- [x] AV-GRID corridor 33-C → 46-C + Breley + Shadowfen
- [x] `data/sites/breley-undercrypt.json`
- [x] `data/loot/tables.json`

---

## P1 — Content (Epic E8 partial)

| Story | Gate |
|-------|------|
| TD-070 – TD-073 | Traps, hazards, humanoids |

- [x] `systems/combat/traps.md`, `hazards.md`, `systems/monsters/humanoids.md`

---

## Wave 6 additions

| Story | Gate |
|-------|------|
| TD-032 | Tier 4–5 spells (12) + wild magic table |
| TD-034 | Divine casting in deities + magic docs |
| TD-035 | Magic items section in gear.md |
| TD-064 | `data/encounters/wilderness.json` + procedure |
| TD-065 | `data/av-grid/ledger-examples.json` (4 entries) |
| TD-074 | NPC services template + 5 NPCs updated |
| TD-091 | RULESCHANGELOG 1.1.0 |

---

## Validation commands (must pass)

```powershell
python tools/validate_content.py
python tools/av_grid.py validate
python -m pytest tools/rules_engine
```

---

## Sign-off

| Milestone | Status |
|-----------|--------|
| **M7 — Game architecture green light** | **READY** |

Remaining P1/P2 (not blocking engine start): TD-045+, TD-075+, expanded deed paths, full monster JSON coverage, CI wiring, codegen spike (TD-086).

**Next step:** Pin this repo commit in the game project's content manifest per [docs/engine-integration.md](../docs/engine-integration.md).
