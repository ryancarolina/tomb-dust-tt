# Pipeline: APP-068-name-advance-must-present-race-table

**Goal:** After valid NAME choice, same turn must show code-owned race table (not bare "The clerk waits.")
**Backlog ticket:** [APP-068](../../app-068-name-advance-must-present-race-table.md)
**Domain spec:** [app-character-creation-spec.md](../../../app-character-creation-spec.md)
**Run folder:** tmp/backlog/runs/app-068-name-advance-must-present-race-table/
**Started:** 2026-05-20
**Current stage:** complete

## Checklist

- [x] Stage 0 — ticket claimed (`tmp/.active-ticket.json`, ticket `in_progress`)
- [x] Research → research-brief.md + reflection-research.md (dispatched)
- [x] PM spec draft + reflection-pm.md (dispatched)
- [x] QA spec PASS (round 1/3) + reflection-qa-spec.md (dispatched)
- [x] Dev plan + reflection-dev-plan.md (dispatched)
- [x] QA plan PASS (round 1/3) + reflection-qa-plan.md (dispatched)
- [x] workstreams + parallel impl (WS1 orchestrator, WS2 tests; scope fix after QA r1)
- [x] QA implementation PASS (round 2/3) + reflection-qa-impl-r2.md (dispatched)
- [x] Stage 6 — drift check + ticket release (`claim_ticket.py release APP-068 --done`)
- [x] Stage 7 — git commit (APP-068 in message; `app/` clean in diff)
- [x] Stage 7 — human-test-plan.md (manual PyGame playtest cases)

## Notes

- Code + tests landed in `e9326f1` (APP-067 bundle) before this run; APP-068 pipeline verified scope, added regression tests, closed ticket, and produced audit artifacts.

## Blockers

_None._

## Links

- Ticket: ../../app-068-name-advance-must-present-race-table.md
- research-brief.md
- spec.md
- plan.md
- human-test-plan.md
- qa-implementation-pass.md
- drift-check.md
