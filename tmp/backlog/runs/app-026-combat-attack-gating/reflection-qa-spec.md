# Reflection: QA — APP-026 spec review round 1

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-spec-report-1.md`, `reflection-qa-spec.md`

## Completed

- Read ticket AC, run `spec.md`, domain spec § APP-026, research brief, PM reflection.
- Traced orchestrator dispatch (`_execute_tool` / `_execute_combat_action`), engine `execute_combat_action` normalization, APP-028 T4 parametrized test.
- Mapped ticket AC to requirements/tests; checked Expected files vs affected paths and registry_gap.
- Wrote adversarial round-1 report with one blocker (ATTACK case sensitivity).

## Self-critique

- Did not run pytest (pre-implementation spec gate — correct for this stage).
- G7 “re-run T4” left vague in spec — noted as acceptable in PM reflection; did not elevate to finding since regression command is listed.
- Error-string duality (`no active combat` vs `for session`) flagged minor only; gate-first order should satisfy AC if Dev follows R3.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths from research brief
- [x] Tests mapped to AC
- [ ] Whether duplicating `_resolve_combatant_id` in orchestrator vs shared helper should be spec-mandated — left to Dev plan (PM flagged)
- [ ] Cross-ticket batch deps (APP-022/034) — out of spec gate scope

## Handoff

**Verdict:** FAIL (1 blocker, 3 minor)  
**Ready for:** PM spec revision (round 2) — fix SPEC-001, optionally clarify G5/G6b  
**Escalate human if:** Product wants exploration `combat_attack` removed from TOOLS (PM non-goal; stronger than AC)
