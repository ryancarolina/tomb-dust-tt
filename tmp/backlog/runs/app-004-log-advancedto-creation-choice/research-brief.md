# Research Brief: APP-004

**backlog_ticket:** APP-004
**domain_spec:** tmp/app-logging-qa-spec.md
**registry_gap:** false

## Summary

`_execute_creation_choice` in `orchestrator.py` returns `advanced_to` but does not log it. APP-002/003 established JSONL patterns in `logger.py`. `creation.py` holds FSM helpers only — no `_execute_creation_choice` (ticket `creation.py` path unused).

## Implementation

- `log_creation_advanced` → `creation_advanced` event with `completed_step`, `advanced_to`
- Call after `self.creation.advance()` on success path only
