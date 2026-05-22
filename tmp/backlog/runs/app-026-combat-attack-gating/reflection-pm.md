# Reflection: PM — APP-026 spec

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-combat-play-spec.md` § APP-026, ticket Expected files fix, `reflection-pm.md`

## Completed

- Wrote run-local `spec.md` with R1–R5, wire points for `_gate_pc_attack`, `combat_attack`, and `combat_action` ATTACK.
- Added domain spec § **Combat attack gating (APP-026)** with helper contract, wire table, APP-028 interaction, tests G1–G7, file map, changelog.
- Fixed ticket Expected files: `app/gm/tools` → `app/gm/tools.py` (optional) + `app/tests/test_combat_attack_gating.py`.
- Mapped ticket AC to requirements and test IDs; scoped turn enforcement as non-goal (existing owners).

## Self-critique

- **Error string split:** `_execute_combat_action` today returns `"no active combat"` while gate spec uses engine `"no active combat for session"`. Documented as acceptable defense-in-depth; Dev may unify — QA should confirm player-visible prefix is still clear.
- **Initiative vs defeated combatants:** Gate checks initiative ids only; a defeated PC might still appear in initiative until engine prunes — edge case deferred to engine post-gate.
- **G7 regression:** Spec allows mock gate or mock bridge for T4 compatibility — Dev should pick one approach and keep `test_combat_failure_narration.py` green without duplicating entire T4 in G7 if parametrized import suffices.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap false
- [x] Code paths from research brief
- [x] Tests mapped to AC
- [ ] Whether `_resolve_combatant_id` should be imported from engine vs duplicated in orchestrator — left to Dev plan (avoid cross-tree import if policy forbids)
- [ ] Human playtest cases — hints only; QA owns `human-test-plan.md` at Stage 7

## Handoff

**Ready for:** QA spec review (adversarial gate)  
**Escalate human if:** Product wants to **remove** exploration `combat_attack` from `TOOLS` entirely — stronger than ticket AC; currently listed as non-goal.
