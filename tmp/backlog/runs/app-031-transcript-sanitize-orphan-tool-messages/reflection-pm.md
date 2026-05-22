# Reflection: PM — APP-031 spec

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-llm-orchestrator-spec.md` (§ Transcript sanitize), `reflection-pm.md`

## Completed

- Drafted run-local [spec.md](./spec.md) with problem, goals, six requirements (R1–R6), test matrix, APP-032 boundary, and orchestrator-only wire scope.
- Updated domain spec with normative § **Transcript sanitize (APP-031)** — invariants, APP-028 reorder rule, wire points, tests, APP-031/032 pairing.
- Corrected file-map drift: sanitize lives in orchestrator, not `openrouter.py`.
- Added checklist item and changelog entry in domain spec; linked Problem section to new §.

## Self-critique

- Reorder algorithm for APP-028 system-before-tool is specified by outcome (tools immediately after assistant) but not pseudocode — Dev plan should nail edge cases (multiple assistant rounds in one array, partial tool batches).
- Optional `transcript_sanitized` logging deferred to APP-034 — acceptable for v1 but QA may want at least one test that sanitize ran when orphans present.
- Test file `test_transcript_sanitize.py` recommended but not in ticket Expected files — flagged in run spec; Dev plan should add to ticket or justify inline tests.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator.py only; no openrouter change
- [x] Domain spec / registry_gap / AGENTS.md — registry_gap false; spec updated in place
- [x] Code paths not traced — research brief covered six call sites; reflected in R4
- [x] Tests or AC not mapped — eight unit/integration cases in run + domain spec
- [x] APP-032 pairing — explicit non-goals + shared helper note
- [ ] APP-079 mid-chain interaction — noted as non-goal; Dev should confirm table-strip append still valid after sanitize

## Handoff

**Ready for:** QA spec review (round 1)  
**Escalate human if:** QA rejects APP-028 reorder as behavior change visible to model (unlikely — system text preserved)
