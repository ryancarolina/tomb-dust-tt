# Reflection: QA — APP-014 plan (round 1)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-plan-pass.md`, `reflection-qa-plan.md`

## Completed

- Read ticket APP-014, run `plan.md`, `qa-spec-pass.md`, `spec.md`, domain spec § setup_new_game lifecycle (APP-014), and Dev `reflection-dev-plan.md`.
- Independently re-traced `setup_new_game`, `process_turn` new-game / resume `run_ended`, `_handle_player_death`, UI `_process_turn` / `_save_session`, bridge `end_session` / `force_close_all_sessions` / `wipe_all_data`, and engine `end_session` / `start_session` return shapes.
- Verified conftest fixtures and death-test pattern for T-014c feasibility.
- Wrote adversarial plan gate: **PASS** with scope metadata note for ticket Expected files.

## Self-critique

- Did **not** run pytest (plan phase; no implementation yet).
- Did **not** execute `claim_ticket.py impl-check APP-014` — orchestrator should run before Stage 4.
- Did **not** draft T-014c fixture steps — flagged as impl risk only; could have been more prescriptive in qa-plan-pass.
- Did **not** update `status.md` — orchestrator owns pipeline checklist.

## Did I miss anything?

- [x] Ticket scope / Expected files — test module gap noted; PASS with pre-impl ticket update (consistent with qa-spec-pass round 1)
- [x] L1b orchestrator requirement — verified against bridge exception-only fallback
- [x] APP-015/016/019 boundary leaks — none found in planned edits
- [ ] **Live repro** of mid-creation `new game` failure — deferred to impl QA + Stage 7 human playtest
- [ ] **Batch merge conflict** with APP-015 — documented in plan; not simulated

## Handoff

**Ready for:** Dev workstreams (WS1: orchestrator + `test_setup_new_game_lifecycle.py`) after orchestrator updates ticket Expected files and runs `impl-check APP-014`.  
**Escalate human if:** Post-wipe `campaign_new` still fails after L1–L2 (plan leaves `"already exists"` swallow unchanged) — may need product call on swallow removal.
