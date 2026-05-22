# Reflection: QA — APP-075 spec review round 1

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-spec-report-1.md`

## Completed

- Read ticket APP-075, run `spec.md`, `research-brief.md`, PM/reflection artifacts, and full `tmp/app-character-creation-spec.md`.
- Independently traced `normalize_skill_slug`, `parse_player_skills`, `_handle_creation_response` SKILLS branch, and `_auto_present_skills|schools|spells` in `app/gm/creation.py` and `app/gm/orchestrator.py`.
- Ran local repro (`manacontrol` → `None`; compact collision scan on 32 skills).
- Confirmed apprentice ticket repro would pass `validate_skill_picks` once parser returns three slugs.
- Issued **FAIL** with six findings (four blockers/major, two minor).

## Self-critique

- Did not run pytest (spec stage — no implementation yet); test contracts reviewed statically only.
- Did not read `app-master-spec.md` registry row (research already tied APP-075 to character-creation spec).
- Forbidden-substring list for T2 not challenged against real session logs — may need PM tuning after flavor policy is fixed.
- `play/tomb_gm/tests/test_creation_gating.py` hook allow-list behavior assumed from backlog rules; did not invoke `impl-check` or hooks.

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 raised
- [x] Domain spec / registry_gap — SPEC-001 phantom sections
- [x] Code paths traced — parser + flavor + schools/spells
- [x] Tests / AC mapped — AC table in report
- [ ] `_auto_present_race|class|equipment` error flavor — intentionally out of ticket AC; noted in research only
- [ ] APP-059 table display vs glued paste UX — minor; not escalated
- [ ] Whether empty flavor on all `error=` paths affects APP-069 committed-state flavor block — Dev plan should confirm compose order still runs sanitizers on `""`

## Handoff

**Ready for:** PM spec revision round 2 — address SPEC-001, TICKET-001, SPEC-002 before re-dispatch QA spec round 2.

**Escalate human if:** Team insists T1 stays in `play/tomb_gm/tests/` but backlog hooks block non-Expected paths and ticket amendment is refused.
