# Spec: APP-006-creation-hardening-006-012

**Status:** approved
**backlog_ticket:** APP-006 … APP-012
**domain_spec:** tmp/app-character-creation-spec.md
**registry_gap:** false
**Domain specs touched:** app-character-creation-spec.md, app-llm-orchestrator-spec.md

## Problem

LLM-owned tables and status lines caused creation drift (empty roster, wrong phase). Exploration tools could run during creation. Resume reset step to NAME. Finalize could succeed in narration without roster.

## Requirements (by ticket)

| Ticket | Requirement |
|--------|-------------|
| APP-006 | Code appends `format_*_table()` + `format_equipment_summary()`; kit/GP from `ensure_equipment_gold()` |
| APP-007 | `format_creation_status()` footer; strip LLM `[Location:…]` / `Awaiting:` tags |
| APP-008 | Block `_llm_loop` while `creation.active`; remove creation fallbacks into exploration |
| APP-009 | After finalize, assert `status.roster` non-empty; on failure stay in creation |
| APP-010 | Resume restores exact step from `session_state.json` creation_state |
| APP-011 | Invalid/wrong-step input re-shows table + error (incl. "Yes" at spell steps) |
| APP-012 | **Decision:** thin LLM flavor (~120 tokens) + code body + code footer until WORLD_INTRO |

## Test plan

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m py_compile app/gm/creation.py app/gm/orchestrator.py
```

## Human playtest hints

- Full apprentice creation through finalize; verify tables match code, roster populated
- Type "Yes" at spell school step — must not advance
- Mid-creation quit + continue — same step restored
- JSONL: no exploration tools during creation turns
