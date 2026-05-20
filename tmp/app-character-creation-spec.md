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
- LLM adds flavor only; cannot skip steps or emit false `[Phase: PRE_DELVE]`.

### Presentation pattern

```text
flavor = optional short LLM (~120 tokens, no tables, no phase tags)
body   = code-generated markdown (exact format_*_table output)
footer = code-generated status line (format_creation_status)
```

### Canon data

- Races, classes, skills: `creation.py` + `build/data/character/`
- Starting kits/spells: `build/data/character/starting-kits.json`, `starting-spells.json`

---

## Task checklist

- [x] `CreationState` + step enum + parsers (`parse_player_skills`, etc.)
- [x] Code-first handling for SKILLS, schools, spells, equipment confirm
- [x] `_auto_finalize` → `character_create` with kit cost guard
- [ ] **Deterministic tables** — code appends `format_skills_table()`, `format_schools_table()`, `format_spells_table()`, kit/GP from `ensure_equipment_gold()`
- [ ] **Code-owned status line** — `format_creation_status(creation)`; strip LLM `[Location: …]` blocks
- [ ] **Hard gate** — no `_llm_loop` / exploration tools while `creation.active` (except FINALIZE/WORLD_INTRO)
- [ ] **Finalize gate** — assert `bridge.status().roster` non-empty after finalize; stay in creation on failure
- [ ] **Persist creation** — resume exact step from `session_state.json`; sync if engine has roster
- [ ] Invalid input at wrong step (e.g. `Yes` at `SPELL_SCHOOLS`) → re-show table + error

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
python -m pytest app/tests/test_creation_flow.py -q   # when added
```

| Scenario | Asserts |
|----------|---------|
| Apprentice + Spellcasting | skills → schools → spells → equipment → finalize; roster populated |
| LLM wrong content | tables still match `format_*_table()` |
| `"Yes"` at `SPELL_SCHOOLS` | no PRE_DELVE |
| Status line | matches `creation.step` |

**Acceptance:** Replay Dumpy flow — cannot reach PRE_DELVE without `character_create` logged.

---

## Open decisions

1. **LLM flavor during creation** — thin wrapper (recommended) or zero LLM until `WORLD_INTRO`?

---

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
| 2026-05-20 | Spec created; merged creation-orchestrator-hardening content |
