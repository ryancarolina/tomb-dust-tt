# Dev implementation reflection — APP-067 (retry)

**Date:** 2026-05-20  
**Agent:** Dev (retry — prior subagent did not persist edits)

## What was wrong on disk

Prior run claimed success but `grep format_roll_stats_table` returned no matches in `creation.py` / `orchestrator.py`. `_auto_roll_stats` still used `_narrate_only` with JSON table instructions; `_chain_after_creation_choice` still appended `_auto_present_class` after roll.

## Changes landed

| File | Change |
|------|--------|
| `app/gm/creation.py` | Added `format_roll_stats_table(roll_result)` after `format_races_table`: life event intro, STR–SPI rows from payload, LUC row with em dashes, HP line `**HP:** {hp} (10 + STA {sta} × 5)`. |
| `app/gm/orchestrator.py` | Import formatter; `_auto_roll_stats` → `_narrate_flavor` + code body + `_compose_creation_narration`; `classes_table_shown = True`; removed `_narrate_only` stat path. Chain `ROLL_STATS` returns `_auto_roll_stats` only (no `_auto_present_class` append). |
| `app/tests/test_creation_flow.py` | `FIXED_ROLL` production shape (`genetic_factors` dicts, no LUC in `base_rolls`); APP-067 assertions after `"human"` turn. |

## Verification

```text
grep format_roll_stats_table app/gm/creation.py app/gm/orchestrator.py
  creation.py:558:def format_roll_stats_table
  orchestrator.py:24:    format_roll_stats_table,
  orchestrator.py:939:        body = format_roll_stats_table(result) + ...

cd app && python -m pytest tests/test_creation_flow.py -q
  2 passed in 0.76s
```

`_auto_roll_stats` no longer calls `_narrate_only` (grep confirms only `_auto_finalize`-adjacent and other paths retain `_narrate_only`).

## Risks / follow-up

- Spec changelog row already drafted in domain spec; release ticket with `claim_ticket.py release APP-067 --done` when batch allows.
- `get_step_prompt` / `system_prompt.py` may still mention LLM-built roll table — non-goal per plan.

## APP-068

`test_name_advance_presents_race_table` unchanged and green in same pytest run.
