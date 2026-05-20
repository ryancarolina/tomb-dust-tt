# APP-072: LLM truncation and duplicate race tables

| Field | Value |
|-------|-------|
| **ID** | APP-072 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

Race-step flavor LLM responses can hit `finish_reason: length`, truncate mid-table, and leave **two** race tables in one narration (truncated LLM table + full `format_races_table()`), confusing players and wasting panel space.

## Evidence (session log)

- `16:44:41` — `llm_response` `finish_reason: length`; narration contains cut-off Human row **and** full code `format_races_table()` appended (`session-2026-05-20.jsonl`).
- Earlier Bumpy race step: single LLM-generated 10k-char description table (no code table) — opposite failure mode.

## Acceptance criteria

- [x] RACE step body is **only** `format_races_table()`; flavor is ≤2 sentences with **no** markdown tables (enforce in `_narrate_flavor` system prompt + post-check).
- [x] If flavor response contains `| Race |` or exceeds token budget, strip table rows and keep prose only.
- [x] No duplicate race tables in `gm_narration` for one turn.
- [x] Test: mock LLM returning embedded table does not duplicate code table in final narration.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/creation.py`
- `app/tests/test_creation_tables.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Align with APP-059 race table catalog (no Description column in cells).

## Notes

**Related:** APP-059, APP-067 pattern (code-owned body).  
**Session:** Caddy flow 16:44:41.
