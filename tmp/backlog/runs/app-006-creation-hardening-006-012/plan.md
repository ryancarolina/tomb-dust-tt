# Implementation Plan: APP-006-creation-hardening-006-012

**Status:** approved
**backlog_ticket:** APP-006 … APP-012

## Approach

Single cohesive pass on `creation.py` + `orchestrator.py`: add formatting/strip helpers, refactor `_auto_present_*` to thin-flavor + code body + code footer, code-first NAME/RACE/CLASS, gate `_llm_loop`, roster assert on finalize, fix resume step restore.

## Files

- `app/gm/creation.py` — tables, status, strip, equipment summary, races/classes tables
- `app/gm/orchestrator.py` — presentation pattern, gates, finalize, resume
- `tmp/app-character-creation-spec.md`
- `tmp/app-llm-orchestrator-spec.md`

## Tests

| Command | Expected |
|---------|----------|
| `pytest play/tomb_gm/tests/test_creation_gating.py -q` | 12 pass |
| `py_compile app/gm/creation.py app/gm/orchestrator.py` | clean |
