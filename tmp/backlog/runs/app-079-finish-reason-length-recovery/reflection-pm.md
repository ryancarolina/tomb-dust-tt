# Reflection: PM — APP-079 finish-reason-length-recovery

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-llm-orchestrator-spec.md` § finish_reason length recovery, `reflection-pm.md`

## Completed

- Drafted run-local [spec.md](./spec.md) with recovery matrix, helper contract, wire points, test mapping, and human playtest hints.
- Added normative § **`finish_reason: length` recovery** to [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) including APP-083 pipeline order and shared per-turn budget.
- Resolved APP-083 coordination: **discard before verify** when `body_pending`; flavor-only/terminal paths allow 079 length retry then 083 verify; single `NARRATION_LLM_MAX_ATTEMPTS` counter (default 6).
- Confirmed `registry_gap: false` — orchestrator spec is registered owner; creation spec cross-link deferred to ticket close per ticket Spec sync.
- Updated pipeline status row for PM spec stage.

## Self-critique

- **`LENGTH_RETRY_MIN_CHARS = 32`** and static fallback strings are not yet tied to existing copy in orchestrator — Dev may need step-specific fallback table; spec allows generic clerk line but NAME prompt text should be verified during plan.
- **`NARRATION_LLM_MAX_ATTEMPTS = 6`** is a PM default (1 length + 5 verify); not in config.yaml yet — Dev plan should confirm or expose in config with orchestrator spec update if changed.
- Mid-chain table strip algorithm is specified at behavior level only; Dev must avoid stripping valid tool-arg markup (research notes low risk).
- Did not edit `app-character-creation-spec.md` now — ticket says on close; QA may ask for forward pointer in creation spec during spec review.

## Did I miss anything?

- [x] Ticket scope / Expected files — spec Affected paths match ticket
- [x] Domain spec / registry_gap / AGENTS.md — orchestrator spec updated; no new domain file
- [x] Code paths not traced — research-brief traces A–E reflected in wire table; combat ~1966 called out
- [x] Tests or AC not mapped — R1–R6 + test table in spec.md
- [x] APP-083 coordination — discard-before-verify, shared budget, batch board alignment
- [ ] Logging spec — event documented in run spec + orchestrator §; `app-logging-qa-spec.md` row left for impl close (per ticket)

## Handoff

**Ready for:** QA spec review (adversarial round 1)  
**Escalate human if:** QA rejects shared budget defaults or demands creation spec cross-link before impl (PM recommends cross-link at APP-079 close only)
