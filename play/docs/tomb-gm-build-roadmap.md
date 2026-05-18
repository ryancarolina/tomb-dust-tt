# Tomb Dust AI GM — section-by-section build roadmap

> **Full implementation detail:** [tomb-gm-implementation-spec.md](tomb-gm-implementation-spec.md)

**How we build:** one section at a time → you test in Cursor → sign off → next section.  
**No throwaway POC:** each section ships production-quality code for that slice.

**Your target experience (definition of “done” for the whole project):**

- Create a **new character** with full canon rules.
- **Explore all of Aventhar** — travel the AV-GRID, visit hubs and wilds, talk to NPCs, pursue hooks — not only dungeon delves.
- **Delves & extraction** are one part of play, not the only loop.
- **Stop and resume:** GM memory + DB state restore phase, place, relationships, open threads.
- **GM tools** handle dice, rules, lore, monsters, gear, locations — agents narrate; **CLI owns state**.
- Up to **4 players**; state is always tracked for a seamless table experience.

## Who does what (player vs agent)

| Actor | Does | Does not |
|-------|------|----------|
| **Players (1–4)** | Talk in character in Cursor chat (`[P1] …`, `[P2] …`, `[PARTY] …`, `[OOC] …`) | Run terminal, edit `play/workspace/`, call CLI, manage files |
| **GM agent (`@tomb-gm`)** | All setup and mechanics: `init`, campaigns, character creation wizard, `session start`/`end`/`resume`, travel, rolls, memory, speak | Invent stats, addresses, or HP; skip CLI when state changes |
| **You (table host)** | **`@tomb-gm`** once to start or continue — agent handles setup, resume, and state | Type PowerShell, copy config files, or manage `play/workspace/` by hand |

**CLI exists for the agent** (and for developers debugging). It is not the player interface.

### Single entry: invoke the skill

**To play:** `@tomb-gm` (optionally: “continue”, “new campaign …”, “start”).

The agent must:

1. Run `status` / `check` / `suggest`
2. Auto-setup workspace (`config`, `init`) if needed
3. Resume an active session, or ask once then `session start` / `campaign new`
4. Own all state from that point until `session end`

No separate “run init first” step for the host.

**Player says → agent does → agent reports:**

- “Start a new campaign called Salt Road” → agent runs `campaign new`, confirms in fiction  
- “I want to make a militia character named Kira” → agent runs `character create` (or equivalent tool flow), asks missing choices in chat  
- “We pick up where we left off” → agent runs `session resume`, `memory recap`, then narrates  
- “I walk east toward the marches” → agent runs `world travel`, describes result  

**Where things live:**

| Path | Role |
|------|------|
| `build/data/`, `build/systems/` | Build canon (read-only during play) |
| `play/tomb_gm/` | Engine + CLI (we build here) |
| `play/workspace/` | Saves, SQLite, `active.json`, campaign logs |
| `.cursor/skills/tomb-gm/` | GM Orchestrator playbook |

---

## How you test (every section)

**Product test (preferred once Section 10 exists):** only use **`@tomb-gm`** in chat — ask the agent to perform the section’s capabilities in plain language; confirm behavior and DB updates. Do not run CLI yourself unless debugging.

**Engineering test (Section 1–9, or when debugging):** you or CI may run CLI commands directly to verify JSON output before the agent wrapper exists.

1. First-time host: ask agent to **set up the gameplay workspace** (agent copies config + `init`) — or do that once manually for development only.
2. In chat: **`@tomb-gm`** + natural requests that exercise the section (see each section’s **Agent test** line).
3. Optionally verify `play/workspace/.local/memory.db` / logs if something looks wrong.
4. Reply **“section N passed”** or report bugs before we start N+1.

---

## Section 1 — Foundation & CLI shell

**Delivers:** `tomb_gm` package, migrations, `init`, `status`, `check`, config loader, content pin.

| CLI (planned) | Purpose |
|---------------|---------|
| `python -m tomb_gm --workspace play/workspace init` | Create DB, dirs, default config |
| `python -m tomb_gm --workspace play/workspace status` | JSON: no active session / workspace health |
| `python -m tomb_gm --workspace play/workspace check` | Validators: config, content_root, DB schema |

**Agent test (after Section 10):** “Set up Tomb Dust for play” → agent runs init/check and reports ready.

**Engineering test (Section 1):** `init` → `status` shows `ok: true`; `check` passes; second `init` is idempotent.

**Not in this section:** characters, travel, GM narration.

---

## Section 2 — Campaign & session lifecycle

**Delivers:** create/list/resume/end campaign; start/end play session; `play/workspace/.local/active.json`.

| CLI | Purpose |
|-----|---------|
| `campaign new --slug <id> --name "..."` | New campaign row + folder under `play/workspace/campaigns/` |
| `campaign list` | All campaigns |
| `session start --campaign <slug>` | Active session, phase `preparation`, default hub `32-C` |
| `session end` | Close session, write session log |
| `session resume` | Restore last session for campaign |

**You test:** start session → `active.json` exists → end → resume restores same campaign id and phase.

---

## Section 3 — World map & travel (open Aventhar)

**Delivers:** load full `av-grid.json` + index; party position; legal moves; travel time fiction hooks; layer transitions (`UG`, `EP`, etc.).

| CLI | Purpose |
|-----|---------|
| `world where` | Current address, displayName, summary, biomes, danger |
| `world exits` | Neighbor cells / child layers you can enter |
| `world travel --to <AV-GRID id>` | Validate + update party address |
| `world describe` | Pull location doc link from cell `links.location` |

**You test:** start at `32-C` → travel east along corridor → reach `46-C` → descend to `32-C-UG-1` when stamped rules allow. Invalid ids rejected.

**Scope note:** This is **surface + layer exploration**, not site-graph room crawl (Section 13).

---

## Section 4 — Character creation

**Delivers:** interactive CLI wizard matching `systems/character/creation-steps.md` (stats, class filter, 3 skills, starting kit); sheet stored in DB per `data/schemas/character.schema.json`.

| CLI | Purpose |
|-----|---------|
| `character create` | Wizard (prompts or flags) |
| `character show --id <id>` | JSON sheet |
| `character list --campaign <slug>` | All PCs in campaign |

**You test:** create one PC with Militia + longsword; HP/MP match derived-stats formulas; sheet survives `session end` / `resume`.

---

## Section 5 — Player roster (1–4 slots)

**Delivers:** bind Discord-less **slots 1–4** to characters; party view; active speaker.

| CLI | Purpose |
|-----|---------|
| `roster set --slot 1 --character <id>` | Bind |
| `roster show` | Party summary |
| `roster clear --slot 2` | Unbind |

**You test:** bind two characters; `roster show` lists both; session resume keeps bindings.

---

## Section 6 — Dice & checks (deterministic)

**Delivers:** all combat math via `tools/rules_engine` (extended as needed); transparent roll log to `events` table.

| CLI | Purpose |
|-----|---------|
| `roll d20 --mod +5 --dc 13 --reason "..."` | Skill check / save |
| `roll attack --attacker <id> --target <monster/instance>` | Full attack pipeline |
| `roll initiative --combat <id>` | Initiative order |

**You test:** attack vs ghoul AC; log shows natural, total, hit, crit, damage; same roll repeated via seed for audit.

---

## Section 7 — Content tools (monsters, gear, spells, NPCs)

**Delivers:** read-only lookups from `data/`; markdown doc paths; **block** if monster JSON missing.

| CLI | Purpose |
|-----|---------|
| `content monster <slug> [--tier skirmisher]` | Stat block |
| `content weapon <slug>` | Weapon row |
| `content spell <slug>` | Spell row |
| `content npc <slug>` | Services + hooks from `systems/npcs/` |
| `content cell <AV-GRID>` | Grid + linked docs |

**You test:** `content monster grave-ghoul` returns AC/HP; unknown slug errors; hollow-knight warns if no JSON yet.

---

## Section 8 — Rules & lore search

**Delivers:** RAG index over `systems/` (and optional `systems/lore/`); ranked excerpts for GM tools.

| CLI | Purpose |
|-----|---------|
| `rules search "Magical Defense"` | Top excerpts + paths |
| `rules search "threat clock" --max 5` | |

**You test:** query returns `systems/combat/calculations.md` / `extraction.md` chunks; no edits to canon files.

---

## Section 9 — Memory (resume seamlessly)

**Delivers:** episodic `events`, semantic `memories`, scene summaries, `recall`, end-of-session compaction.

| CLI | Purpose |
|-----|---------|
| `memory remember --fact "..." --entities kira,32-C` | Pin fact |
| `memory recall --query "marshal key"` | Ranked facts for prompts |
| `memory recap` | Last session + open threads |
| `memory compact` | Summarize session (usually on `session end`) |

**You test:** play a few beats → `remember` a custom fact → `session end` → new Cursor chat → `resume` + `recap` includes the fact.

---

## Section 10 — Cursor integration (orchestrator)

**Delivers:** `.cursor/skills/tomb-gm/` (invoke = start), `tomb-gm-active` rule, hooks (prompt injection, shell allowlist), player line parser, **invoke branching** (setup / resume / new).

| Player format | `[P1 Name] action` … `[P4]`, `[PARTY]`, `[OOC]`, `[GM] pause` |
| Invoke | `@tomb-gm` alone must run status → setup or resume → play |
| Agent turn | `status` → `check` → `suggest` → narrate (no state writes without CLI) |

**Agent test:** Fresh folder → only `@tomb-gm` → agent inits workspace, asks campaign name, no host terminal.

**Agent test:** Active session → `@tomb-gm` → recap + correct address, no “start a new campaign” unless session ended.

---

## Section 11 — Exploration beat loop (open world play)

**Delivers:** `beat` command: ingest player actions, update world/social state, append events, return structured `{ narration_brief, tools_run, prompts }` for the agent to speak.

**Covers:** hubs, wilderness encounters (`data/encounters/wilderness.json`), reading location fiction, downtime scenes — **without requiring a delve**.

| CLI | Purpose |
|-----|---------|
| `beat --actions '<json>'` | One table beat |
| `suggest` | What the table should do next (OOC hint) |

**You test:** spend 30 minutes wandering `32-C` → `33-C`, trigger travel encounter roll, talk to an NPC via fiction + `content npc`, stop, resume with recap.

---

## Section 12 — Social, factions & services

**Delivers:** Registry stamps, shops, hirelings, faction rep (from docs + JSON); gold and inventory on character rows.

| CLI | Purpose |
|-----|---------|
| `economy buy --item ...` | Deduct gold, add inventory |
| `registry stamp --address ...` | Legal claim for delves |
| `faction rep --faction ...` | Read/update rep |

**You test:** buy rations in hub; stamp undercrypt; rep stored in campaign state.

---

## Section 13 — Delves & site graphs

**Delivers:** `data/sites/*.json` navigation, edges, locks, site encounters; threat clock; extract phases integrated with Section 3 world position.

| CLI | Purpose |
|-----|---------|
| `site enter --id breley-undercrypt` | Enter graph at entry node |
| `site move --to <nodeId>` | Follow edge |
| `clock tick --reason "loud fight"` | Threat clock |

**You test:** full Breley undercrypt run linked from Section 3 travel to `32-C-UG-1`.

---

## Section 14 — Combat

**Delivers:** initiative, turns, 4-player spotlight, conditions, dying, Fortune, spells from JSON.

| CLI | Purpose |
|-----|---------|
| `combat start --encounter ...` | Spawn monsters |
| `combat turn` | Advance turn |
| `combat end` | XP/loot hooks |

**You test:** skirmish with 2 players; conditions apply; TPK and death rules per persistence doc.

---

## Section 15 — Account persistence & deeds

**Delivers:** stash vs body gear, death → new character inherits account, `data/deeds/promotions.json` eligibility.

| CLI | Purpose |
|-----|---------|
| `account stash` | View deposit box |
| `character retire / inherit` | Death flow |
| `deeds check` | Promotion eligibility |

**You test:** die on delve → new PC keeps stash gold, not body inventory.

---

## Section 16 — Voice (edgeTTS)

**Delivers:** `speak` command, queue, cache, stop; agent runs after each beat.

| CLI | Purpose |
|-----|---------|
| `speak --beat-id <id>` | Narration audio |
| `speak --stop` | Clear queue |

**You test:** hear GM open scene; stop mid-line; resume without re-fetching cached lines.

---

## Dependency graph (build order)

```text
1 Foundation
  → 2 Campaign/session
    → 3 World/travel
      → 4 Character create
        → 5 Roster
          → 6 Dice
            → 7 Content tools
              → 8 Rules search
                → 9 Memory
                  → 10 Cursor skill
                    → 11 Exploration beats
                      → 12 Social/economy
                        → 13 Delves/sites
                          → 14 Combat
                            → 15 Persistence/deeds
                              → 16 Voice
```

Sections 12–14 can overlap slightly once 11 exists; order above minimizes rework.

---

## What you cannot do yet (today)

| Action | Status |
|--------|--------|
| “Start the game” | **Not built** — begin with **Section 1** |
| `@tomb-gm` | After Section 10 |
| Hear GM voice | After Section 16 |
| Full world | After Section 3 + 11 |

---

## When the full roadmap is complete (player experience)

**One action to play:** `@tomb-gm`

| You say | Agent handles |
|---------|----------------|
| `@tomb-gm` | setup if needed → resume active session **or** prompt new/continue campaign |
| `@tomb-gm New campaign Salt Road, four players` | `campaign new`, character creation in chat, `session start`, open scene |
| `@tomb-gm` (days later) | `session resume`, `memory recap`, continue |
| `@tomb-gm We're done` | `session end`, memory compact, goodbye recap |
| `[P1 Kira] …` | `beat` / travel / combat tools — players never touch CLI |

Optional couch co-op: host reads player speech into `[P1]`…`[P4]` lines. Still no terminal for anyone.

---

## Next step

Say **“start Section 1”** and we implement Foundation & CLI shell only; you test before any character or world code lands.
