# Research Brief: APP-074-remove-dead-step-prompt

**Date:** 2026-05-20
**Question:** Is `get_step_prompt()` dead on the live creation path, and what must change to remove it without breaking code-first creation?

**backlog_ticket:** APP-074
**ticket_path:** tmp/backlog/app-074-remove-dead-get-step-prompt.md
**domain_spec:** tmp/app-character-creation-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) is the correct owner per [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** (`gm/creation.py`, creation path in orchestrator). No new domain spec is needed; close work is delete dead function + spec changelog stating prompts live only in `_auto_present_*` / `format_*_table`.

## Summary

`get_step_prompt(state)` in `app/gm/creation.py` (lines **742–833**) is **legacy LLM-step instruction text** from the pre–code-first creation path. It mandates `set_creation_choice` tool calls and, for RACE, builds an inline `| Race | Adjustments | Description |` table from `RACES`. **Zero callers** exist under `app/`, `play/`, or `app/tests/`; `orchestrator.py` does not import it (contrast: `get_combat_step_prompt` is imported and used in exploration LLM context).

Live creation uses `_creation_turn` → `_creation_turn_body` → `_handle_creation_response` / `_auto_present_*` with thin flavor via `_creation_flavor_messages` + code bodies from `format_*_table()`. `_creation_llm_loop` (orchestrator ~1161) is also uncalled but **out of ticket scope**.

Removal is low-risk: ~92 lines deleted from `creation.py`, domain spec § Presentation / file map updated on close. **Do not** edit `system_prompt.py` in this ticket (still documents tool-driven creation; separate follow-up if desired).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Dead function | `app/gm/creation.py` `get_step_prompt` (742–833) | Only definition; duplicate RACE table logic vs `format_races_table()` (605–616) |
| Live tables | `app/gm/creation.py` `format_races_table`, `format_roll_stats_table`, `format_classes_table`, … | Sole runtime table sources |
| Live orchestration | `app/gm/orchestrator.py` `_creation_turn`, `_auto_present_*`, `_handle_creation_response`, `_compose_creation_narration` | No reference to `get_step_prompt` |
| Dead sibling (out of scope) | `app/gm/orchestrator.py` `_creation_llm_loop` (1161+) | Zero callers; tool loop + `set_creation_choice` |
| Global LLM prompt (out of scope) | `app/gm/system_prompt.py` § CHARACTER CREATION (29–38) | Still instructs `set_creation_choice` + LLM tables |
| Tool registry | `app/gm/tools.py` `set_creation_choice` | Still registered; `_execute_tool` allows it during `creation.active` but code-first path does not invoke LLM tools for desk steps |
| Parallel pattern (keep) | `app/gm/combat_fsm.py` `get_combat_step_prompt` | Used by orchestrator ~1499 — not analogous dead code |

## Code-path traces

### Live: code-first creation turn

1. Entry: `orchestrator.py` `process_turn` → `_creation_turn` when `creation.active` (~660)
2. Router: `_creation_turn_body` (~667) branches on `creation.step` → `_auto_roll_stats`, `_auto_present_*`, or `_handle_creation_response`
3. Flavor: `_auto_present_*` → `_narrate_flavor(_creation_flavor_messages(per-step instruction, …))` (~606–627, ~764+)
4. Body: `format_races_table()` / `format_skills_table()` / etc. appended in `_compose_creation_narration` (~546–580)
5. Commit: `_execute_creation_choice` (~1262) from `_handle_creation_response` parsers — **not** from `get_step_prompt` text
6. Exit: footer `format_creation_status()`; persistence via session export / bridge on finalize

### Dead: `get_step_prompt` (never reached)

1. Definition only: `creation.py:742` — would return step-specific strings if called
2. RACE branch (~755–770): duplicates table construction; instructs “output EXACT markdown table” + `set_creation_choice`
3. SKILLS/SPELL_* branches (~797–813): stub “handled by code” (already aligned with APP-012 intent but unused)
4. No import in `orchestrator.py` import block (lines 16–48 list `format_*` helpers only)

### Dead: `_creation_llm_loop` (related, not APP-074)

1. Defined `orchestrator.py:1161`; grep shows definition only
2. Would call `set_creation_choice` via LLM tool_calls; never wired from `_creation_turn`

## Existing specs & docs

- **Ticket domain spec:** Documents code-first FSM, `_auto_present_*`, `format_*_table`, thin LLM flavor (APP-012). Does **not** name `get_step_prompt`; close should add explicit “no legacy step prompt builder” bullet per ticket AC.
- **APP-059 ticket** still cites `get_step_prompt()` RACE table as problem source — update that ticket prose when APP-074 closes (backlog hygiene, not domain spec).
- **Prior runs:** APP-067/072 research confirmed dead path; APP-072 deferred removal to APP-074.

## Tests & commands

```bash
# No test imports get_step_prompt; regression = existing creation suite
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q

# Post-delete verification
rg "get_step_prompt" app/
```

No new test required for deletion-only chore unless PM wants a negative grep guard in `test_creation_tables.py` (optional, not in ticket AC).

## Risks & unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Agent re-wires `get_step_prompt` from stale docs | Medium | Delete function; spec changelog; grep AC |
| `system_prompt.py` still contradicts code-first | Medium (confusion) | Out of scope; note in spec or separate ticket |
| APP-059 backlog text still references removed symbol | Low | Edit `app-059-*.md` on APP-074 close |
| Confusion with `get_combat_step_prompt` | Low | Different symbol; combat path stays |
| `_creation_llm_loop` removal bundled by mistake | Low | Ticket Expected files = `creation.py` + domain spec only |

## Raw notes

### Grep: `get_step_prompt`

```
app/gm/creation.py:742:def get_step_prompt(state: CreationState) -> str:
```

No matches in `app/tests/`, `play/`, or imports.

### `get_step_prompt` branch inventory (742–833)

| Step | Returns | Legacy behavior |
|------|---------|-----------------|
| NAME | Tool mandate + scene text | `set_creation_choice(NAME)` |
| RACE | Inline 16-race Description table + tool mandate | Conflicts with APP-072 “code owns table” |
| ROLL_STATS | `""` | Already vacated (APP-067) |
| CLASS | Stats line + eligible class prose + tool mandate | Superseded by `format_classes_table` + `_auto_roll_stats` |
| SKILLS / SPELL_SCHOOLS / SPELLS | “handled by code” | Matches live path but unused |
| EQUIPMENT_GOLD | Kit/gold prose + confirm tool mandate | Superseded by `format_equipment_summary` + parsers |
| FINALIZE / WORLD_INTRO | `""` | N/A |

### Ticket line-number drift

Ticket cites ~639–728; function now at **742–833** after APP-067/072 insertions (`format_roll_stats_table`, sanitizers).

### Orchestrator import excerpt (no `get_step_prompt`)

`from gm.creation import (` … `format_races_table`, `format_roll_stats_table`, … `)` — lines 16–48.

### Acceptance mapping

| AC | Research finding |
|----|------------------|
| Remove `get_step_prompt` | Safe delete; no callers |
| Grep `app/` clean | Expected after delete |
| Spec: prompts in `_auto_present_*` / `format_*` only | Spec already describes pattern; add explicit negation on close |
