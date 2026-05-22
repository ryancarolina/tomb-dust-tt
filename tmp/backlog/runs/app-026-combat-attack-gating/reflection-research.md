# Reflection: Research — APP-026 combat attack gating

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read ticket APP-026, domain spec `app-combat-play-spec.md`, APP-028 run spec (non-goals boundary), dev-team research template.
- Traced exploration `_execute_tool` / `_llm_loop`, combat `_combat_llm_loop_inner` / `_execute_combat_action`, bridge combat wrappers, and engine `combat_attack` validation chain.
- Confirmed `registry_gap: false` — combat play spec owns behavior; Expected files ⊆ orchestrator + tools.py.
- Documented that `app/gm/tools/` is not a directory; schemas are in `app/gm/tools.py`.
- Mapped primary gap: no orchestrator pre-gate before `bridge.combat_attack`; partial gate on `combat_action` ATTACK (combat + turn_id only).
- Listed recommended shared gate helper, test matrix G1–G5, and APP-028 regression note.

## Self-critique

- Static read + grep only — did not run pytest or live LLM loop.
- Did not read full `orchestrator.py` (~2588 lines); focused combat dispatch symbols and `process_turn` routing.
- Did not trace `cast_spell` combat paths — ticket AC is attack-specific; spell gating may be APP-adjacent but out of scope.
- Initiative-vs-combatants divergence under defeat mid-round not exercised — assumed ids align per engine `roll_initiative_for_round`.
- Session JSONL from spec problem statement not replayed (gitignored / absent).

## Did I miss anything?

- [x] Ticket scope / Expected files / AC (`status.combat` + initiative)
- [x] Domain spec / registry_gap / AGENTS.md backlog rules
- [x] Code paths: exploration `combat_attack`, combat `combat_action`, engine validation
- [x] APP-028 boundary (narration vs gating)
- [x] Tests / recommended G1–G5
- [ ] Whether PM wants turn-order check in APP-026 or only combat+initiative membership — flagged for spec
- [ ] Deprecating exploration `combat_attack` tool entirely — optional PM decision, not researched for product impact

## Handoff

**Ready for:** PM run-local `spec.md` — define orchestrator `_gate_pc_attack` (or equivalent) contract: error strings, initiative id resolution, wire points (`_execute_tool` + `_execute_combat_action` ATTACK), tests G1–G5, changelog bullets for `app-combat-play-spec.md`. Clarify non-goals: monster auto-chain, APP-027 engine validation, removing tool from schema.

**Escalate human if:** Product intent is to **remove** `combat_attack` from exploration tools rather than pre-gate — stronger UX change than ticket AC wording.
