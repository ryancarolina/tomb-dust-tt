# Tomb Dust — project rules for agents

Read this before changing game content, world data, or rules docs. **If anything conflicts, follow the priority order below.**

## What this repository is

- **Tomb Dust**: hardcore **extraction fantasy** TTRPG (frequent death, delver economy, deed-based class tiers).
- Primary content: **`systems/`** (rules + lore markdown), **`data/av-grid/`** (world grid source of truth), **`tools/`** (validators).
- **`assets/tomb-dust-source-archive.md`**: historical monolith export only — **do not treat as canon** and do not extend it.
- Playable game code may live outside this repo; design docs here are authoritative for setting and mechanics.

---

## Source-of-truth priority

| Priority | Location | Holds |
|----------|----------|--------|
| **1** | `data/av-grid/av-grid.json` | All **AV-GRID** addresses, layers, biomes, regions, danger, Registry flags, links to docs |
| **2** | `systems/core/` + `systems/combat/calculations.md` | **d20** resolution, attributes, AC, PB, crits, Fortune |
| **3** | Other `systems/**` | Skills, monsters, locations, factions, NPCs (must **match** 1–2) |
| **4** | `assets/tomb-dust-source-archive.md` | Reference only |

**When markdown disagrees with JSON → JSON wins.** Update markdown after changing JSON.

---

## AV-GRID (world coordinates)

Every place has an address: surface **`CC-R`** (e.g. `23-A`), then layers:

| Layer | Example | Meaning |
|-------|---------|---------|
| `UG-n` | `23-A-UG-1` | Underground level *n* (deeper = higher *n*) |
| `EP` | `24-B-EP` | Ether / thin-veil (same column-row) |
| `BV` | `47-B-BV` | Black Vale rift plane |
| `SK` | `18-H-SK` | Skyreach altitude layer |
| Stacked | `32-C-UG-2-EP` | Vault + veil bleed |

### Required workflow for new/changed places

1. Edit **`data/av-grid/av-grid.json`** (`parent`, `childAddresses`, `biomes`, `region`, `links`, etc.).
2. Run `python tools/av_grid.py validate`
3. Run `python tools/av_grid.py build-index`
4. Update human docs (`systems/locations/*.md`, etc.) to match — include **AV-GRID** on the location page.

**Never** invent canon coordinates only in markdown. **Never** add parallel grid docs (e.g. `option-d-*.md`) — use `systems/world/grid.md` + JSON.

**Registry stamps** (e.g. `REG-1204 rev.C`) are legal paperwork; **AV-GRID** is the real location.

Details: `data/av-grid/README.md`, `systems/world/grid.md`

---

## Game mechanics (canon d20 system)

All uncertain outcomes use **one d20 test**: roll d20 + modifiers vs DC or AC.

| Topic | Rule | Doc |
|-------|------|-----|
| Attributes | Modifier = `floor((score − 10) / 2)` | `systems/core/attributes.md` |
| **LUC** | **Fortune only** (session pool; not a 7th combat modifier) | `systems/core/resolution.md` |
| Class bonus | **PB** by deed tier, cap **+4** | `systems/combat/calculations.md` |
| Skills | Skill bonus cap **+4** at level 10; techniques at 3/6/9 | `systems/skills/skill-checks.md` |
| Crits | **Gritty**: crit if hit and (nat 20 or beat AC by 5+) | `systems/core/resolution.md` |
| AC | Armor category caps AGI; **flat-footed** drops AGI + Dodge | `systems/equipment/armor.md` |
| Attacks | `d20 + mod + PB + skill bonus` vs **AC** | `systems/combat/calculations.md` |

**Skill bonus (canon):** only the tier table in `combat/calculations.md` (+0 at skill 1–2 up to +4 at 9–10). Skill **level** (1–10) scales techniques and passive effects, not d20 roll bonuses.

**Obsolete — do not reintroduce:** d100 evasion/hit tables, `1d12` attack vs “physical defense”, `2d6` as the default skill check, undefined “map IDs” that are not AV-GRID.

Progression: **deed-based class tiers** + skill XP — not character levels 1–20.

Tone: `systems/world/extraction.md`, `systems/character/creation.md`

---

## Content conventions

### Monsters

- Use d20 stat blocks: **+hit** vs AC, explicit **danger** tier (hazard / skirmisher / elite / boss).
- Template: `systems/monsters/README.md`
- Set habitat via AV-GRID `links` / region in JSON when adding sites.

### Locations

- Must have **AV-GRID** in `av-grid.json` and on the location markdown (`## World ties` or header).
- Encounters reference monster paths under `systems/monsters/`.

### NPCs

- d20 stats if combat-relevant; social/delve services tied to grid where applicable.
- Index: `systems/npcs/README.md`

### Factions & events

- Align with `systems/world/history.md` and regions in JSON.
- Do not duplicate Eclipse Festival text for other events.

### Editing style

- Match existing `systems/` voice and structure.
- **Do not** drive-by refactor unrelated files.
- **Do not** create markdown the user did not ask for unless it is required to sync canon (e.g. after JSON grid change).
- Preserve `TODO` stubs unless the task is to fill them.

---

## Repository layout (quick)

```
data/av-grid/          ← SOURCE OF TRUTH for places
systems/
  core/                ← d20, attributes, resolution
  combat/              ← PB, damage, Dodge
  world/               ← setting (human); grid rules
  locations/ monsters/ npcs/ factions/ …
tools/av_grid.py       ← validate / parse / build-index
AGENTS.md              ← this file
```

Entry: `systems/README.md` · Setting: `systems/world/README.md`

---

## Commands agents should run

```bash
# After any av-grid.json change
python tools/av_grid.py validate
python tools/av_grid.py build-index

# Content + reference engine
python tools/validate_content.py
python -m pytest tools/rules_engine
```

**Game integration contract:** [docs/engine-integration.md](docs/engine-integration.md)

---

## Dev-team sessions (when active)

If `.dev-team/active.json` exists, also follow `.cursor/rules/dev-team-active.mdc` and `.cursor/skills/dev-team/SKILL.md` (orchestrator CLI, gates, artifacts under `.dev-team/works/` only).

When dev-team state is `DONE` or no active session, normal Tomb Dust rules above apply.

---

## Checklist before finishing a content task

- [ ] New/changed places exist in **`av-grid.json`** and validate clean
- [ ] `index.json` rebuilt if grid changed
- [ ] Location/monster/NPC markdown updated and links consistent
- [ ] No obsolete mechanics (d12/d100/2d6 standard) introduced
- [ ] No duplicate “alternate rules” files; one d20 system only
- [ ] AV-GRID ids in prose match JSON exactly (e.g. `47-B-UG-3`, not vague “map 47-B” unless meaning surface cell)
