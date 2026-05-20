# Reflection: PM — APP-057 test-creation-flow (revision 2)

**Agent:** PM  
**Round:** 2 (spec revision — QA round 1 FAIL remediation)  
**Input:** `qa-spec-report-1.md` (SPEC-001, SPEC-002, SCOPE-001, SPEC-003)  
**Deliverables:** `spec.md` (r2), `tmp/app-character-creation-spec.md`, `tmp/backlog/app-057-test-creation-flow.md`, this file

## PM decisions

| Finding | Decision |
|---------|----------|
| SCOPE-001 | **Expand APP-057 scope** — minimal `orchestrator.py` + `creation.py` fixes in scope; no split ticket unless human blocks |
| SPEC-001 | Require `races_table_shown` / `classes_table_shown` gating (mirror SKILLS) — documented in domain spec + R6 |
| SPEC-002 | Require chain NAME→RACE and ROLL_STATS→CLASS; 8-turn input table updated with per-turn step + chain contract |
| SPEC-003 | R1: `orchestrator` fixture only (transitive `mock_openrouter_client`); forbid module-level `Orchestrator` import |

## Scope expansion summary

**Before (r1):** Test-only ticket — `test_creation_flow.py` + optional `conftest.py`; non-goals excluded orchestrator/creation behavior changes.

**After (r2):** Integration test **plus** minimal creation routing fixes so the canonical Apprentice path reaches `_auto_finalize` with a non-empty roster. Rationale: ticket intent is “guard creation drift regressions”; an E2E test that cannot run on current code fails that intent.

**In scope (minimal):**

- `CreationState`: `races_table_shown`, `classes_table_shown` (+ `to_dict` / `from_dict` / advance reset)
- `orchestrator.py`: `_creation_turn_body` gate conditions; set flags in `_auto_present_*`; `_chain_after_creation_choice` for RACE and CLASS; `_execute_creation_choice` table-shown guards

**Still out of scope:** Militia spell-skip test, JSONL drift logs, resume, APP-059 table polish, `_auto_roll_stats` LLM prompt rewrite (only ensure class table is code-chained).

## Expected files (ticket)

| File | Role |
|------|------|
| `app/tests/test_creation_flow.py` | New integration test |
| `app/gm/orchestrator.py` | RACE/CLASS gating, chain handlers, execute guards |
| `app/gm/creation.py` | `CreationState` `*_table_shown` flags |
| `app/tests/conftest.py` | Only if shared fixture needed (default: unchanged) |

## Files updated

- `tmp/backlog/runs/app-057-test-creation-flow/spec.md` — R6, revised R1/R3 turn table, non-goals, affected paths, changelog
- `tmp/app-character-creation-spec.md` — § Table-shown gating, integration test turn table, fixture discipline
- `tmp/backlog/app-057-test-creation-flow.md` — Expected files list

## Handoff

**Ready for:** QA spec re-review (round 2) — focus: R6 achievability, turn table vs chain, Expected files vs ticket, R1 import rule  
**Escalate human if:** QA insists on splitting orchestrator fixes to a prerequisite ticket despite PM scope expansion
