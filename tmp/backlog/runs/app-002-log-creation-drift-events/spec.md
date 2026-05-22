# Spec: APP-002-log-creation-drift-events

**Status:** approved
**backlog_ticket:** APP-002
**ticket_path:** tmp/backlog/app-002-log-creationdrift-events.md
**domain_spec:** tmp/app-logging-qa-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-logging-qa-spec.md

## Problem

During character creation, GM narration sometimes includes a status line (`Phase`, `Awaiting`) that disagrees with the code-owned creation FSM and engine `status()`. This happened in production logs (empty roster + exploration-phase UI) with no structured JSONL event, making regressions hard to spot.

## Goals

- After each GM narration while creation is in scope, detect mismatch between parsed narration status fields and engine truth.
- Emit `creation_drift` JSONL with fields required by ticket AC plus parsed values for debugging.

## Non-goals

- Fixing drift automatically (APP-008+)
- Logging `creation_step` each turn (APP-003)
- UI changes (APP-036)
- New test package (APP-049) — optional inline import test only

## Requirements

### R1: Parse narration status line

**Acceptance criteria**

- [ ] Extract `Phase` and `Awaiting` from narration when bracket status line present (regex tolerant of pipe-separated format).
- [ ] If neither field present, skip drift check (no false positives).

### R2: Drift detection scope

Run check when **any** of:

- `creation.active` is True, or
- `bridge.status().awaiting == "CHARACTER_CREATION"` and `len(roster) == 0`

**Acceptance criteria**

- [ ] Check runs on all orchestrator narration emit paths via single helper (not duplicated logic).

### R3: Drift conditions

Emit `creation_drift` when **any** of:

- Parsed `Awaiting` present and ≠ engine `status.awaiting` (case-insensitive trim)
- Parsed `Phase` present and engine `party.phase` present and ≠ engine phase (case-insensitive)
- `creation.active` and parsed `Phase` is one of `delve`, `ingress`, `extract`, `aftermath` (premature exploration phase during creation)

**Acceptance criteria**

- [ ] Event payload includes: `step`, `roster_len`, `awaiting`, `creation.active` (ticket AC)
- [ ] Payload also includes: `narrated_phase`, `narrated_awaiting`, `engine_phase` when available

### R4: Logger API

**Acceptance criteria**

- [ ] `log_creation_drift(data: dict)` in `app/gm/logger.py` writes `type: creation_drift`

## Test plan

```bash
python -c "from gm.logger import log_creation_drift; log_creation_drift({'step':'NAME','roster_len':0,'awaiting':'CHARACTER_CREATION','creation.active':True})"
python -c "import re; from gm.orchestrator import Orchestrator; print(hasattr(Orchestrator,'_emit_narration'))"
```

Manual: run creation turn with mocked narration containing wrong `Awaiting:` → verify JSONL line in `app/logs/session-*.jsonl`.

## Affected paths

- `app/gm/logger.py` (ticket lists `logging.py` — corrected)
- `app/gm/orchestrator.py`

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial approved spec for APP-002 |
