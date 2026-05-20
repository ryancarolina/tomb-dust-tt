# Spec: APP-003-log-creation-step-snapshot

**Status:** approved
**backlog_ticket:** APP-003
**ticket_path:** tmp/backlog/app-003-log-creation-step-snapshot-each-turn.md
**domain_spec:** tmp/app-logging-qa-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-logging-qa-spec.md

## Problem

Creation debugging relies on inferring FSM state from narration. APP-002 logs drift anomalies only when status lines disagree. Operators need a **baseline telemetry event every creation turn** to correlate step, roster, and awaiting without waiting for drift.

## Goals

- Emit `creation_step` JSONL after every `_creation_turn` completes.
- Payload: `step`, `roster_len`, `awaiting`, `creation.active` (engine + orchestrator truth).

## Non-goals

- Logging `advanced_to` transitions (APP-004)
- Post-finalize engine status dump (APP-005)
- New test package (APP-049)

## Requirements

### R1: Per-turn creation_step event

**Acceptance criteria**

- [ ] After each `_creation_turn` return path, append one `creation_step` JSONL entry.
- [ ] `data` includes: `step`, `roster_len`, `awaiting`, `creation.active`.
- [ ] `roster_len` and `awaiting` from `bridge.status()`; `step` / `creation.active` from `CreationState`.
- [ ] Domain spec event table marks `creation_step` implemented (not planned).

## Test plan

```bash
cd app && python -c "from gm.logger import log_creation_step; from gm.orchestrator import Orchestrator; assert hasattr(Orchestrator, '_log_creation_step_snapshot')"
```

Manual: new game → one creation turn → inspect `app/logs/session-*.jsonl` for `creation_step`.

## Human playtest hints (for Stage 7)

- Start new game, enter delver name, submit — verify JSONL contains `creation_step` with `step: NAME` then advancing steps.
- Continue mid-creation — snapshot reflects resumed step.

## Affected paths

- `app/gm/logger.py` — `log_creation_step`
- `app/gm/orchestrator.py` — `_log_creation_step_snapshot`, `_creation_turn` finally hook

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial draft |
