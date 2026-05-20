# Dev Implementation Reflection: APP-074

**Ticket:** APP-074 — Remove dead `get_step_prompt()` LLM instructions  
**Date:** 2026-05-20

## What was done

- Deleted `get_step_prompt(state)` from `app/gm/creation.py` (lines 742–833, ~92 lines).
- No other files under `app/` required edits — zero callers confirmed pre- and post-delete.
- Finalized domain spec changelog row (replaced "spec draft" with "removed legacy prompt builder").
- Marked ticket AC complete and status `done`.

## Verification

| Check | Result |
|-------|--------|
| `rg "get_step_prompt" app/` | Zero matches |
| `pytest app/tests/test_creation_flow.py -q` | Pass |
| `pytest app/tests/test_creation_tables.py -q` | Pass |
| `pytest play/tomb_gm/tests/test_creation_gating.py -q` | Pass |
| Combined run | **19 passed** in 1.44s |

## Deviations from plan

None. Deletion-only chore; no orchestrator, bridge, or test edits needed.

## Risks / follow-ups

- **APP-059 backlog** still cites `get_step_prompt` as RACE problem source — optional close hygiene per plan (not impl-stage scope).
- Live creation path unchanged: `_creation_turn` → `_auto_present_*` / `format_*_table` / `_execute_creation_choice`.

## Files changed

1. `app/gm/creation.py` — removed dead function
2. `tmp/app-character-creation-spec.md` — changelog finalized
3. `tmp/backlog/app-074-remove-dead-get-step-prompt.md` — AC + status
