# QA PASS: spec

**Task:** APP-068-name-advance-must-present-race-table  
**backlog_ticket:** APP-068  
**ticket_path:** tmp/backlog/app-068-name-advance-must-present-race-table.md  
**Round:** 1  
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress` (`tmp/backlog/app-068-name-advance-must-present-race-table.md`)
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md` — § NAME→RACE same-turn presentation APP-068, § Tests APP-068)
- [x] Acceptance criteria testable (run `spec.md` R1–R3; concrete assertion table in domain spec)
- [x] Code traces match repo (`orchestrator.py` NAME branch ~712–724 → `_chain_after_creation_choice("")`; RACE chain ~843–845 → `_auto_present_race`; fallthrough ~867 `return prior or "The clerk waits."`; `format_races_table()` ~544–555 in `creation.py`)
- [x] AGENTS.md / canon compliance (app/orchestrator + tests only; no `build/` mechanics drift)
- [x] Tests/commands listed (`cd app && python -m pytest tests/test_creation_flow.py -q`; human playtest hints in run spec)
- [x] registry_gap matches reality (`false` — **Character creation** row in `app-master-spec.md` owns `gm/creation.py` + orchestrator creation branch)
- [x] If registry_gap true: N/A — no § Proposed domain spec in run `spec.md` (correct)

## Ticket AC coverage

| Ticket AC | Spec / domain mapping |
|-----------|------------------------|
| After NAME, same turn returns `_auto_present_race()` body (code table + footer) | **R1**; domain spec R1 table (lines 67–67): `_auto_present_race`, `format_races_table`, `Awaiting: RACE_INPUT`, `races_table_shown = True` |
| Never bare `"The clerk waits."` when `step == RACE` and race unset | **R2**; domain spec R2 (line 68): forbid chain default; NAME must hit RACE branch or direct `_auto_present_race` |
| Integration test: name → race header + `Awaiting: RACE_INPUT` | **R3**; domain spec § Tests APP-068 (lines 230–242): intro, `\| Race \| Adjustments \| Description \|`, footer, forbidden clerk-waits, optional dedicated test |

## Scope gate

Run `spec.md` **Affected paths** ⊆ ticket **Expected files**:

- `app/gm/orchestrator.py` ✓
- `app/tests/test_creation_flow.py` ✓
- `tmp/app-character-creation-spec.md` ✓

Non-goals exclude APP-059/066, duplicate-table recovery, new domain spec — no out-of-scope paths.

## Notes

- Run `spec.md` lists R1–R3 checklists for Dev/QA traceability; **authoritative behavior** is domain spec § NAME→RACE + § Tests APP-068 (per SKILL `registry_gap: false` pointer pattern; same as APP-067).
- Root cause at `_chain_after_creation_choice` entry remains **unproven** (intermittent session log); spec correctly states observable failure + belt-and-suspenders Dev hint without mandating one fix path.
- Research brief pytest path `app/tests/...` from `cd app` is wrong; run spec / domain spec use `tests/test_creation_flow.py` — Dev should follow run spec command.
- R1 `races_table_shown` assertion extends ticket wording slightly; aligned with § Table-shown gating and `_execute_creation_choice` RACE guard — in scope.
