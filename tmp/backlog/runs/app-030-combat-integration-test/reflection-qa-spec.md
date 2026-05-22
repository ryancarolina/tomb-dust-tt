# Reflection: QA — APP-030 spec (round 1)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-spec-pass.md`, `reflection-qa-spec.md`

## Completed

- Read ticket APP-030 AC, Expected files, and spec sync requirements.
- Adversarial review of run `spec.md` R1–R7, I1 step trace, optional I2/I3 stretch, and test plan commands.
- Cross-checked domain spec § Combat integration golden path (APP-030), APP-027 V4 absorption row, file map, and draft changelog.
- Verified code paths: `bridge` combat API, `is_pc_turn`, `handle_status` combat nesting, V4 skip in validation module, engine `start_combat` roster spawn, direct `combat_attack` (no auto-finalize on bridge path).
- Confirmed ticket Expected files include `app/tests/test_combat_integration.py` (no APP-027/065-style hook gap).

## Self-critique

- Did not live-run a probe fixture in pytest — relied on research brief live probe + static traces. Acceptable for spec gate; impl QA should run I1 green.
- Turn-cap flake risk (PC never reached in 5 rounds) judged low for 1× `grave-ghoul:1` but not empirically bounded — noted as Dev/impl concern, not spec blocker.
- Did not read full `spawn_roster_combatants` — inferred from step-2 PC-in-combatants assert and research.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths not traced — bridge vs orchestrator layer choice validated
- [x] Tests or AC not mapped
- [ ] Human playtest plan — out of scope for spec gate (Stage 7)

## Handoff

**Ready for:** Dev plan (PM revision not required)  
**Escalate human if:** Dev plan expands scope to I2/I3 orchestrator chain as required AC, or bridge `seed` API becomes mandatory
