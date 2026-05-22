# Reflection: QA — APP-027 spec (round 1)

**Agent:** QA (adversarial spec review)  
**Round:** 1  
**Deliverables:** `qa-spec-report-1.md`, `reflection-qa-spec.md`

## Completed

- Read ticket APP-027, run `spec.md`, domain spec § APP-027, research brief, PM/research reflections.
- Verified registry_gap false against `app-combat-play-spec.md` + `app-master-spec.md` combat row.
- Traced code paths: engine `load_monster_json`, bridge `start_combat`, orchestrator `_llm_loop` vs `_execute_tool`, APP-028 failure narration tests.
- Mapped ticket AC to R1–R6 / V1–V9; compared Expected files to APP-026/APP-028 precedent.
- Wrote **FAIL** report with two blockers (TICKET-001, SPEC-001) and three minors.

## Self-critique

- Did not run pytest suites — relied on file reads and grep; implementation QA should confirm baselines green.
- V4 happy-path deferral to APP-030 accepted without reading APP-030 ticket — acceptable because ticket AC does not require success path.
- Did not verify backlog hook script line-by-line for `app/tests/` denial — inferred from `tomb-dust-backlog.mdc` Expected-files rule and sibling ticket pattern.

## Did I miss anything?

- [x] Ticket scope / Expected files — **TICKET-001** flagged
- [x] Domain spec / registry_gap / AGENTS.md — PASS draft sync; no registry gap
- [x] Code paths not traced — beat `pending_start`, CLI, mixed-tool non-goals covered in research; not re-traced
- [x] Tests or AC not mapped — **SPEC-001** V5 wire gap; V8/V9 ambiguity noted
- [ ] Hook script exact allow-list — assumed from rules; orchestrator can confirm if disputed

## Handoff

**Ready for:** PM spec revision (round 2) — fix blockers, then QA spec re-review  
**Escalate human if:** PM prefers validation inside `_execute_tool` instead of `_llm_loop` — would need explicit architectural decision and APP-080 alignment note
