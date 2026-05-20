# Reflection: APP-067 WS2 implementation

**backlog_ticket:** APP-067  
**workstream:** WS2 — Roll orchestration + tests  
**date:** 2026-05-20

## What changed

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | Import `format_roll_stats_table`; refactor `_auto_roll_stats` to thin-flavor + code tables; set `classes_table_shown` after `advance()`; ROLL_STATS chain returns roll only |
| `app/tests/test_creation_flow.py` | `FIXED_ROLL` production bridge shape; APP-067 assertions after `"human"` turn |

## `_auto_roll_stats` pattern

Aligned with `_auto_present_skills`: `roll_attributes` → store → `advance()` → `_remember_creation_step` → flavor via `_narrate_flavor` → body from `format_roll_stats_table` + `format_classes_table` → `_compose_creation_narration`. Removed `_narrate_only` JSON context path entirely.

**Flag order:** `advance()` lands on `CLASS` and resets `classes_table_shown` in `CreationState.advance()` — set `classes_table_shown = True` immediately after advance, before compose.

## Chain dedup

`_chain_after_creation_choice` ROLL_STATS branch now returns `_auto_roll_stats` only. Class table is embedded in roll response; no chained `_auto_present_class` (avoids duplicate `Pick **one tier-1 class**` and `**Final attributes:**` one-liner).

`_auto_present_class` left unchanged for Flow C (direct CLASS / resume / invalid input).

## Tests

- `FIXED_ROLL`: removed LUC from `base_rolls`; `genetic_factors` dicts with `roll`/`mod` per STR–SPI.
- After `"human"`: table header, per-attr finals, LUC row, HP 60, single class table, no `**Final attributes:**`, mock flavor present, `classes_table_shown` True.

## Verification

```text
cd app && python -m pytest tests/test_creation_flow.py -q
→ 1 passed
```

Grep: `_auto_roll_stats` has no `_narrate_only`; ROLL_STATS chain has no `_auto_present_class`.

## Out of scope (ticket release)

- `tmp/app-character-creation-spec.md` changelog + `claim_ticket.py release APP-067 --done` (plan task 5).

## Risks / notes

- Per-attr assertion uses `| {final} |` substring — could false-positive if another table shared the same final digit; acceptable for fixed fixture with distinct INT 12.
- `get_step_prompt` / `system_prompt` still mention LLM roll table (non-goal per plan).
