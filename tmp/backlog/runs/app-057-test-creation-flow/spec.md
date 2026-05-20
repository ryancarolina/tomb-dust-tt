# Spec: APP-057-test-creation-flow

**Status:** draft (revision 2 — QA round 1 fixes)  
**backlog_ticket:** APP-057  
**ticket_path:** tmp/backlog/app-057-test-creation-flow.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**registry_gap:** false  
**Domain specs touched:** [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) — § Integration test (APP-057), § Table-shown gating, Tests, Task checklist, Changelog (spec draft)

## Summary

Add `app/tests/test_creation_flow.py`: an orchestrator integration test that drives the full character-creation FSM via `process_turn()` (no live LLM), through `_auto_finalize` and engine `character_create`, and asserts a non-empty roster plus post-finalize engine/UI gates.

**Revision 2 (PM):** Expand scope to include **minimal orchestrator + `CreationState` fixes** so the canonical 8-input path is runnable. Ticket intent is guarding creation drift regressions; a test that cannot reach finalize is useless. No split ticket unless human blocks.

**Pointers**

| Topic | Location |
|-------|----------|
| FSM steps, caster rules, spell skip | [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) § Spec, § Table-shown gating, § Integration test (APP-057) |
| Code paths | [`research-brief.md`](research-brief.md) — traces, input table, fixture inventory |
| Fixtures (`orchestrator`, mocks) | [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) · `app/tests/conftest.py` (APP-049) |
| Parser-only coverage | `play/tomb_gm/tests/test_creation_gating.py` (not duplicated) |
| Ticket AC | [`app-057-test-creation-flow.md`](../../app-057-test-creation-flow.md) |

## Problem

Creation hardening (APP-006–012) fixed code-owned tables and finalize gates, but there is no **app-layer** integration test that replays the Dumpy-style flow through `Orchestrator.process_turn`. Regressions can leave `creation.active` true, an empty roster, or wrong `awaiting` without failing engine parser tests.

**QA round 1 blockers:** On current code, RACE/CLASS auto-present gates on empty `race` / `chosen_class` (not `*_table_shown`), so player picks never commit; NAME→RACE and ROLL_STATS→CLASS are not chained like SKILLS→SPELL_SCHOOLS. The spec’s 8-input table does not reach finalize without orchestrator fixes.

## Goals

- One primary pytest: **Apprentice + Spellcasting** full FSM (all gated steps including schools/spells).
- Deterministic `bridge.roll_attributes` via inline `monkeypatch` (no flake from random eligibility).
- Assert finalize outcomes: non-empty roster, `creation.active` false, `creation.step == WORLD_INTRO`, `status["awaiting"] == PLAYER_ACTIONS`.
- **Minimal orchestrator/creation fixes** so the integration test path is achievable (see R6).
- Command gate: `python -m pytest app/tests/test_creation_flow.py -q` exits 0.

## Non-goals

- **Militia non-caster spell-skip test** — deferred (see PM decision below).
- JSONL / `creation_drift` log assertions (APP-002).
- Mid-creation resume (APP-010).
- LLM narration content matching tables (mock returns fixed string; tables are code-owned).
- Exact GP from `ensure_equipment_gold` random roll (optional `random.randint` patch not required).
- New shared conftest fixture unless Dev proves inline monkeypatch is duplicated across modules (prefer inline in test module).
- Broad creation UX refactors, APP-059 table column standardization, or LLM prompt changes for `_auto_roll_stats` flavor (only chain/table fixes required for APP-057).

## PM decision: Militia spell-skip test

**Out of scope for APP-057** — defer to a follow-up ticket (e.g. `APP-057b` or backlog note on APP-059/QA).

**Rationale:** Ticket AC requires one path through finalize with non-empty roster; domain spec’s canonical acceptance scenario is Apprentice + Spellcasting. Militia validates `skip_inapplicable_spell_steps` mid-FSM — valuable but orthogonal to the P0 “empty roster after finalize” guard.

## PM decision: Scope expansion (SCOPE-001)

**In scope for APP-057 (revision 2):** Minimal fixes in `app/gm/orchestrator.py` and `app/gm/creation.py` required for the integration test to pass. Test-only delivery without these fixes contradicts ticket intent.

| Fix area | Requirement |
|----------|-------------|
| RACE/CLASS gating | Mirror SKILLS: `races_table_shown` / `classes_table_shown` on `CreationState`; gate `_creation_turn_body` auto-present on `not *_table_shown` or `is_system_trigger`; set flags in `_auto_present_race` / `_auto_present_class`; persist in `to_dict` / `from_dict`; reset on `advance()` into step if needed |
| Chain NAME→RACE | After NAME commit, `_chain_after_creation_choice` appends `_auto_present_race` when `step == RACE` (same pattern as SKILLS chain) |
| Chain ROLL_STATS→CLASS | After RACE→ROLL_STATS chain, class table must appear in the **same** turn output as stats roll: either `_chain_after_creation_choice` handler for `step == CLASS` calling `_auto_present_class`, and/or code-owned `format_classes_table()` in `_auto_roll_stats` return (not LLM-only) |
| `_execute_creation_choice` | Reject RACE/CLASS commits when `*_table_shown` is false (mirror SKILLS guard at `orchestrator.py:1212+`) |

## Requirements

### R1: Module and fixtures

**Acceptance criteria**

- [ ] New file `app/tests/test_creation_flow.py` under `app/tests/`.
- [ ] Test function uses **`orchestrator` fixture only** from `app/tests/conftest.py` (APP-049). That fixture **transitively** applies `mock_openrouter_client` (patches `create_client` before `Orchestrator` is constructed).
- [ ] **Forbidden:** module-level `from gm.orchestrator import Orchestrator` (or any import that constructs `Orchestrator` before pytest fixtures run). APP-049 lesson: patches must apply first.
- [ ] **Forbidden:** duplicating `mock_openrouter_client` setup inline unless a second test module needs it.
- [ ] Does **not** import or duplicate `play/tomb_gm/tests/test_creation_gating.py` parser tests.

### R2: Deterministic roll mock

**Acceptance criteria**

- [ ] Before turn loop, `monkeypatch.setattr(orchestrator.bridge, "roll_attributes", lambda race: FIXED_ROLL)` (or equivalent) where `FIXED_ROLL` includes:
  - `"ok": True`
  - `"eligible_classes"` containing at least `"apprentice"` (and ideally `"militia"`, `"peasant"` for future tests)
  - `"final_attributes"` with `INT >= 8` (apprentice gate)
  - `"race"` echoing the `race` argument
- [ ] Module-level constant or fixture-local dict documented in test file (see research-brief sketch).

### R3: Primary test — `test_full_creation_apprentice_caster`

**Acceptance criteria**

- [ ] Single test function drives `orchestrator.process_turn(text)` in order (8 player inputs; tables may appear in **prior** turn narration via chain):

| # | Input | `creation.step` after turn | What happens (code contract) |
|---|--------|----------------------------|------------------------------|
| 1 | `"new game"` | `NAME` | `creation.active` True; `_auto_present_name` |
| 2 | `"Dumpy"` | `RACE` | NAME committed; **chain** appends race table in same narration |
| 3 | `"human"` | `CLASS` | RACE committed; **chain** runs `_auto_roll_stats` then presents class table (stats + eligible classes in one response) |
| 4 | `"apprentice"` | `SKILLS` | CLASS committed; **chain** appends skills table |
| 5 | `"Lore, Spellcasting, Arcana"` | `SPELL_SCHOOLS` | SKILLS committed; chain presents schools table |
| 6 | `"pyromancy, ether"` | `SPELLS` | Schools committed; chain presents spells table |
| 7 | `"ember-touch, static-lash"` | `EQUIPMENT_GOLD` | Spells committed; chain presents equipment summary |
| 8 | `"yes"` | `WORLD_INTRO` | Equipment confirm → FINALIZE → `_auto_finalize`; `creation.active` False |

- [ ] After loop, `status = orchestrator.bridge.status()`.

**Post-finalize assertions (required)**

| Assert | Expected |
|--------|----------|
| `orchestrator.creation.active` | `False` |
| `orchestrator.creation.step` | `"WORLD_INTRO"` |
| `len(status["roster"])` | `>= 1` |
| `status["awaiting"]` | `"PLAYER_ACTIONS"` |
| `status["roster"][0]["display_name"]` | `"Dumpy"` (verify field name at impl — engine uses `display_name`) |
| `status["roster"][0]["base_class"]` | `"apprentice"` (or equivalent sheet key) |
| Final `process_turn` return (`last`) | substring `"Awaiting: RECEPTION_CHOICE"` |
| Final narration | substring `"Phase: preparation"` (not `PRE_DELVE` / delve phases) |

**Optional (nice-to-have, not AC blockers)**

- [ ] Assert chosen skills appear on roster/sheet if exposed in `status["roster"][0]`.
- [ ] `status.get("party", {}).get("phase")` aligns with preparation if present.

### R4: conftest.py changes

**Acceptance criteria**

- [ ] `app/tests/conftest.py` modified **only if** a new shared fixture is required (e.g. shared `FIXED_ROLL` across multiple test modules).
- [ ] Default: no conftest change; roll mock stays in `test_creation_flow.py`.

### R5: Domain spec sync (on ticket close)

**Acceptance criteria**

- [ ] Dev/PM marks APP-057 checklist item done in [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md).
- [ ] Changelog entry dated on close (not draft-only).

### R6: Orchestrator / creation fixes (in scope)

**Acceptance criteria**

- [ ] `CreationState` adds `races_table_shown: bool = False` and `classes_table_shown: bool = False`; serialized in `to_dict` / `from_dict`; reset when advancing into `RACE` / `CLASS` if mirroring SKILLS reset pattern.
- [ ] `_creation_turn_body`: RACE branch uses `(is_system_trigger or not self.creation.races_table_shown)` for auto-present; CLASS uses `(is_system_trigger or not self.creation.classes_table_shown)` — **not** `not self.creation.race` / `not self.creation.chosen_class`.
- [ ] `_auto_present_race` sets `races_table_shown = True`; `_auto_present_class` sets `classes_table_shown = True`.
- [ ] `_chain_after_creation_choice`: when `step == "RACE"`, append `_auto_present_race(...)`; when `step == "CLASS"` after roll, append `_auto_present_class(...)` (or equivalent so turn 3 output includes class table).
- [ ] `_execute_creation_choice` rejects RACE/CLASS if respective `*_table_shown` is false (consistent with SKILLS).
- [ ] Manual or test verification: 8-input sequence reaches finalize with non-empty roster.

## Test plan

```bash
# Primary gate (APP-057)
python -m pytest app/tests/test_creation_flow.py -q

# Related — must remain green; not owned by this ticket
python -m pytest app/tests/test_smoke.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

**Expected after implementation:** ≥1 test collected in `test_creation_flow.py`, exit code 0; no writes under `play/workspace`.

## Human playtest hints (for Stage 7)

- Manual replay optional: PyGame `new game` → same inputs as table → confirm roster panel shows Dumpy and phase preparation at Registry.
- Primary validation is automated; human plan can reference “mirror APP-057 pytest inputs.”

## Affected paths

Must match ticket **Expected files**:

- `app/tests/test_creation_flow.py` (new)
- `app/gm/orchestrator.py` (RACE/CLASS gating, chain handlers, execute guards)
- `app/gm/creation.py` (`CreationState` flags + serialization)
- `app/tests/conftest.py` (extend only if necessary)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM spec draft (APP-057); militia spell-skip test deferred |
| 2026-05-20 | **R2:** QA round 1 fixes — expanded scope (orchestrator + creation), RACE/CLASS table-shown gating, NAME→RACE / ROLL_STATS→CLASS chain, R1 fixture/import discipline, turn table aligned with chain behavior |
