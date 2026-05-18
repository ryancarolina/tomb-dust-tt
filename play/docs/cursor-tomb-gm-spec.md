# Cursor AI GM — architecture summary

> **Normative full spec:** [tomb-gm-implementation-spec.md](tomb-gm-implementation-spec.md) — CLI, database, beat loop, memory, combat, and acceptance criteria.

Tomb Dust tabletop play runs in **Cursor** via agents + a deterministic CLI.

| Tree | Purpose |
|------|---------|
| [`build/`](../build/) | **Build** — canon: `data/`, `systems/`, validators |
| [`play/`](../) | **Play** — `workspace/` saves, `tomb_gm/` engine, this doc |

Agents must treat **`play/workspace/`** as the session workspace and **`build/`** as read-only canon during play.

## Play layout

See [play/README.md](../README.md) and [workspace/README.md](../workspace/README.md).

- Config: `play/workspace/config.yaml` (`content_root: ../../build`)
- Database: `play/workspace/.local/memory.db`
- Active session: `play/workspace/.local/active.json`
- Engine: `play/tomb_gm/`

## Player vs agent (required UX)

| Players | GM agent |
|---------|----------|
| In-character and OOC lines in chat only | **All** CLI: init, campaigns, characters, sessions, travel, rolls, memory, speak |
| `[P1] …` … `[P4]`, `[PARTY]`, `[OOC]` | Runs `python -m tomb_gm --workspace play/workspace …` via shell |
| Never run terminal or edit saves | Never invent mechanics; `check` must pass before narrating forward |

## Entry point: invoke the skill

**To play, the host only types `@tomb-gm`.**

On invoke the agent must: `status` / `check` / `suggest` → auto-setup workspace → resume or branch new campaign.

Skill: [.cursor/skills/tomb-gm/SKILL.md](../../.cursor/skills/tomb-gm/SKILL.md)

## Full product scope

- **Open world:** full AV-GRID, hubs, wilderness, NPCs — not delves-only
- **Delves & extraction:** one mode of play among many
- Up to 4 characters; full d20 combat; persistent SQLite memory
- **GM tools (CLI):** dice, rules, lore, monsters — agents never own state
- Canon from `build/data/*` per [engine-integration.md](../../build/docs/engine-integration.md)

**Build plan:** [tomb-gm-build-roadmap.md](tomb-gm-build-roadmap.md)

## Active session

| File | Effect |
|------|--------|
| `play/workspace/.local/active.json` | Table play active; GM runs `status` / `check` / `suggest` each turn |

## Implementation status

| Component | Status |
|-----------|--------|
| `build/` + `play/` layout | **Done** |
| `play/tomb_gm` CLI | Not started |
| `.cursor/skills/tomb-gm/` | Skill draft |
