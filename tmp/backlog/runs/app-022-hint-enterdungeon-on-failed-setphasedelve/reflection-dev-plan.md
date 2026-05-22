# Reflection: Dev — APP-022 plan

**Agent:** Dev  
**Round:** 1  
**Deliverables:** `plan.md`, `reflection-dev-plan.md`

## Completed

- Read research-brief, spec.md, qa-spec-pass.md, ticket Expected files, domain spec § Failed set_phase(delve) hint (APP-022).
- Traced `_llm_loop` failure inject (`orchestrator.py` L2420–2478), `_COMBAT_TOOL_NAMES` early return, depth-0 init, APP-024 compose wiring.
- Confirmed no existing `_delve_entry_tool_hint` or APP-022 tests in repo.
- Reviewed `test_exploration_site_entry_gate.py` helpers and mock-LLM pattern for T1–T6.
- Checked `bridge.compass_exits()` return shape for R4 optional suffix (`exits.below[].address`).
- Wrote `plan.md` with six flow traces, five task sections, R1–R5 mapping, test matrix, files ⊆ Expected files.

## Self-critique

- **T6 message capture not prototyped:** Plan describes spying on `messages` list mutation but does not verify the cleanest hook (direct `_llm_loop` call vs `process_turn`). Impl should prefer minimal `_llm_loop` invocation with pre-built messages to avoid full turn side effects.
- **T4 success path setup:** Plan says "legal phase" but does not pin whether to mock `_execute_tool` returning `{ok: true}` or drive real bridge from `ingress` — mock is simpler and matches T1/T3 style; impl should stay consistent.
- **Hint prose vs domain spec markdown:** Domain spec shows bold tool names; plan recommends plain names in injects. Minor drift risk at close — align domain § Hint text to actual constant if exported, or note plain-text inject in changelog.
- **Double hint with APP-024 refusal:** Spec accepts overlap on same turn; plan does not assert ordering relative to `_SITE_ENTRY_REFUSAL_LINE` when sanitizer empties content — T2 should only assert hint + stripped markers, not refusal absence.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator + new test module only; no bridge/tools/prompt edits
- [x] Domain spec / registry_gap / AGENTS.md — hints-only; no canon/mechanics change
- [x] Code paths traced — primary fail path, negatives, partial success, combat suppress, depth guard
- [x] Tests / AC mapped — T1–T6 + regression commands; R4 optional
- [x] QA adversarial notes — depth==0 for R3, combat batch suppress, TurnTruth bypass documented
- [ ] `impl-check APP-022` — flagged open question; not run in plan phase (orchestrator read-only)

## Handoff

**Ready for:** QA plan gate (adversarial review of injection ordering, depth guard, T5/T6 test feasibility, APP-024 interaction)

**Escalate human if:** QA requires player-visible hint at depth ≥ 1 or wants hint suppressed when APP-024 refusal alone is sufficient — product choice beyond ticket AC
