# Reflection: QA — APP-020 spec

**Agent:** QA (adversarial)
**Round:** 1
**Deliverables:** `qa-spec-pass.md`, `reflection-qa-spec.md`

## Completed

- Read ticket APP-020, run `spec.md`, domain spec § APP-020 + related APP-014/064/071 sections, `research-brief.md`, `reflection-pm.md`, live `app/README.md` (L15/L59 stale persistence claims), and `orchestrator.py` restore/`setup_new_game` paths.
- Confirmed `registry_gap: false` and `domain_spec_creation: not_needed` — session-persistence spec is the correct owner; no new `tmp/app-*-spec.md` warranted.
- Mapped ticket AC (single bullet) to D1–D7 / R-020a–g; verified checklist is manually testable without pytest.
- Checked AGENTS.md drift policy: doc-only, forbidden hand-edit/CLI paths documented, behavior pointers match closed implementation tickets.

## Self-critique

- Did not re-read full APP-018 test module or APP-014 human-test-plan TC-1 line-by-line — relied on domain spec G3a and orchestrator L833–834 trace for the APP-018 continue nuance note.
- Did not verify `app/ui/app.py` startup chip strings against live code this round — research-brief and domain § APP-064 S2/S3 were treated as authoritative (APP-064 closed).
- Adversarial pass on D5/D6 scope expansion beyond minimal ticket AC: judged acceptable README correctness within single Expected file, not a ticket gate failure.

## Did I miss anything?

- [x] Ticket scope / Expected files — impl `app/README.md` only; domain spec draft is spec-sync, not impl creep
- [x] Domain spec / registry_gap / AGENTS.md — PASS; `domain_spec_creation: not_needed`
- [x] Code paths traced — setup_new_game lifecycle + boot has_save + README stale lines confirmed
- [x] Tests or AC mapped — R-020 checklist + T-020b
- [ ] Plan-stage file ⊆ Expected files gate — not run (spec stage only)
- [ ] Implementation diff review — not run (spec stage only)

## Handoff

**Verdict:** PASS (round 1)
**Ready for:** Dev agent (plan phase) — inputs: `research-brief.md`, `spec.md`, `qa-spec-pass.md`, ticket Expected files
**Escalate human if:** Product wants APP-018 mid-creation continue documented in README (scope decision beyond stuck-recovery AC)
