# Reflection: QA — APP-022 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, ticket AC + close, `reflection-qa-drift.md`

## Completed

- Compared `_delve_entry_tool_hint`, `_should_delve_entry_hint`, `_build_delve_entry_hint`, sticky `_delve_entry_hint_this_turn`, and `_llm_loop` R1–R3 against domain spec § Failed set_phase(delve) hint and run `spec.md` R1–R5.
- Ran `pytest tests/test_exploration_set_phase_delve_hint.py` + `test_exploration_site_entry_gate.py` — **13 passed**; engine phase FSM regressions — **2 passed**.
- Confirmed domain spec checklist APP-022 `[x]` and changelog **APP-022 done** (2026-05-22) already present — no domain spec edits required.
- Marked ticket AC checkbox, Status `done`, Closed 2026-05-22; updated run `status.md` Stage 6 drift complete.

## Self-critique

- Did not run full `app/tests/` or extraction slice — qa-implementation-pass already covered scoped suites.
- Did not update `tmp/app-llm-orchestrator-spec.md` open-work list (not in Expected files; noted for orchestrator on release).
- Did not run `claim_ticket.py release APP-022 --done` — out of scope for drift subagent per prior run convention.
- Did not replay PyGame human playtest (Stage 7).

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py`, `test_exploration_set_phase_delve_hint.py`)
- [x] Domain spec / AGENTS.md drift policy
- [x] Code paths traced (R1–R3, APP-024 compose order, partial success, combat early return)
- [x] Tests mapped to AC and domain spec test table
- [ ] Orchestrator spec open-work hygiene — deferred to release
- [ ] Human playtest — deferred to Stage 7
- [ ] R4 below-address suffix — no dedicated test; core hint satisfies AC

## Handoff

**Ready for:** Orchestrator `release APP-022 --done`, Stage 7 commit + `human-test-plan.md`  
**Escalate human if:** Live model ignores R2/R3 hints and retries `set_phase(delve)` repeatedly, or hint spam appears on successful `enter_dungeon` entry paths
