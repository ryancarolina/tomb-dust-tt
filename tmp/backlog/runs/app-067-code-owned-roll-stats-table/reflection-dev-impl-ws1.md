# Reflection: Dev — APP-067 WS1

**backlog_ticket:** APP-067  
**workstream:** WS1 — Roll-stats table formatter  
**date:** 2026-05-20

## What shipped

- Added `format_roll_stats_table(roll_result)` in `app/gm/creation.py` between `format_races_table` and `format_classes_table`.
- Payload-only formatter: life event intro, STR–SPI rows (Base / Genetic mod / Life Evt / Racial / Final from `final_attributes`), LUC row with em dashes in intermediate columns, HP line `10 + STA×5`.
- Markdown pipes and alignment row mirror `format_classes_table` conventions.

## Design choices

- **Final column:** always `final_attributes.get(attr, 0)` — no recomputed sums (clamp-safe per domain spec).
- **Genetic column:** `genetic_factors[attr]["mod"]` when dict-shaped (bridge production); tolerant of legacy int values in fixtures until WS2 updates `FIXED_ROLL`.
- **No orchestrator coupling:** WS1 scope excluded `orchestrator.py` and tests per workstreams.

## Verification

- Manual smoke: production-shaped dict → asserts life event line, header, STR row, LUC row, `**HP:** 60` — passed (`PYTHONPATH` includes `app` + `play`).

## Handoff to WS2

- Import `format_roll_stats_table` in `orchestrator.py`; refactor `_auto_roll_stats` to thin flavor + `format_roll_stats_table(result) + format_classes_table(eligible)`.
- Chain dedup: ROLL_STATS branch returns `_auto_roll_stats` only.
- Update `FIXED_ROLL` genetic_factors to dict shape; add integration assertions after `"human"` turn.

## Risks / notes

- Em dash `—` in LUC row matches domain spec; tests should use substring match, not ASCII hyphen.
- `×` in HP line matches spec example; integration test may use tolerant STA+60 check.
