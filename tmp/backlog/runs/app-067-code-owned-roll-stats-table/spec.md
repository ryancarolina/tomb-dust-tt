# Spec: APP-067-code-owned-roll-stats-table

**Status:** draft  
**backlog_ticket:** APP-067  
**ticket_path:** tmp/backlog/app-067-code-owned-roll-stats-table.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**registry_gap:** false  
**Domain specs touched:** tmp/app-character-creation-spec.md

## Problem

`_auto_roll_stats()` still calls `_narrate_only()` with instructions for the LLM to render the attribute breakdown table. The LLM invents wrong column math (e.g. STR final 7 when `roll_attributes` returned 6). ROLL_STATS is the only gated creation step that missed APP-006/012 code-owned table pattern.

## Goals

- Add `format_roll_stats_table(roll_result)` in `creation.py`; every cell derived from `GameBridge.roll_attributes` payload only.
- Refactor `_auto_roll_stats()` to thin `_narrate_flavor()` + code body + `_compose_creation_narration()` — same pattern as `_auto_present_skills`.
- Emit stats table + class table + HP in one roll response; set `classes_table_shown`; dedupe chain so class table appears once.
- Test asserts table cells and HP match monkeypatched `FIXED_ROLL` (production fixture shape).

## Non-goals

- Changing roll logic in `GameBridge.roll_attributes` or unifying with `tomb_gm` CLI pipeline.
- APP-059 race/class column redesign (except ROLL_STATS catalog row added here).
- Removing stale `get_step_prompt` / `system_prompt` roll-table prose (optional cleanup; note in domain spec only).

## Requirements

**Authoritative behavior:** [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) § Creation tables (`ROLL_STATS` row), § ROLL_STATS orchestration, § Tests (APP-067).

### R1: Code-owned attribute table

**Acceptance criteria**

- [ ] `format_roll_stats_table(roll_result)` in `creation.py` — columns `Attr | Base | Genetic | Life Evt | Racial | Final`; life event name intro line; HP line after table.
- [ ] STR–SPI columns from payload fields only; **Final** from `final_attributes[attr]` (authoritative when clamp applies — do not recompute sum for display or tests).
- [ ] LUC row: `—` for Base/Genetic/Life Evt/Racial; Final from `final_attributes["LUC"]`.

### R2: Thin-flavor roll presentation

**Acceptance criteria**

- [ ] `_auto_roll_stats()` uses `_narrate_flavor()` + `format_roll_stats_table(result)` + `format_classes_table(eligible)` — no `_narrate_only` stat math.
- [ ] HP line `**HP:** {hp} (10 + STA {sta} × 5)` matches `10 + final_attributes["STA"] * 5`.
- [ ] Sets `classes_table_shown = True` when class table is embedded.
- [ ] Footer `CLASS_INPUT` via `_compose_creation_narration` (step already `CLASS` after advance).

### R3: Chain deduplication

**Acceptance criteria**

- [ ] `_chain_after_creation_choice` ROLL_STATS branch: call `_auto_roll_stats` only — **do not** append `_auto_present_class` (avoids duplicate class table).
- [ ] `_auto_present_class` unchanged for direct CLASS entry (invalid input, resume, `_creation_turn_body` when `not classes_table_shown`).

### R4: Tests

**Acceptance criteria**

- [ ] Update `FIXED_ROLL` to production shape: `genetic_factors[attr]` = `{"roll", "mod"}`; no `LUC` in `base_rolls`.
- [ ] After `"human"` turn, assert narration contains table cells from `FIXED_ROLL` finals and HP `60` for STA 10.
- [ ] Optional: dedicated `test_format_roll_stats_table` unit test.

## Test plan

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
# optional:
cd app && python -m pytest tests/test_creation_tables.py -q
```

## Human playtest hints (for Stage 7)

- New game → name → pick race → verify attribute table Base/Genetic/Life/Racial/Final match tool log in `app/logs/session-*.jsonl` (no off-by-one on STR or wrong racial column).
- Same turn: class table appears once; status footer shows class pick prompt.
- Continue/resume mid-creation at CLASS: class table re-shows without duplicate stats block if already shown.

## Affected paths

- `app/gm/creation.py`
- `app/gm/orchestrator.py`
- `app/tests/test_creation_flow.py` or `app/tests/test_creation_tables.py`
- `tmp/app-character-creation-spec.md`

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-067) |
