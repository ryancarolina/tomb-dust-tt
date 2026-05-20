# Spec: APP-074-remove-dead-step-prompt

**Status:** draft  
**backlog_ticket:** APP-074  
**ticket_path:** [tmp/backlog/app-074-remove-dead-get-step-prompt.md](../../app-074-remove-dead-get-step-prompt.md)  
**domain_spec:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-character-creation-spec.md`

## Problem

`get_step_prompt(state)` in `app/gm/creation.py` (lines **742–833**) is **legacy LLM-step instruction text** from the pre–code-first creation path. It mandates `set_creation_choice` tool calls and, for RACE, builds an inline `| Race | Adjustments | Description |` table from `RACES` — duplicating `format_races_table()`.

**Zero callers** exist under `app/`, `play/`, or `app/tests/`. `orchestrator.py` imports `format_*` helpers only; it does not import `get_step_prompt`. Dead code risks agents or docs re-wiring the old LLM-driven desk path.

**Contrast (keep):** `get_combat_step_prompt` in `combat_fsm.py` is live — imported and used by orchestrator for exploration combat context. Not analogous dead code.

## Goals

- Delete `get_step_prompt()` from `creation.py`.
- Confirm `rg "get_step_prompt" app/` returns no matches after delete.
- Domain spec explicitly states creation step **body** and **footer** live only in `_auto_present_*` / `format_*_table` / `format_creation_status()` — no legacy step prompt builder.

## Non-goals

| Deferred | Notes |
|----------|-------|
| `app/gm/system_prompt.py` § CHARACTER CREATION | Still instructs `set_creation_choice` + LLM tables — separate follow-up if desired |
| `orchestrator.py` `_creation_llm_loop` | Zero callers; tool loop + `set_creation_choice` — out of ticket Expected files |
| `format_races_table()` Description column removal | [APP-059](../../app-059-standardize-creation-table-outputs.md) |
| Negative grep guard test in `test_creation_tables.py` | Optional; not in ticket AC |
| Backlog hygiene: APP-059 ticket prose still cites `get_step_prompt` as problem source | Update `app-059-*.md` on APP-074 **close**, not PM spec pass |

## Requirements

Full behavior contract: domain spec § **Step content sources (APP-074)**.

### R1: Remove dead function

**Acceptance criteria**

- [ ] `get_step_prompt` function deleted from `app/gm/creation.py` (~92 lines).
- [ ] No imports, references, or docstring mentions of `get_step_prompt` under `app/`.

### R2: Live path unchanged (code-first only)

**Acceptance criteria**

- [ ] Creation turn routing unchanged: `process_turn` → `_creation_turn` → `_creation_turn_body` → `_auto_present_*` / `_auto_roll_stats` / `_handle_creation_response`.
- [ ] Step **body** remains sole output of `format_*_table()` / `format_equipment_summary()` appended in `_compose_creation_narration`.
- [ ] Step **flavor** remains thin `_narrate_flavor` via `_creation_flavor_messages` — no tool mandates, no inline tables.
- [ ] Player commits via `_execute_creation_choice` from code parsers — not LLM `set_creation_choice` during desk steps.

### R3: Domain spec sync

**Acceptance criteria**

- [ ] Domain spec § Step content sources documents code-first-only pattern and negates `get_step_prompt`.
- [ ] Changelog entry on ticket close: removed legacy prompt builder.

## Acceptance criteria mapping

| Ticket AC | Spec / verification |
|-----------|---------------------|
| Remove `get_step_prompt()` | R1 |
| Grep `app/` confirms no references | R1 — `rg "get_step_prompt" app/` |
| Spec: prompts in `_auto_present_*` / `format_*` only | R2 + R3 — domain spec § Step content sources |

## Test plan

No new test required (deletion-only chore). Regression = existing creation suite:

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q

# Post-delete verification
rg "get_step_prompt" app/
```

All commands must pass; grep must return zero matches.

## Expected files (implementation)

- `app/gm/creation.py` — delete `get_step_prompt`
- `tmp/app-character-creation-spec.md` — § Step content sources + changelog on close

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Smoke:** `new game` → name → race — narration still shows single code race table + `Awaiting: RACE_INPUT` (no behavior change expected).
- **Full path:** Replay Dumpy golden path (APP-057) — all tables and footers unchanged.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — code traces, branch inventory, risks
- **Domain truth:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md) — § Presentation pattern, § Step content sources (APP-074)
- **Related:** APP-059 (formatter catalog; backlog text cites dead symbol), APP-072 (code-owned RACE body), APP-067 (ROLL_STATS vacated in dead prompt)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft |
