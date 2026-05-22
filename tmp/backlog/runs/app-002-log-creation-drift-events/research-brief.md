# Research Brief: APP-002-log-creation-drift-events

**Date:** 2026-05-20
**Question:** Where should creation drift be detected and how do narration status lines relate to engine creation state?

**backlog_ticket:** APP-002
**ticket_path:** tmp/backlog/app-002-log-creationdrift-events.md
**domain_spec:** tmp/app-logging-qa-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) already owns `app/gm/logger.py`, JSONL event types, and lists `creation_drift` as planned. [`tmp/app-master-spec.md`](../../../app-master-spec.md) maps app-logging-qa-spec → creation_drift logging. No new domain spec required.

## Summary

Session log review (2026-05-20 Dumpy) documented UI/exploration phase diverging from in-progress character creation with no structured JSONL alert. The app logs narration via `log_gm_narration` in `app/gm/logger.py` from multiple paths in `app/gm/orchestrator.py`. Creation is code-driven (`CreationState` in `app/gm/creation.py`); engine truth is `bridge.status()` with `awaiting=CHARACTER_CREATION` when roster is empty. GM prompts require a bracket status line with `Phase:` and `Awaiting:` (`app/gm/system_prompt.py`). Drift detection should parse those fields from outgoing narration and compare to engine `creation.step`, `creation.active`, `status.awaiting`, `party.phase`, and `len(roster)` when creation is active or awaiting character creation.

Ticket **Expected files** lists `app/gm/logging.py` — that path does not exist; implementation target is `app/gm/logger.py` (per domain spec file map).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| JSONL logger | `app/gm/logger.py` | `log_entry`, `log_gm_narration` |
| Turn loop | `app/gm/orchestrator.py` | `_creation_turn`, `process_turn`, `log_gm_narration` ×6 |
| Creation FSM | `app/gm/creation.py` | `CreationState.step`, `active`, `to_dict()` |
| Engine status | `app/gm/bridge.py` → `play/tomb_gm/cli/cmd_core.py` | `awaiting=CHARACTER_CREATION` when no roster |
| Prompt contract | `app/gm/system_prompt.py` | Status line format with Phase/Awaiting |
| UI phase badge | `app/ui/panels/stats.py` | Reads `party.phase` from engine on refresh |

## Code-path traces

### GM narration → JSONL

1. Entry: `Orchestrator.process_turn` / `_creation_turn` / `_combat_turn`
2. Narration produced (LLM or deterministic string)
3. `log_gm_narration(narration)` → `logger.log_entry("gm_narration", …)`
4. **Gap:** no post-narration drift check today

### Creation-active engine truth

1. `setup_new_game` → `CreationState(active=True, step="NAME")`
2. `_creation_turn` runs while `self.creation.active`
3. `_sync_creation_from_status`: if `awaiting==CHARACTER_CREATION` and no characters → `creation.active=True`
4. `bridge.status()` → `awaiting`, `roster`, `party.phase` from `cmd_core.session_status`

### Known failure mode (spec)

- LLM emits `Phase: delve` or `Awaiting: PLAYER_ACTIONS` while `creation.step` still `NAME` / `SKILLS`
- UI stats panel shows `party.phase` (often `preparation`) but player believes they are in delve

## Existing specs & docs

- Ticket domain spec: `tmp/app-logging-qa-spec.md` — `creation_drift` row marked **(planned)**
- Parent: `tmp/app-master-spec.md` — logging QA owns drift events
- Known issue table cites Dumpy session

## Tests & commands

```bash
# No app/tests package yet (APP-049). Manual smoke after implement:
cd app && python -c "from gm.logger import log_creation_drift; ..."
# Import check:
python -c "from gm.orchestrator import Orchestrator"
```

## Risks & unknowns

- Narration may omit status line → no drift log (acceptable; only detect when line present)
- Ticket wording "phase != creation.step" — interpret per domain spec (Phase/Awaiting vs engine, not literal string match to step name)
- `logging.py` typo in ticket Expected files — use `logger.py`

## Raw notes

- `log_gm_narration` call sites in orchestrator: ~400, 501, 330, 1125, 1145, 1156
- Finalize narrate prompt hardcodes `Phase: preparation` at `orchestrator.py:805`
- CREATION_STEPS in `creation.py`: NAME → … → FINALIZE → WORLD_INTRO
