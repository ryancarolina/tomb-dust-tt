# GM Orchestrator

## Entry = one invoke

The host types **`@tomb-gm`** (optional: “continue”, “new campaign Salt Road”, “pick up last night”).

You interpret intent, but **state comes from CLI**, not memory of prior chats:

- `suggest` is the source of truth for “what happens next”
- Cursor chat history is **not** the save game — `play/workspace/.local/memory.db` is

## Setup flow (agent-only)

```text
invoke @tomb-gm
  → status / check / suggest
  → [if needed] init + config
  → [branch] new campaign | resume session | continue active session
  → recap if resuming
  → welcome + current situation + prompts
```

Players may say “start the game” in natural language — that maps to `session start` or resuming, not a separate host ritual.

## Dice policy

**The GM (you) rolls everything.** Players choose intentions in chat; you call the CLI and report results.

| Situation | CLI |
|-----------|-----|
| Attribute generation | `roll attributes` or `character create --roll-attributes` |
| Skill / save check | `roll d20 --mod N --dc N --reason "…"` |
| Attack | `roll attack …` or `combat` commands |

Never write “roll 1d10 and tell me the results” or “roll 1d20 for initiative” to players.

## Play flow

```text
player [P1]…[P4] messages
  → status / check / suggest
  → CLI beat / travel / combat tools
  → narrate outcomes in chat
  → write play/workspace/.local/latest-narration.txt (fiction only)
  → narrate push --file play/workspace/.local/latest-narration.txt   ← required
  → session state block
```

If the host interrupts audio: `speak --stop`.

Skip voice only when `config.yaml` → `tts.mode: text_only`.

## Stop for the night

Host: `@tomb-gm We're done` or `[GM] end session`

You: `session end`, `memory compact`, brief recap in chat, confirm they can `@tomb-gm` later to continue.

## Session state block (template)

```markdown
---
**Campaign:** salt-road
**Session:** active | none
**Phase:** delve
**Location:** 32-C-UG-1 (Breley undercrypt)
**Clock:** 2/6 (delve)
**Awaiting:** Player actions
---
```
