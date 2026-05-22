# Reflection: PM — APP-075 skills-parse-error-flavor

**Agent:** PM
**Round:** 1
**Deliverables:** `spec.md`, `tmp/app-character-creation-spec.md` (§ Skill slug normalization, § Gated-step flavor on validation failure, § Tests APP-075, changelog draft), `status.md`

## Completed

- Wrote run-local `spec.md` with problem/goals/non-goals, requirement IDs (P1–P3, E1–E2, T1–T2), AC mapping, implementation pointers, test plan, and human playtest hints.
- Updated domain spec (registry owner, `registry_gap: false`) with normative parser resolution order including compact/glued pass, parse-error messaging priority, validation-failure flavor contract (V1–V5) for skills/schools/spells, and test contracts T1–T2.
- Echoed research conclusion: two independent bugs (parser + flavor), collision-free compact rule, schools/spells flavor aligned per ticket AC; spell-id glued parsing left non-goal.

## Self-critique

- Did not specify exact correction-only LLM prompt text — left (a) empty flavor vs (b) brief correction as implementation choice; QA may want one mandated path for deterministic tests.
- Unknown-token error wording is behavioral (“when practical”) not a fixed string — Dev must align orchestrator and parser helper.
- T2 test uses forbidden substring list that may need tuning if correction-only flavor legitimately uses words like “choices” in “invalid choices”.
- Domain spec changelog is **draft** only; ticket still requires “on close” entry when implementation lands.

## Did I miss anything?

- [x] Ticket scope / Expected files (`creation.py`, `orchestrator.py`, tests, domain spec)
- [x] `registry_gap: false` — no new `tmp/app-*-spec.md`
- [x] Research traces (normalize order, `_auto_present_*` error ignored)
- [x] Tests mapped (gating + flow; optional `test_creation_parsers.py`)
- [x] APP-011/069/070 cross-links
- [ ] `app-master-spec.md` priority table — ticket says “still accurate” on close; no change needed for PM draft
- [ ] Equipment `_auto_present_equipment` error path — intentionally out of scope per ticket AC

## Handoff

**Ready for:** QA spec review (adversarial round 1) — verify compact rule order, V1–V5 testability, and that schools/spells are in scope.

**Escalate human if:** QA wants spell-id glued parsing in APP-075 scope (research marked stretch) or mandates non-empty correction flavor vs empty flavor for all error paths.
