# Reflection: Research — APP-030 combat integration test

**Agent:** Research  
**Round:** 1  
**Deliverables:** `research-brief.md`, `reflection-research.md`

## Completed

- Read ticket APP-030, domain spec `app-combat-play-spec.md`, dev-team `templates.md`.
- Mapped all `app/tests/*combat*` modules and APP-027/028 run research briefs.
- Traced `bridge.start_combat`, `combat_attack`, `combat_end`, `combat_action`, `run_combat_monster_turns` and orchestrator `_combat_turn`, `_combat_llm_loop_inner`, `_combat_auto_chain`, `_execute_tool`.
- Ran live probes on isolated `GameBridge` for start/attack/end with and without roster PC.
- Documented V4 skip contract, fixture requirements, proposed I1–I3 test matrix, and exploration vs combat-tool guard conflict.
- Set `registry_gap: false` with master-spec + combat spec justification.

## Self-critique

- Did not run full pytest suite in research round — relied on existing green modules and targeted probes; PM/Dev should confirm no ordering flake on `run_combat_monster_turns` loop across seeds.
- Orchestrator “single integration test” wording in AC is ambiguous; recommended bridge-first I1 and optional `_execute_tool` I2 — PM must choose whether one test or two is required.
- Did not read every line of `test_combat_failure_narration.py` T8–T11 (combat inner loop) — summarized from spec + partial read; sufficient for contrast with happy path.

## Did I miss anything?

- [x] Ticket scope / Expected files (`app/tests/` only)
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (bridge + orchestrator + engine reference)
- [x] Tests and AC mapped (V4 skip, APP-028/026/027 patterns)
- [x] Live verification of golden path prerequisites (roster + monster turn advance)
- [ ] APP-025 registry hub integration patterns — skimmed grep only; out of ticket domain

## Handoff

**Ready for:** PM spec draft — define I1 (required) vs I2/I3 (optional), V4 skip removal, fixture name, and whether AC allows bridge-only or requires `_execute_tool` orchestration.  
**Escalate human if:** Product insists on one-shot LLM tool batch covering start+attack+end — current combat guard makes that impossible without spec change.
