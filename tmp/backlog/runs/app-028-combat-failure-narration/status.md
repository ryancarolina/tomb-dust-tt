# Pipeline: APP-028-combat-failure-narration

**Goal:** Enforce failure narration when combat tools return ok:false (no success fiction on COMBAT_START with combat:null).
**Backlog ticket:** [APP-028](../../app-028-combat-tool-failure-narration.md)
**Domain spec:** [app-combat-play-spec.md](../../../app-combat-play-spec.md)
**Run folder:** tmp/backlog/runs/app-028-combat-failure-narration/
**Batch board:** [batch-board-APP-024-APP-028-APP-080.md](../batch-board-APP-024-APP-028-APP-080.md)
**Started:** 2026-05-21
**Current stage:** drift (Stage 6 complete; release pending orchestrator)

## Checklist

- [x] Stage 0 — ticket claimed (`tmp/.active-ticket.json`, ticket `in_progress`)
- [x] Research → research-brief.md + reflection-research.md (dispatched)
- [x] PM spec draft + reflection-pm.md (dispatched)
- [x] QA spec PASS (round 1/3) + reflection-qa-spec.md (dispatched)
- [x] Dev plan + reflection-dev-plan.md (dispatched)
- [x] QA plan PASS (round 1/3) + reflection-qa-plan.md (dispatched)
- [x] workstreams + parallel impl (reflection-dev-impl.md)
- [x] QA implementation PASS + reflection-qa-impl.md (dispatched)
- [x] Stage 6 — drift check (`drift-check.md`, `reflection-qa-drift.md`; ticket AC + domain spec synced)
- [ ] Stage 6 — ticket release (`claim_ticket.py release APP-028 --done`)
- [ ] Stage 7 — git commit (APP-028 in message; `app/` clean in diff)
- [x] Stage 7 — human-test-plan.md (manual PyGame playtest cases)

## Blockers

_None._
