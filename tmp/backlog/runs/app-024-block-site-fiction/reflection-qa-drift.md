# Reflection: QA — APP-024 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, domain spec changelog/checklist, ticket AC + close, `reflection-qa-drift.md`

## Completed

- Compared `sanitize_premature_site_entry_flavor`, `_entry_committed_this_turn`, `_exploration_gate_active`, `_compose_exploration_narration`, and `_llm_loop` `all_failed` branch against domain spec § Site-entry fiction gate and run `spec.md` E1–E9.
- Ran `pytest tests/test_exploration_site_entry_gate.py -q` — **7 passed**.
- Synced domain spec: checklist APP-024 `[x]`, pinned `_SITE_ENTRY_REFUSAL_LINE` copy, changelog **APP-024 done** (2026-05-21).
- Marked ticket AC checkboxes, Status `done`, Closed 2026-05-21; updated run `status.md` Stage 6 drift complete.

## Self-critique

- Did not run full `app/tests/` or `play/tomb_gm/tests/test_extraction_slice.py` — qa-implementation-pass already ran 93-test regression slice.
- Did not replay session JSONL or PyGame human playtest (Stage 7).
- Did not run `claim_ticket.py release APP-024 --done` — out of scope for drift subagent per prior run convention.
- Did not add `mode=site` bypass integration test — gate predicate is symmetric; low risk.

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py`, `test_exploration_site_entry_gate.py`)
- [x] Domain spec / AGENTS.md drift policy
- [x] Code paths traced (sticky flag, both compose entry points, combat vs exploration `all_failed` split)
- [x] Tests mapped to AC and domain spec test table
- [ ] Human playtest — deferred to Stage 7
- [ ] E7 `premature_site_entry` telemetry — optional, deferred

## Handoff

**Ready for:** Orchestrator `release APP-024 --done`, Stage 7 commit + `human-test-plan.md`  
**Escalate human if:** Live model emits site-entry prose that bypasses marker regex (wilderness "crypt" banter, non-English entry verbs) or `party.mode=site` bypass behaves differently than `dungeon` in play
