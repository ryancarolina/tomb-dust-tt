# Pipeline: APP-080-normalize-tool-args

**Goal:** Normalize/coerce LLM tool args before bridge dispatch (remember_fact importance corruption fix).
**Backlog ticket:** [APP-080](../../app-080-normalize-tool-args-before-dispatch.md)
**Domain spec:** [app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)
**Run folder:** tmp/backlog/runs/app-080-normalize-tool-args/
**Batch board:** [batch-board-APP-024-APP-028-APP-080.md](../batch-board-APP-024-APP-028-APP-080.md)
**Started:** 2026-05-21
**Current stage:** drift check PASS → ready for release + commit

## Checklist

- [x] Stage 0 — ticket claimed (`tmp/.active-ticket.json`, ticket `in_progress`)
- [x] Research → research-brief.md + reflection-research.md (dispatched)
- [x] PM spec draft + reflection-pm.md (dispatched)
- [x] QA spec PASS (round 1/3) + reflection-qa-spec.md (dispatched)
- [x] Dev plan + reflection-dev-plan.md (dispatched)
- [x] QA plan PASS (round 1/3) + reflection-qa-plan.md (dispatched)
- [x] workstreams + parallel impl (each stream: reflection-dev-impl-*)
- [x] QA implementation PASS + reflection-qa-impl.md (dispatched)
- [x] Stage 6 — drift check + ticket AC/close (`reflection-qa-drift.md`, `drift-check.md`)
- [ ] `claim_ticket.py release APP-080 --done` — orchestrator
- [ ] Stage 7 — git commit (APP-080 in message; `app/` clean in diff)
- [ ] Stage 7 — human-test-plan.md (manual PyGame playtest cases)

## Blockers

_None._
