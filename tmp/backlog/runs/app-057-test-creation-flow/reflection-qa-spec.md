# Reflection: QA — APP-057 spec (round 1)

**Agent:** QA (adversarial)
**Round:** 1
**Deliverables:** `qa-spec-report-1.md`, `reflection-qa-spec.md`

## Completed

- Read ticket APP-057, `spec.md`, `research-brief.md`, `tmp/app-character-creation-spec.md`, `reflection-pm.md`.
- Traced `_creation_turn_body`, `_chain_after_creation_choice`, `_auto_roll_stats`, `_auto_finalize`, `cmd_core.handle_status` roster/awaiting shape.
- Validated spell/skill/school IDs against `creation.py` parsers and `play/tomb_gm/tests/test_creation_gating.py`.
- **Runtime replay** of spec 8-input sequence (isolated workspace + stub LLM + patched `roll_attributes`) — stuck at `RACE`, empty roster.
- Verdict **FAIL** (4 findings: 3 blockers + 1 major).

## Self-critique

- Runtime script used ad-hoc patch pattern first (wrong bridge swap); corrected to APP-049 GameBridge factory pattern before confirming RACE stall — initial script bug did not change conclusion.
- Did not run pytest (no `test_creation_flow.py` yet; spec review only).
- Did not read full APP-006 human-test-plan for whether manual play uses LLM tool path — code shows `_creation_llm_loop` is dead; manual play would hit same RACE/CLASS routing unless UI sends different inputs.

## Did I miss anything?

- [x] Ticket scope / Expected files — aligned
- [x] Domain spec / registry_gap false — aligned; § Integration test present
- [x] Code paths traced — RACE/CLASS routing + chain gaps
- [x] Assertions achievable — post-finalize shape OK; E2E path not OK
- [x] Spell/skill names — verified
- [ ] Whether PyGame UI bypasses orchestrator for creation — out of scope; spec targets `process_turn`

## Handoff

**Ready for:** PM spec revision round 2 (`qa-spec-report-1.md` findings)
**Escalate human if:** Product wants APP-057 test-only while keeping current RACE/CLASS routing (test will red until separate fix lands)
