# Reflection: QA spec — APP-023 friendly-travel-av-grid

**Agent:** QA (adversarial)
**Round:** 1
**Deliverables:** `qa-spec-report-1.md`, `reflection-qa-spec.md`

## Completed

- Read ticket APP-023, run `spec.md`, domain spec § APP-023, `research-brief.md`, `reflection-pm.md`, dev-team QA templates.
- Verified registry_gap false against `app-master-spec.md` exploration row and PM domain updates.
- Traced code paths: `bridge.world_travel`, `beat.py` travel branch, `world.legal_exits`, `site_resolve._match_score`.
- Ran scoring proof: `kings road` → score **0** vs `33-C` displayName with documented rules; confirmed `33-C` lacks `tradeRoute` in live JSON.
- Wrote **FAIL** report with four findings (two blockers on scoring + ticket paths, one on layered algorithm, one major on error codes).

## Self-critique

- Did not exhaustively enumerate all duplicate-name exit pairs for ambiguity fixtures — T4 left to Dev/PM to pick a concrete grid cell in plan phase (acceptable if SPEC-001 fixed).
- Did not verify whether LLM prompts already emit `king's road` vs `kings road` in logs — scoring fix should not depend on LLM punctuation luck.
- `app-gamebridge-spec.md` not updated — deferred to ticket close per normal drift workflow; not raised as blocker (same as APP-022 PASS notes).

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001
- [x] Domain spec / registry_gap — PASS
- [x] Research risks — layered pass + scoring proof gaps flagged
- [x] AC testability — FAIL on primary fixture
- [ ] Live PyGame repro — not run (spec stage; human playtest Stage 7)

## Handoff

**Verdict:** FAIL (round 1)
**Report:** [qa-spec-report-1.md](./qa-spec-report-1.md)
**Ready for:** PM spec revision round 2 addressing SPEC-001, TICKET-001, SPEC-002, SPEC-003
**Escalate human if:** Product requires global name lookup despite 155 duplicate displayNames (conflicts with research + spec policy)
