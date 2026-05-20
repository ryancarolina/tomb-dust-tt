# APP-068: NAME advance must present race table same turn

| Field | Value |
|-------|-------|
| **ID** | APP-068 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

After a valid NAME choice, the player sometimes receives only “The clerk waits.” with no race table on the same turn, despite `creation_advanced` logging `NAME` → `RACE`.

## Evidence (session log)

- `16:44:25` — input `Caddy` → `creation_advanced` `NAME`→`RACE` → `gm_narration`: **“The clerk waits.”** (no `format_races_table()`, no LLM flavor request in log).
- Next input repeats `Caddy` at RACE step before lineage is resolved.

## Acceptance criteria

- [x] `_handle_creation_response` / `_chain_after_creation_choice` after NAME always returns `_auto_present_race()` body (code race table + footer) on the same turn.
- [x] Never return bare `_chain_after` fallback “The clerk waits.” when step is `RACE` and race unset.
- [x] Integration test: name input → narration contains race table header and `Awaiting: RACE_INPUT`.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_creation_flow.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Changelog entry in character-creation spec.

## Notes

**Session:** `app/logs/session-2026-05-20.jsonl` (Caddy flow).  
Suspect `_chain_after_creation_choice` default branch or empty compose path.
