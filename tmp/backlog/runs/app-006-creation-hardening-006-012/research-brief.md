# Research Brief: APP-006-creation-hardening-006-012

**Date:** 2026-05-20
**Question:** What remains to harden the creation FSM after APP-002–005 logging?

**backlog_ticket:** APP-006 (batch: APP-006–012)
**ticket_path:** tmp/backlog/app-006-deterministic-creation-tables-from-code.md
**domain_spec:** tmp/app-character-creation-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) owns `app/gm/creation.py` and creation branch of `orchestrator.py`. APP-008 cross-refs [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md). No new domain spec required.

## Summary

Partial implementation existed: `format_skills_table`, `format_schools_table`, `format_spells_table`, and `ensure_equipment_gold` in `creation.py`, but orchestrator still asked the LLM to emit tables verbatim. `_llm_loop` could run during creation via `process_turn("look around")` fallbacks. Resume overwrote restored creation step with `NAME`. Finalize did not assert non-empty roster. Wrong-step inputs like "Yes" at spell steps could confuse players. APP-012 decision documented in spec as thin LLM flavor + code body/footer.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Creation FSM | `app/gm/creation.py` | Steps, tables, parsers, `CreationState` |
| Turn loop | `app/gm/orchestrator.py` | `_creation_turn`, `_auto_finalize`, `_llm_loop` |
| Session persist | `app/ui/app.py`, `app/session_state.json` | `creation_state` export/import |
| Engine | `app/gm/bridge.py` | `character_create`, `status().roster` |

## Tests & commands

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m py_compile app/gm/creation.py app/gm/orchestrator.py
```

## Risks & unknowns

- `_creation_llm_loop` retained but unused after code-first NAME/RACE/CLASS; safe dead code for now.
- WORLD_INTRO after finalize sets `active=False`; next turn uses exploration loop (intended).
