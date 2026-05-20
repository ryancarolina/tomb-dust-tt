# Research Brief: APP-003-log-creation-step-snapshot

**Date:** 2026-05-20
**Question:** Where should per-turn creation telemetry be emitted, and what fields match engine truth?

**backlog_ticket:** APP-003
**ticket_path:** tmp/backlog/app-003-log-creation-step-snapshot-each-turn.md
**domain_spec:** tmp/app-logging-qa-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) owns JSONL event types including planned `creation_step`. APP-002 established `log_creation_drift` + orchestrator hooks in the same files. No new domain spec required.

## Summary

APP-003 adds unconditional per-turn creation telemetry (not drift detection). Character creation runs through `Orchestrator._creation_turn`, invoked from `process_turn` when `self.creation.active` or on new game / resume-into-creation. Each turn ends with `_emit_narration` on the happy path; early exits recurse to `process_turn("look around")`. A `try/finally` on `_creation_turn` guarantees one snapshot per creation turn including early returns. Field shape mirrors APP-002 drift payload minus narration comparison fields: `step`, `roster_len`, `awaiting`, `creation.active`. Engine truth comes from `bridge.status()`; creation step from `CreationState`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Creation turn entry | `app/gm/orchestrator.py:_creation_turn` | Single funnel for creation turns |
| Creation FSM | `app/gm/creation.py:CreationState` | `step`, `active` |
| Engine status | `app/gm/bridge.py` → `play/tomb_gm` | `awaiting`, `roster` |
| JSONL logger | `app/gm/logger.py` | Add `log_creation_step` (mirror APP-002) |
| Prior art | APP-002 `_check_creation_drift` | Same status fetch pattern |

## Code-path traces

### Creation turn lifecycle

1. Entry: `process_turn` → `_creation_turn(player_input)` when `creation.active` or new game / resume
2. Step handlers (`_auto_roll_stats`, LLM loop, `_handle_creation_response`, …) produce narration
3. Normal path: `_emit_narration` → history append → return
4. Early exit: `return self.process_turn("look around")` when creation completes
5. **Gap:** no `creation_step` JSONL today

### Status snapshot fields

1. `self.creation.step` — FSM step (NAME, RACE, …)
2. `len(status.get("roster") or [])` — engine roster count
3. `status.get("awaiting")` — e.g. `CHARACTER_CREATION`
4. `self.creation.active` — orchestrator creation flag

## Existing specs & docs

- Domain spec lists `creation_step` as **(planned)**
- APP-002 changelog: drift logging pattern in orchestrator + logger

## Tests & commands

```bash
cd app && python -c "from gm.logger import log_creation_step; from gm.orchestrator import Orchestrator; assert hasattr(Orchestrator, '_log_creation_step_snapshot')"
```

No `app/tests/` package yet (APP-049).

## Risks & unknowns

- Recursive `process_turn` from `_creation_turn` finally block logs before exploration turn — acceptable (captures transition state)
- Ticket Expected files originally only `orchestrator.py`; add `logger.py` for dedicated writer (APP-002 precedent)

## Raw notes

- `_creation_turn` lines 475–567 in `orchestrator.py`
- APP-002 drift payload at lines 204–213 uses identical core fields
