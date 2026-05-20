# APP-067: Code-owned ROLL_STATS attribute table

| Field | Value |
|-------|-------|
| **ID** | APP-067 |
| **Type** | bug |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | _(set when done)_ |

## Summary

`_auto_roll_stats()` still calls `_narrate_only()` with instructions to build the attribute breakdown table. The LLM invents wrong column math that disagrees with `roll_attributes` tool output.

## Evidence (session log vs code)

- **Bumpy (human):** tool `roll_attributes` → `STR: 6`; GM table narrated `STR` final **7** with incorrect racial column (`session-2026-05-20.jsonl` ~15:39:46).
- **Code:** `_auto_roll_stats()` passes JSON to LLM and asks for “Attr | Base | Genetic | Life Evt | Racial | Final” table (`orchestrator.py` ~915–947) instead of formatting from `roll_result` in Python.
- APP-006/059 require code-owned tables; ROLL_STATS was missed.

## Acceptance criteria

- [x] Attribute breakdown table built in `creation.py` (e.g. `format_roll_stats_table(roll_result)`) from `roll_attributes` payload only.
- [x] `_auto_roll_stats()` uses thin `_narrate_flavor()` + code table + `format_classes_table(eligible)` — no `_narrate_only` stat math.
- [x] Narrated HP matches `10 + STA×5` from engine attrs shown in table.
- [x] Test asserts table cells match `roll_result` for a fixed monkeypatched roll.

## Expected files

- `app/gm/creation.py`
- `app/gm/orchestrator.py`
- `app/tests/test_creation_flow.py` or `app/tests/test_creation_tables.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add ROLL_STATS row to creation table catalog in domain spec.

## Notes

**Session:** `app/logs/session-2026-05-20.jsonl` (Bumpy human roll).  
**Related:** APP-059 (table catalog), APP-006 (deterministic tables).
