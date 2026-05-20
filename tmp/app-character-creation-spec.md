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

**Table catalog:** § [Creation tables](#creation-tables) below; full standardization tracked in [APP-059](backlog/app-059-standardize-creation-table-outputs.md). **ROLL_STATS** catalog and formatter contract added by APP-067.

### Table-shown gating (APP-057)

Gated steps must not treat “field still empty” as “show table again” — that blocks commits on the next player turn.

| Step | Flag | Set in | `_creation_turn_body` auto-present when |
|------|------|--------|----------------------------------------|
| `RACE` | `races_table_shown` | `_auto_present_race` | `is_system_trigger` or `not races_table_shown` |
| `CLASS` | `classes_table_shown` | `_auto_roll_stats` (chain) or `_auto_present_class` (direct/resume) | `is_system_trigger` or `not classes_table_shown` |
| `SKILLS` | `skills_table_shown` | `_auto_present_skills` | `is_system_trigger` or `not skills_table_shown` |
| `SPELL_SCHOOLS` | `schools_table_shown` | `_auto_present_schools` | same pattern |
| `SPELLS` | `spells_table_shown` | `_auto_present_spells` | same pattern |

`_execute_creation_choice` rejects RACE/CLASS/SKILLS/SCHOOLS/SPELLS if the step’s `*_table_shown` is false (player must see the code table first).

**Chain after commit:** `_chain_after_creation_choice` appends the next step’s table in the **same** narration when advancing to `RACE`, `ROLL_STATS`, `SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, or `EQUIPMENT_GOLD`. Required for APP-057/067: **NAME→RACE** and **RACE→ROLL_STATS→CLASS** — after race pick, `_auto_roll_stats` emits stats table + class table in **one** response (APP-067); chain must **not** also call `_auto_present_class` (duplicate class table).

#### NAME→RACE same-turn presentation (APP-068)

After a successful NAME commit (`_execute_creation_choice("NAME", …)` → `advance()` to `RACE`, `races_table_shown = False` per `creation.py`):

| ID | Requirement |
|----|-------------|
| **R1** | Same `process_turn` narration **must** include `_auto_present_race()` output: `body` = `format_races_table()` (intro `Pick **one race**` + header `\| Race \| Adjustments \| Description \|`) and `footer` from `format_creation_status()` → **`Awaiting: RACE_INPUT`**. Thin LLM flavor via `_narrate_flavor` inside `_auto_present_race` is allowed; it is **not** a substitute for the code table. Set `races_table_shown = True` before return. |
| **R2** | When `creation.step == "RACE"` and race is unset, narration **must not** be exactly `"The clerk waits."` (the `_chain_after_creation_choice` default `return prior or "The clerk waits."` when no step branch matches). NAME success must invoke the `RACE` chain branch or return `_auto_present_race(...)` directly — never the empty-prior fallthrough. |

**Observed failure (regression target):** `creation_advanced` `NAME`→`RACE` logged while `gm_narration` is only `"The clerk waits."` with no `llm_request` — chain did not call `_auto_present_race`. See APP-068 ticket / `app/logs/session-2026-05-20.jsonl`.

### Creation tables

Code-owned markdown tables per step. LLM flavor is ≤2 sentences **before** the table block; never invents table cells.

| Step | Formatter | In-table columns | Out of table |
|------|-----------|------------------|--------------|
| RACE | `format_races_table()` | Race, Adjustments, Description | Registry clerk banter (flavor only) |
| **ROLL_STATS** | `format_roll_stats_table(roll_result)` | Attr, Base, Genetic, Life Evt, Racial, Final | Life event **name** on intro line above table; HP line below table |
| CLASS | `format_classes_table(eligible)` | Class, Requirement, Key skills, Starting GP | Class fantasy blurb |
| SKILLS | `format_skills_table(chosen_class)` | Category, Skill, Class key? | Pick rules in intro lines |
| SPELL_SCHOOLS | `format_schools_table(chosen_class)` | School, Tradition, Themes | Pick rules in intro lines |
| SPELLS | `format_spells_table(...)` | Spell, School, MP, Effect | Full spell text in canon only |
| EQUIPMENT_GOLD | `format_equipment_summary(state)` | Kit, Starting GP, Confirm prompt | Clerk commentary (flavor) |

#### `format_roll_stats_table(roll_result)` (APP-067)

**Input:** successful `GameBridge.roll_attributes()` dict (see [`app-gamebridge-spec.md`](app-gamebridge-spec.md) / `bridge.py`). Formatter reads payload fields only — no re-roll, no LLM.

**Intro line:** `Life event: {life_event["name"]}` (or equivalent single line citing `roll_result["life_event"]["name"]`).

**Table header:** `| Attr | Base | Genetic | Life Evt | Racial | Final |`

**Rows STR, AGI, STA, INT, SPI** — one row per attribute:

| Column | Source |
|--------|--------|
| Base | `base_rolls[attr]` |
| Genetic | `genetic_factors[attr]["mod"]` |
| Life Evt | `life_event["mods"].get(attr, 0)` |
| Racial | `racial_adjustments.get(attr, 0)` |
| Final | `final_attributes[attr]` — **authoritative**; may differ from column sum when bridge applies `max(1, …)` clamp |

**LUC row contract:** LUC is not broken out in `base_rolls` / `genetic_factors` / `life_event.mods`. Show one LUC row with `—` in Base, Genetic, Life Evt, and Racial columns; **Final** = `final_attributes["LUC"]` only.

**HP line (after table, blank line):** `**HP:** {hp} (10 + STA {sta} × 5)` where `sta = final_attributes["STA"]` and `hp = 10 + sta * 5` (canon: `build/systems/core/derived-stats.md`, `compute_hp()`).

**Clamp vs Final:** Tests and display use **Final** from `final_attributes`, not `Base + Genetic + Life Evt + Racial`. Do not assert or narrate recomputed sums when clamp changed a value.

#### ROLL_STATS orchestration (APP-067)

`_auto_roll_stats(player_input)`:

1. `bridge.roll_attributes(race)` → store `creation.roll_result`; `advance()` → step `CLASS`; `_remember_creation_step("ROLL_STATS")`.
2. `flavor = _narrate_flavor(...)` — brief attribute-roll color; **no tables, no stat math**.
3. `body = format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)`.
4. `creation.classes_table_shown = True` before return (CLASS commit guard in `_execute_creation_choice`).
5. `return _compose_creation_narration(flavor, body)` → footer `Awaiting: CLASS_INPUT`.

**Chain dedup:** `_chain_after_creation_choice` when `step == "ROLL_STATS"`: return `_auto_roll_stats(...)` only. Do **not** append `_auto_present_class` — roll path already includes `format_classes_table`.

**Direct CLASS path:** `_auto_present_class` remains for `_creation_turn_body` when `step == "CLASS"` and `not classes_table_shown`, invalid class re-prompt, and resume edges. Body is `**Final attributes:**` one-liner + `format_classes_table` (no full stats table repeat).

**Removed pattern:** `_narrate_only()` with JSON context instructing LLM to build the attribute table.

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

### Awaiting contract (engine vs app) — APP-066

Character creation uses **two layers** of “awaiting.” They are **not** required to match each other during desk creation.

| Layer | Owner | API / symbol | When set | Purpose |
|-------|--------|--------------|----------|---------|
| **Engine (coarse)** | `play/tomb_gm` | `bridge.status()["awaiting"]` | `handle_status`: empty roster and no character rows → `CHARACTER_CREATION`; after `character_create` + `roster_set` → `PLAYER_ACTIONS` | CLI `suggest`, save/resume gates, exploration LLM context (`gm/context.py`) |
| **App (granular)** | `app/gm/creation.py` | `CREATION_STATUS_LABELS[creation.step]` in `format_creation_status()` | Every creation narration footer from `CreationState.step` | Player-facing status line, suggestion chips (parse `Awaiting:`), **expected** label for `creation_drift` when `creation.active` |

**Step truth:** `CreationState.step` (persisted in `session_state.json` as `creation_state` on resume). Engine `awaiting` does **not** encode `SKILLS` vs `SPELL_SCHOOLS`; do not drive UI step badges from engine `awaiting` alone (see APP-036).

**Drift QA:** While `creation.active`, compare narrated `Awaiting:` to `CREATION_STATUS_LABELS[step]`, **not** to engine `CHARACTER_CREATION`. Mismatch vs the label map is real drift; match with engine still `CHARACTER_CREATION` is healthy.

**Post-finalize (`WORLD_INTRO`):** `creation.active` is false; engine `awaiting` is `PLAYER_ACTIONS`; footer may use `Awaiting: RECEPTION_CHOICE` and optional `Phase: preparation` — outside granular desk-creation contract (separate reception semantics).

### Status line labels (code-owned)

Single source: `CREATION_STATUS_LABELS` in `creation.py` (also imported by orchestrator drift check).

| Step | Awaiting label |
|------|----------------|
| `NAME` | `NAME_INPUT` |
| `RACE` | `RACE_INPUT` |
| `ROLL_STATS` | `STATS_REVIEW` |
| `CLASS` | `CLASS_INPUT` |
| `SKILLS` | `SKILLS_INPUT` |
| `SPELL_SCHOOLS` | `SPELL_SCHOOLS_INPUT` |
| `SPELLS` | `SPELLS_INPUT` |
| `EQUIPMENT_GOLD` | `EQUIPMENT_GOLD_CONFIRMATION` |
| `FINALIZE` | `FINALIZE` |
| `WORLD_INTRO` | `RECEPTION_CHOICE` |

Unknown step fallback (formatter + drift): `{step}_INPUT`.

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
| 2 | `Dumpy` | `RACE` (race table chained in same narration — **APP-068:** assert table + footer on this turn) |
| 3 | `human` | `CLASS` (roll + class table chained) |
| 4 | `apprentice` | `SKILLS` |
| 5 | `Lore, Spellcasting, Arcana` | `SPELL_SCHOOLS` |
| 6 | `pyromancy, ether` | `SPELLS` |
| 7 | `ember-touch, static-lash` | `EQUIPMENT_GOLD` |
| 8 | `yes` | `WORLD_INTRO` |

**Setup:** `monkeypatch` on `orchestrator.bridge.roll_attributes` returning fixed `eligible_classes` (includes `apprentice`), `INT >= 8`, `ok: True`. **`FIXED_ROLL`** must match production `roll_attributes` shape: `genetic_factors[attr]` = `{"roll": int, "mod": int}`; `base_rolls` keys STR–SPI only (no LUC); see APP-067.

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

#### APP-068: NAME→RACE narration assertions

After turn 2 (`"Dumpy"`) on fresh `new game`, when `creation.step == "RACE"`:

| Check | Expected |
|-------|----------|
| Race table intro | `Pick **one race**` in narration |
| Race table header | `\| Race \| Adjustments \| Description \|` in narration (`format_races_table`) |
| Footer | `Awaiting: RACE_INPUT` |
| Forbidden | narration stripped must **not** equal `"The clerk waits."` |
| `races_table_shown` | `True` |

May be a dedicated test (e.g. `test_name_advance_presents_race_table`) or assertions added to `test_full_creation_apprentice_caster` turn 2. Drive via `orchestrator.process_turn` with `mock_openrouter_client` fixture (same as APP-057).

#### APP-067: ROLL_STATS table assertions

After turn 3 (`"human"`), when `creation.step == "CLASS"`:

| Check | Expected |
|-------|----------|
| Table header | `Attr \| Base \| Genetic \| Life Evt \| Racial \| Final` in narration |
| STR–SPI / LUC finals | Markdown cells match `FIXED_ROLL["final_attributes"]` (assert **Final** column, not recomputed sum) |
| LUC row | Intermediate columns `—`; Final = `final_attributes["LUC"]` |
| HP line | `**HP:** 60` (or equivalent) for STA 10 — `10 + 10×5` |
| Class table | `format_classes_table` eligible rows present **once** (no duplicate from chain) |
| `classes_table_shown` | `True` after roll turn |

Optional unit test: `test_format_roll_stats_table(FIXED_ROLL)` in `test_creation_tables.py`.

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
| 2026-05-20 | APP-067 spec draft: `format_roll_stats_table`, ROLL_STATS catalog row, chain dedup, LUC/HP/clamp contracts, test assertions |
| 2026-05-20 | APP-057 done: `test_full_creation_apprentice_caster` green; `races_table_shown`/`classes_table_shown` + NAME→RACE / ROLL_STATS→CLASS chain in orchestrator |
| 2026-05-20 | APP-066 spec draft: § Awaiting contract (engine `CHARACTER_CREATION` vs app `CREATION_STATUS_LABELS`); full status label table |
| 2026-05-20 | APP-066 done: drift check uses `CREATION_STATUS_LABELS` when `creation.active`; engine `CHARACTER_CREATION` documented as coarse layer; golden-path test asserts no `creation_drift` |
| 2026-05-20 | APP-068 spec draft: § NAME→RACE same-turn presentation (R1 table+footer, R2 no clerk-waits); § Tests APP-068 narration assertions |
| 2026-05-20 | APP-068 done: NAME commit returns `_auto_present_race()` same turn (direct path in `_handle_creation_response`); chain RACE fallthrough guard; `test_name_advance_presents_race_table` + turn-2 assertions in `test_full_creation_apprentice_caster` green |
| 2026-05-20 | APP-067 done: `format_roll_stats_table` in `creation.py`; `_auto_roll_stats` thin flavor + code tables; ROLL_STATS chain dedup; `test_creation_flow.py` APP-067 assertions green |
