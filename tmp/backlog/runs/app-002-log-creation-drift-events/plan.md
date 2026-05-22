# Implementation Plan: APP-002-log-creation-drift-events

**Status:** approved
**backlog_ticket:** APP-002
**ticket_path:** tmp/backlog/app-002-log-creationdrift-events.md
**domain_spec:** tmp/app-logging-qa-spec.md
**Spec:** spec.md

## Approach

Add `parse_narration_status_line` and `log_creation_drift` to the logger module. Add `Orchestrator._emit_narration` that logs GM text then runs `_check_creation_drift`. Replace direct `log_gm_narration` calls in `orchestrator.py` with `_emit_narration`. Drift logic lives in orchestrator (needs `creation` + `bridge.status()`).

## Code-path traces (planned)

### Change: central narration emit

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `orchestrator.py:Orchestrator._emit_narration` | New wrapper |
| 2 | `orchestrator.py` | Replace `log_gm_narration(...)` → `self._emit_narration(...)` |
| 3 | `orchestrator.py:Orchestrator._check_creation_drift` | Parse + compare + call logger |
| 4 | `logger.py:log_creation_drift` | `log_entry("creation_drift", data)` |
| 5 | `logger.py:parse_narration_status_line` | Regex helpers (or keep parse in orchestrator) |

## Task breakdown

1. Add `log_creation_drift` to `logger.py`
2. Add parse + drift check + `_emit_narration` to `orchestrator.py`
3. Replace all `log_gm_narration` in orchestrator
4. Update `app-logging-qa-spec.md` — mark `creation_drift` implemented, changelog
5. Update ticket AC + status

## Files (must ⊆ ticket Expected files)

- `app/gm/logger.py` (corrects ticket `logging.py`)
- `app/gm/orchestrator.py`

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `python -c "from gm.logger import log_creation_drift"` | exit 0 from `app/` cwd |
| 2 | `python -c "from gm.orchestrator import Orchestrator; import inspect; assert '_emit_narration' in dir(Orchestrator)"` | exit 0 |
| 3 | Unit-style inline test for parse regex | Phase/Awaiting extracted |

## Rollback / flags

None — logging only, no behavior change to gameplay.

## Open questions

None.
