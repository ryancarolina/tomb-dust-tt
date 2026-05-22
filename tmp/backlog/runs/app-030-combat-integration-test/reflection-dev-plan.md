# Reflection: Dev plan — APP-030

**Agent:** Dev  
**Round:** 1  
**Deliverables:** [plan.md](./plan.md)

## Completed

- Traced bridge golden path A (`start_combat` → `run_combat_monster_turns` → `combat_attack` → `combat_end`) with line anchors in `bridge.py` L244–324 and engine `run_monster_turns_until_pc_or_end` L834–864.
- Locked fixture contract: salt-road session + `character_create(name, background="militia")` with explicit `{ok}` assert before combat — addresses QA adversarial note 1 and roster requirement from research.
- Planned `_advance_to_pc_turn` loop using `is_pc_turn` + capped iterations with distinct fail messages for combat-ended vs cap-exceeded (QA note 4).
- Mapped R5 combatant resolution by `kind` and `grave-ghoul` id prefix — no hardcoded PC id.
- Specified V4 deletion (not merge/re-enable skip) and regression commands for APP-026/027/028 modules.
- Confirmed test-only scope: no `app/gm/` production edits; domain spec sync deferred to ticket close per Expected files.

## Self-critique

- **Attacker id resolution** in the sketch prefers `turn_id` when PC turn — correct for initiative; fallback to first PC combatant is defensive if `turn_id` shape drifts.
- **Single `run_combat_monster_turns` per loop iteration** may be redundant internally (engine already loops to PC) — outer cap still satisfies R4 and handles edge cases without flaking.
- **DRY duplication** of `_ensure_salt_road_session` vs validation module accepted v1 per QA note 5; documented optional follow-up only.
- **Post-attack active combat assert** added in plan as optional strengthener — not in ticket AC but catches silent finalize regressions QA flagged for direct `combat_attack`.

## Did I miss anything?

- [x] Ticket scope / Expected files — plan ⊆ integration module, V4 removal, domain spec on close
- [x] Domain spec / registry_gap / AGENTS.md — test-only; behavior already in § Combat integration golden path
- [x] Code paths traced — Flows A–D; contrast table vs APP-026/027/028 and engine tests
- [x] Tests or AC mapped — I1 + regression matrix; V4 absorption explicit
- [x] QA spec adversarial notes — roster assert, militia without skill_ids, combatant resolution, fail messages
- [x] Non-goals — I2/I3, LLM, auto-chain, seed API explicitly out of scope

## Handoff

**Ready for:** QA plan gate (Stage 4) → workstreams / implementation  
**Escalate human if:** I1 flakes on initiative in CI despite cap (would need bridge `seed` enhancement — new ticket) or `character_create` roster_set silently fails in environment (investigate bridge L537–538 swallow)
