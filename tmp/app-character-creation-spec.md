# Spec — App Character Creation

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress — **P0 hardening**  
**Owns:** `app/gm/creation.py`, creation branch of `app/gm/orchestrator.py`

---

## Problem (2026-05-20 session)

Gated steps (`SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, `EQUIPMENT_GOLD`) use `_narrate_only()`. Gemini invented equipment/PRE_DELVE while code stayed on `SPELL_SCHOOLS`. `character_create` never ran — empty roster, UI showed registered delver.

---

## Spec

Code-enforced state machine for new delvers at Registry (`32-C`).

### Steps (order)

`NAME` → `RACE` → `ROLL_STATS` → `CLASS` → `SKILLS` → (`SPELL_SCHOOLS` → `SPELLS` if caster) → `EQUIPMENT_GOLD` → `FINALIZE` → `WORLD_INTRO`

### Rules

- Apprentice/Novice with **Spellcasting** skill → must pick schools + tier-1 spells.
- Without Spellcasting → auto-skip schools/spells (`skip_inapplicable_spell_steps`).
- Tables emitted **by code**, not LLM-only.
- `character_create` + `roster_set` only in `_auto_finalize()` after equipment confirm.
- LLM adds **thin flavor only** (~120 tokens); cannot skip steps or emit false `[Phase: PRE_DELVE]`.

### LLM during creation (APP-012 decision)

**Chosen approach:** thin LLM wrapper — `_narrate_flavor()` for 1–2 sentences; **code** appends markdown tables, kit/GP numbers, and `format_creation_status()` footer. No exploration `_llm_loop` while `creation.active`. Interactive step validation is code-first (`_handle_creation_response`); LLM does not call tools for SKILLS/SCHOOLS/SPELLS/EQUIPMENT steps.

### Presentation pattern

```text
flavor = optional short LLM (~120 tokens, no tables, no phase tags)
body   = code-generated markdown (exact format_*_table output)
footer = code-generated status line (format_creation_status)
```

**Table catalog:** see [APP-059](backlog/app-059-standardize-creation-table-outputs.md) — canonical columns per step; enforced in `format_*_table()` (race/class/equipment still pending).

### Table-shown gating (APP-057)

Gated steps must not treat “field still empty” as “show table again” — that blocks commits on the next player turn.

| Step | Flag | Set in | `_creation_turn_body` auto-present when |
|------|------|--------|----------------------------------------|
| `RACE` | `races_table_shown` | `_auto_present_race` | `is_system_trigger` or `not races_table_shown` |
| `CLASS` | `classes_table_shown` | `_auto_present_class` | `is_system_trigger` or `not classes_table_shown` |
| `SKILLS` | `skills_table_shown` | `_auto_present_skills` | `is_system_trigger` or `not skills_table_shown` |
| `SPELL_SCHOOLS` | `schools_table_shown` | `_auto_present_schools` | same pattern |
| `SPELLS` | `spells_table_shown` | `_auto_present_spells` | same pattern |

`_execute_creation_choice` rejects RACE/CLASS/SKILLS/SCHOOLS/SPELLS if the step’s `*_table_shown` is false (player must see the code table first).

**Chain after commit:** `_chain_after_creation_choice` appends the next step’s table in the **same** narration when advancing to `RACE`, `CLASS` (after roll), `SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, or `EQUIPMENT_GOLD`. Required for APP-057: **NAME→RACE** and **ROLL_STATS→CLASS** (stats roll + `format_classes_table()` in one response after race pick).

### Canon data

- Races, classes, skills: `creation.py` + `build/data/character/`
- Starting kits/spells: `build/data/character/starting-kits.json`, `starting-spells.json`

---

## Task checklist

- [x] `CreationState` + step enum + parsers (`parse_player_skills`, etc.)
- [x] Code-first handling for SKILLS, schools, spells, equipment confirm
- [x] Code appends `format_*_table()` + `format_equipment_summary()` (APP-006)
- [x] `format_creation_status()` + strip LLM status tags (APP-007)
- [x] Hard gate exploration during creation (APP-008)
- [x] Finalize roster non-empty gate (APP-009)
- [x] Resume restores creation step from session_state (APP-010)
- [x] Invalid input at wrong step re-shows table + error (APP-011)
- [x] LLM flavor decision documented and implemented (APP-012)
- [x] `_auto_finalize` → `character_create` with kit cost guard

- [x] Integration test `test_creation_flow.py` — full FSM through finalize (APP-057)

**Open work:** [APP-059](backlog/app-059-standardize-creation-table-outputs.md). Militia spell-skip integration test deferred (post APP-057).

### Status line labels (code-owned)

| Step | Awaiting label |
|------|----------------|
| `NAME` | `NAME_INPUT` |
| `RACE` | `RACE_INPUT` |
| `SPELL_SCHOOLS` | `SPELL_SCHOOLS_INPUT` |
| `EQUIPMENT_GOLD` | `EQUIPMENT_GOLD_CONFIRMATION` |
| `WORLD_INTRO` | `RECEPTION_CHOICE` |

---

## Tests

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q
```

### Integration test (APP-057)

**Module:** `app/tests/test_creation_flow.py`  
**Fixtures:** test uses **`orchestrator` only** from `app/tests/conftest.py` (APP-049), which transitively applies **`mock_openrouter_client`**. Do not import `Orchestrator` at module level before fixtures run.  
**Drive:** `orchestrator.process_turn(text)` end-to-end — not parser unit tests.  
**Prerequisite behavior (APP-057 in scope):** RACE/CLASS `*_table_shown` gating + NAME→RACE / ROLL_STATS→CLASS chain — see § Table-shown gating.

#### Primary: `test_full_creation_apprentice_caster`

Eight `process_turn` inputs; tables may appear in the **prior** turn via chain.

| # | Input | Step after |
|---|--------|------------|
| 1 | `new game` | `NAME` |
| 2 | `Dumpy` | `RACE` (race table chained in same narration) |
| 3 | `human` | `CLASS` (roll + class table chained) |
| 4 | `apprentice` | `SKILLS` |
| 5 | `Lore, Spellcasting, Arcana` | `SPELL_SCHOOLS` |
| 6 | `pyromancy, ether` | `SPELLS` |
| 7 | `ember-touch, static-lash` | `EQUIPMENT_GOLD` |
| 8 | `yes` | `WORLD_INTRO` |

**Setup:** `monkeypatch` on `orchestrator.bridge.roll_attributes` returning fixed `eligible_classes` (includes `apprentice`), `INT >= 8`, `ok: True`.

**Required assertions after final turn:**

| Check | Expected |
|-------|----------|
| `orchestrator.creation.active` | `False` |
| `orchestrator.creation.step` | `WORLD_INTRO` |
| `bridge.status()["roster"]` | non-empty |
| `bridge.status()["awaiting"]` | `PLAYER_ACTIONS` |
| Roster entry | `display_name == "Dumpy"`, `base_class == "apprentice"` |
| Final narration | contains `Awaiting: RECEPTION_CHOICE` and `Phase: preparation` |

**Out of scope (APP-057):** Militia non-caster path (spell steps skipped) — follow-up ticket.

#### Other scenarios (existing / future)

| Scenario | Asserts | Owner |
|----------|---------|-------|
| Apprentice + Spellcasting (manual) | skills → schools → spells → equipment → finalize; roster populated | Human playtest |
| LLM wrong content | tables still match `format_*_table()` | Manual / future |
| `"Yes"` at `SPELL_SCHOOLS` | no PRE_DELVE | `test_creation_gating.py` |
| Status line | matches `creation.step` | Manual / APP-007 |

**Acceptance:** Replay Dumpy flow — cannot reach PRE_DELVE without `character_create` logged. APP-057 automates the Apprentice path above.

---

## Open decisions

_All P0 creation decisions closed (APP-012: thin LLM flavor)._

## File map

| File | Role |
|------|------|
| `gm/creation.py` | State machine, tables, parsers |
| `gm/orchestrator.py` | `_creation_turn`, `_auto_present_*`, `_auto_finalize`, `_execute_creation_choice` |
| `gm/choice_memory.py` | Remember creation choices |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | APP-006–012: code-owned tables/status, exploration gate, finalize roster gate, resume step restore, invalid-input guards, thin LLM flavor decision |
| 2026-05-20 | Spec created; merged creation-orchestrator-hardening content |
| 2026-05-20 | APP-057 spec draft: integration test contract in § Integration test; militia spell-skip deferred |
| 2026-05-20 | APP-057 spec r2: § Table-shown gating (RACE/CLASS flags + chain); integration turn table; fixture import discipline; orchestrator fixes in ticket scope |
| 2026-05-20 | APP-057 done: `test_full_creation_apprentice_caster` green; `races_table_shown`/`classes_table_shown` + NAME→RACE / ROLL_STATS→CLASS chain in orchestrator |
