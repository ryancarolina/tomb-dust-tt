# Reflection: QA — APP-023 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, ticket AC + close, domain spec changelog, `reflection-qa-drift.md`

## Completed

- Compared `resolve_surface_address`, `_candidate_pool`, scoring helpers, `bridge.world_travel`, and `process_beat` travel branch against domain spec § Friendly surface travel resolution (APP-023) and run `spec.md` R1–R7.
- Ran `pytest play/tomb_gm/tests/test_world.py play/tomb_gm/tests/test_beat.py play/tomb_gm/tests/test_site_resolve.py` — **32 passed**.
- Updated domain spec: APP-023 checklist `[x]`, removed from open-work list, changelog **APP-023 done** (2026-05-22).
- Marked ticket AC checkbox, Status `done`, Closed 2026-05-22.

## Self-critique

- Did not run full extraction slice or app orchestrator tests — qa-implementation-pass already covered scoped suites; APP-023 is engine + bridge scoped.
- Did not update `app/gm/tools.py` `world_travel.to_address` description — ticket marks optional; spec wiring table mentions it on close; noted as non-blocking in drift-check.
- Did not run `claim_ticket.py release APP-023 --done` — out of scope for drift subagent per prior run convention.
- Did not replay PyGame human playtest (Stage 7).

## Did I miss anything?

- [x] Ticket scope / Expected files (`world.py`, `beat.py`, `bridge.py`, tests)
- [x] Domain spec / AGENTS.md drift policy
- [x] Code paths traced (two-pass resolver, compound gate, beat error map, bridge pre-resolve)
- [x] Tests mapped to AC and domain spec test table
- [ ] `tools.py` friendly-name tool description — optional; deferred
- [ ] Human playtest — deferred to Stage 7
- [ ] CLI `cmd_world.py` parity — optional per plan

## Handoff

**Ready for:** Orchestrator `release APP-023 --done`, Stage 7 commit + `human-test-plan.md`  
**Escalate human if:** Live play shows friendly travel resolving to wrong exit despite green tests, or LLM ignores `USE_ENTER_DUNGEON` and retries `world_travel` to UG ids
