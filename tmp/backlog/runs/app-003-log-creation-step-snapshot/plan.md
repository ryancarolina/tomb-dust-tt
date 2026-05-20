# Implementation Plan: APP-003-log-creation-step-snapshot

**Status:** approved
**backlog_ticket:** APP-003
**ticket_path:** tmp/backlog/app-003-log-creation-step-snapshot-each-turn.md
**domain_spec:** tmp/app-logging-qa-spec.md
**Spec:** spec.md

## Approach

Add `log_creation_step` to logger (mirror `log_creation_drift`). Add `Orchestrator._log_creation_step_snapshot` that reads `bridge.status()` and logs the four AC fields. Wrap `_creation_turn` body in `try/finally` so every return path emits exactly one snapshot.

## Code-path traces (planned)

### Change: creation_step snapshot

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `logger.py:log_creation_step` | `log_entry("creation_step", data)` |
| 2 | `orchestrator.py:Orchestrator._log_creation_step_snapshot` | Build payload, call logger |
| 3 | `orchestrator.py:Orchestrator._creation_turn` | `try/finally` → snapshot in `finally` |
| 4 | `app-logging-qa-spec.md` | Mark event implemented + changelog |

## Task breakdown

1. Add `log_creation_step` to `logger.py`
2. Import + `_log_creation_step_snapshot` + `_creation_turn` finally in `orchestrator.py`
3. Update domain spec + ticket AC
4. Run import smoke test

## Files (must ⊆ ticket Expected files)

- `app/gm/logger.py`
- `app/gm/orchestrator.py`

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `cd app && python -c "from gm.logger import log_creation_step"` | exit 0 |
| 2 | `cd app && python -c "from gm.orchestrator import Orchestrator; assert '_log_creation_step_snapshot' in dir(Orchestrator)"` | exit 0 |

## Rollback / flags

None — logging only.

## Open questions

None.
