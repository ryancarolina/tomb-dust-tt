# Reflection: Dev impl WS3 — APP-080

**Date:** 2026-05-21  
**Stream:** WS3 — Unit + integration tests  
**Agent:** Dev  
**Files:** `app/tests/test_tool_args.py` (new)

## What shipped

- Full plan test matrix in `app/tests/test_tool_args.py` (15 tests).
- Holt session fixtures: `HOLT_CORRUPTED_IMPORTANCE`, `HOLT_REMEMBER_FACT_ARGS` (ticket-shaped markup bleed, no gitignored JSONL).
- Helper unit tests import `_coerce_int`, `_strip_tool_markup` from `gm.tool_args`.
- Normalize + validate unit coverage for all plan rows (remember_fact, memory_recall precedence, fortune_spend whitelist, enter_dungeon alias, clock_tick).
- `semantic.remember` in-memory sqlite test proves coerced `importance` avoids `TypeError` on clamp.
- Integration: `_dispatch_like_llm_loop` applies normalize → validate → `_execute_tool` (documents post-WS2 loop contract before orchestrator wire).

## Test adjustments vs plan wording

| Item | Resolution |
|------|------------|
| `test_strip_tool_markup_truncates_invoke_tail` | Plan example used `4</importance>…` but markers cut at `</invoke>` / `<invoke`, not `</importance>`. Test uses `keep</invoke>…` so assert proves invoke-tail removal. |
| Integration `_execute_tool` | `setup_new_game()` leaves `creation.active=True`; test sets `creation.active=False` and `combat.active=False` (same pattern as `test_combat_failure_narration.exploration_ready`) so `remember_fact` is allowed. |
| Raw args to `_execute_tool` | WS2 not wired yet; `_dispatch_like_llm_loop` helper mirrors the three-loop pattern WS2 will inline. |

## Pytest results

```text
cd app && python -m pytest tests/test_tool_args.py -v
15 passed in 0.60s
```

## Out of scope (WS2)

- `orchestrator.py` normalize/validate at `json.loads` sites.
- Remove ad-hoc `enter_dungeon` `site_id` rewrite in `_execute_tool`.
- Full `app/tests/` regression gate.

## Risks / notes for WS2

- Integration test already green via `_dispatch_like_llm_loop`; WS2 should make production loops identical (no test change required if pattern matches).
- `log_tool_call` post-normalize args — document on spec close.
- Optional validate rows for `enter_dungeon` / `clock_tick` deferred (plan optional).

## Done when (WS3 gate)

```bash
cd app && python -m pytest tests/test_tool_args.py -q
```

Met — WS2 may proceed.
