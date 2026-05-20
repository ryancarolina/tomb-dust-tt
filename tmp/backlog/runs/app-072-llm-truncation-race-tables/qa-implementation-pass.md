# QA PASS: implementation

**Task:** APP-072-llm-truncation-race-tables  
**backlog_ticket:** APP-072  
**ticket_path:** tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md  
**Round:** 1  
**domain_spec_creation:** pending on close (draft § APP-072 present; no `APP-072 done` changelog row yet)

## Verdict

**PASS** — APP-072 acceptance criteria and run `spec.md` T1–T6 are satisfied in code and automated tests.

## Automated tests

```text
cd app && python -m pytest tests/test_creation_tables.py tests/test_creation_flow.py -q
......                                                                   [100%]
6 passed in 1.39s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_creation_tables.py` | 2 (APP-072 unit + integration) | ✓ |
| `test_creation_flow.py` | 4 (regression + APP-069 spies on same branch) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| RACE step body is **only** `format_races_table()` | `orchestrator.py` `_auto_present_race`: `body = err + format_races_table()`; integration asserts `Pick **one race**` | ✓ |
| Flavor ≤2 sentences, **no** markdown tables (prompt + post-check) | RACE instruction tightened (L801–804); global `_creation_flavor_messages` retains “Do NOT include markdown tables”; `strip_flavor_race_table` post-check in compose | ✓ |
| If flavor contains `\| Race \|` or hits token budget, strip table rows / keep prose | `creation.py` `strip_flavor_race_table` (block + line fallback); integration stub uses `finish_reason="length"` + embedded table | ✓ |
| No duplicate race tables in `gm_narration` for one turn | `test_race_narration_single_table_header`: `count("\| Race \| Adjustments \|") == 1` on NAME→RACE and invalid re-prompt | ✓ |
| Test: mock LLM embedded table does not duplicate code table | Same integration test with `_patch_llm_content(BAD_FLAVOR, finish_reason="length")` | ✓ |

## Spec T1–T6 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **T1** | Body = `err + format_races_table()` only | `_auto_present_race` L808; body never passed through sanitizer | ✓ |
| **T2** | RACE flavor prompt forbids listing races / tables | L801–804 instruction string | ✓ |
| **T3** | Block-scoped strip on flavor before compose | `creation.py` L577–599; compose L604 `strip_flavor_race_table(...)` on flavor path only | ✓ |
| **T4** | Line fallback if `\| Race \|` remains | L597: `kept = [ln for ln in kept if "\| Race \|" not in ln]` | ✓ |
| **T5** | Exactly one `\| Race \| Adjustments \|` in composed narration | Integration test primary assert | ✓ |
| **T6** | Re-prompt path uses same compose hook | Invalid race turn in integration test; `count == 1` | ✓ |

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| NAME→RACE | `_creation_turn_body` → `_auto_present_race` → `_compose_creation_narration` | Sanitizer on flavor; single code table in body |
| RACE re-prompt | `_handle_creation_response` error → `_auto_present_race(..., error=...)` | Same compose hook |
| Truncated LLM table (no separator) | Unit fixture: header + partial `\| Human \|` row | Prose retained; no `\| Race \|` |
| Full LLM table + separator + rows | Unit fixture | Leading/trailing prose retained |

**Compose order (flavor only):** `strip_llm_status_tags` → APP-070 `sanitize_premature_completion_flavor` (when active / empty roster) → `_sanitize_creation_flavor` (APP-069) → `strip_flavor_race_table` (APP-072) → append body + footer.

## Scope notes (non-blocking for APP-072 PASS)

| Item | Note |
|------|------|
| **Branch scope** | Working diff also carries APP-069 (`_narrate_creation_flavor`, committed-state block, history omission) and APP-070 (premature completion sanitizer + drift). APP-072 core deliverables are present and testable in isolation via `test_creation_tables.py`. |
| **`test_creation_flow.py`** | Edited on branch for APP-069 spy signatures + gated-step assertions — outside APP-072 plan “do not extend” note, but regression suite is green. |
| **Optional `test_format_races_table_contract`** | Not added (optional per plan). |
| **R6 debug log on strip** | Skipped (plan non-blocking). |
| **Release / drift** | Ticket still `in_progress`; domain spec has draft § APP-072 but no dated “APP-072 done” changelog — required at `release --done`. |
| **Human playtest** | Not run this round (session log replay deferred to Stage 7). |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-072 --done` (spec changelog, ticket AC checkboxes, Closed date).  
**Human playtest:** NAME→RACE — one race table block; clerk flavor 1–2 sentences without second table; optional `finish_reason: length` check in `app/logs/session-*.jsonl`.
