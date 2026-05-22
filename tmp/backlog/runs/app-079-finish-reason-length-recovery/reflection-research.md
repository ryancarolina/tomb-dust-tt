# Reflection: Research — APP-079 finish-reason-length-recovery

**Agent:** Research  
**Round:** 1  
**Deliverables:** `research-brief.md`, `reflection-research.md`

## Completed

- Read `AGENTS.md`, ticket APP-079, `tmp/app-llm-orchestrator-spec.md`, APP-083 ticket, batch board.
- Traced `_narrate_flavor`, `_llm_loop`, `_combat_llm_loop_inner`, `_compose_creation_narration`, `log_llm_response`, `_last_content`, and creation present paths in `orchestrator.py`.
- Reviewed APP-072/073 strippers in `creation.py` and existing tests that stub `finish_reason="length"`.
- Ran `tmp/analyze_session_log.py` on local `session-2026-05-20.jsonl` (28× `length`).
- Set `registry_gap: false` with master-spec justification.
- Documented APP-083 coordination risks and recommended layering in brief.

## Self-critique

- Did not read full `session-2026-05-21.jsonl` line-by-line for Sumpty repro (APP-083 cites L4743+) — relied on ticket + 2026-05-20 aggregate stats.
- Combat/exploration `length` harm is inferred from code paths more than log volume (only 3 exploration tools in 2026-05-20 log).
- Did not enumerate every `_narrate_flavor` instruction string for flavor-only vs table-body classification — PM can derive from step list in brief §A.
- Proposed “recommended PM decision” in brief is advisory; PM may choose different retry stacking.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (`_narrate_flavor`, `_llm_loop`, combat final narrate)
- [x] Tests / AC mapped to `test_llm_truncation_recovery.py` + existing stubs
- [x] APP-083 coordination called out
- [ ] Live OpenRouter `length` rate on current model (`config.yaml` model) — historical log only

## Handoff

**Ready for:** PM spec draft — add orchestrator § `finish_reason: length` recovery (per-mode table), creation spec cross-link, logging event in `app-logging-qa-spec.md`; resolve 079 vs 083 retry budget and call order with APP-083 run folder.

**Escalate human if:** Product wants 079 deferred until APP-083 Phase 1 ships (shared `narrate_with_verification` only) — batch board currently allows parallel implementation.
