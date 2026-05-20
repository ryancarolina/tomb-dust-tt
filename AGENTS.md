# Tomb Dust — project rules for agents

Read this before changing game content, world data, or rules docs. **If anything conflicts, follow the priority order below.**

## What this repository is

- **Tomb Dust**: hardcore **extraction fantasy** TTRPG (frequent death, delver economy, deed-based class tiers).
- **Build** (canon): [`build/`](build/README.md) — `data/`, `systems/`, `tools/`
- **Play** (runtime): [`play/`](play/README.md) — saves, AI GM sessions — **not canon**
- **`build/assets/tomb-dust-source-archive.md`**: historical export only — **do not treat as canon**

---

## Source-of-truth priority

| Priority | Location | Holds |
|----------|----------|--------|
| **1** | `build/data/av-grid/av-grid.json` | All **AV-GRID** addresses, layers, biomes, regions, danger, Registry flags, links to docs |
| **2** | `build/systems/core/` + `build/systems/combat/calculations.md` | **d20** resolution, attributes, AC, PB, crits, Fortune |
| **3** | Other `build/systems/**` | Skills, monsters, locations, factions, NPCs (must **match** 1–2) |
| **4** | `build/assets/tomb-dust-source-archive.md` | Reference only |

**When markdown disagrees with JSON → JSON wins.** Update markdown after changing JSON.

---

## App development specs (mandatory for `app/`)

**Specs are the source of truth for app development and testing. Drift between spec and code is NEVER allowed.**

| Priority | Location | Holds |
|----------|----------|--------|
| **A1** | [`tmp/app-master-spec.md`](tmp/app-master-spec.md) | Registry of all app domain specs, drift policy, agent workflow |
| **A2** | `tmp/app-*-spec.md` (domain specs) | Behavior, task checklist, tests, changelog for each app area |
| **A3** | `app/**` code | Must match the domain spec — update spec in the same change |

### Rules

1. **Every change under `app/`** must update the **respective domain spec** (see registry in app master spec) before or alongside code.
2. **Specs define tests** — acceptance criteria and pytest/smoke commands live in the spec; passing them is done.
3. **Changelog required** — mark checklist items and append a dated changelog entry when work lands.
4. **No orphan behavior** — if it is not in a spec, add it to a spec first.
5. **No stale specs** — spec and code update together; never leave drift.

### Domain spec index (quick)

| Spec file | Owns |
|-----------|------|
| `tmp/app-shell-config-spec.md` | `main.py`, config, deps |
| `tmp/app-session-persistence-spec.md` | Saves, resume, `new game` |
| `tmp/app-pygame-ui-spec.md` | `ui/**` |
| `tmp/app-gamebridge-spec.md` | `gm/bridge.py` |
| `tmp/app-character-creation-spec.md` | Creation state machine |
| `tmp/app-llm-orchestrator-spec.md` | Turn loop, tools, prompt |
| `tmp/app-exploration-delve-spec.md` | Travel, sites, delves |
| `tmp/app-combat-play-spec.md` | Combat FSM |
| `tmp/app-economy-inventory-play-spec.md` | Pack, stash, vendors (app) |
| `tmp/app-tts-narration-spec.md` | Voice + narration panel |
| `tmp/app-logging-qa-spec.md` | JSONL logs, `app/tests/` |

**Only `tmp/app-*-spec.md` files are development specs.** Canon mechanics: `build/systems/` + `build/docs/engine-integration.md`.

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

1. Edit **`build/data/av-grid/av-grid.json`** (`parent`, `childAddresses`, `biomes`, `region`, `links`, etc.).
2. Run `python build/tools/av_grid.py validate`
3. Run `python build/tools/av_grid.py build-index`
4. Update human docs (`build/systems/locations/*.md`, etc.) to match — include **AV-GRID** on the location page.

**Never** invent canon coordinates only in markdown. **Never** add parallel grid docs (e.g. `option-d-*.md`) — use `build/systems/world/grid.md` + JSON.

**Registry stamps** (e.g. `REG-1204 rev.C`) are legal paperwork; **AV-GRID** is the real location.

Details: `build/data/av-grid/README.md`, `build/systems/world/grid.md`

---

## Game mechanics (canon d20 system)

All uncertain outcomes use **one d20 test**: roll d20 + modifiers vs DC or AC.

| Topic | Rule | Doc |
|-------|------|-----|
| Attributes | Modifier = `floor((score − 10) / 2)` | `build/systems/core/attributes.md` |
| **LUC** | **Fortune only** (session pool; not a 7th combat modifier) | `build/systems/core/resolution.md` |
| Class bonus | **PB** by deed tier, cap **+4** | `build/systems/combat/calculations.md` |
| Skills | Skill bonus cap **+4** at level 10; techniques at 3/6/9 | `build/systems/skills/skill-checks.md` |
| Crits | **Gritty**: crit if hit and (nat 20 or beat AC by 5+) | `build/systems/core/resolution.md` |
| AC | Armor category caps AGI; **flat-footed** drops AGI + Dodge | `build/systems/equipment/armor.md` |
| Attacks | `d20 + mod + PB + skill bonus` vs **AC** | `build/systems/combat/calculations.md` |

**Skill bonus (canon):** only the tier table in `combat/calculations.md` (+0 at skill 1–2 up to +4 at 9–10). Skill **level** (1–10) scales techniques and passive effects, not d20 roll bonuses.

**Obsolete — do not reintroduce:** d100 evasion/hit tables, `1d12` attack vs “physical defense”, `2d6` as the default skill check, undefined “map IDs” that are not AV-GRID.

Progression: **deed-based class tiers** + skill XP — not character levels 1–20.

Tone: `build/systems/world/extraction.md`, `build/systems/character/creation.md`

---

## Content conventions

### Monsters

- Use d20 stat blocks: **+hit** vs AC, explicit **danger** tier (hazard / skirmisher / elite / boss).
- Template: `build/systems/monsters/README.md`
- Set habitat via AV-GRID `links` / region in JSON when adding sites.

### Locations

- Must have **AV-GRID** in `av-grid.json` and on the location markdown (`## World ties` or header).
- Encounters reference monster paths under `build/systems/monsters/`.

### NPCs

- d20 stats if combat-relevant; social/delve services tied to grid where applicable.
- Index: `build/systems/npcs/README.md`

### Factions & events

- Align with `build/systems/world/history.md` and regions in JSON.
- Do not duplicate Eclipse Festival text for other events.

### Editing style

- Match existing `build/systems/` voice and structure.
- **Do not** drive-by refactor unrelated files.
- **Do not** create markdown the user did not ask for unless it is required to sync canon (e.g. after JSON grid change).
- Preserve `TODO` stubs unless the task is to fill them.
- **Do not** edit `play/workspace/` when authoring canon (except playtesting).

---

## Repository layout (quick)

```
build/                 ← BUILD: data/, systems/, tools/, docs/
app/                   ← PLAY: PyGame client (canonical player entry)
play/                  ← Engine + workspace saves (used by app)
  workspace/           ← SQLite, campaigns, active session
AGENTS.md              ← this file
```

**Build vs play:** edit canon under `build/`; **play via `app/main.py`** ([app/README.md](../app/README.md)). The `play/tomb_gm` CLI is for engine development and tests only — not for running a session at the table.

Entry: `build/systems/README.md` · Setting: `build/systems/world/README.md`

---

## Commands agents should run

```bash
# After any av-grid.json change
python build/tools/av_grid.py validate
python build/tools/av_grid.py build-index

# Content + reference engine
python build/tools/validate_content.py
python -m pytest build/tools/rules_engine
```

**Game integration contract:** [build/docs/engine-integration.md](build/docs/engine-integration.md)

**Play the game:** [app/README.md](../app/README.md) (`python main.py`).  
**App development specs:** [tmp/app-master-spec.md](../tmp/app-master-spec.md) — **mandatory for all `app/` changes** (only spec location)  
**Engine integration:** [build/docs/engine-integration.md](build/docs/engine-integration.md) — canon ↔ `play/tomb_gm/`

---

## Checklist before finishing an app task

- [ ] Correct domain spec identified in [`tmp/app-master-spec.md`](../tmp/app-master-spec.md)
- [ ] Spec updated: behavior, tasks, tests, changelog — **no drift from code**
- [ ] Tests listed in the spec pass
- [ ] Cross-domain changes reflected in each affected spec

---

## Checklist before finishing a content task

- [ ] New/changed places exist in **`av-grid.json`** and validate clean
- [ ] `index.json` rebuilt if grid changed
- [ ] Location/monster/NPC markdown updated and links consistent
- [ ] No obsolete mechanics (d12/d100/2d6 standard) introduced
- [ ] No duplicate “alternate rules” files; one d20 system only
- [ ] AV-GRID ids in prose match JSON exactly (e.g. `47-B-UG-3`, not vague “map 47-B” unless meaning surface cell)
