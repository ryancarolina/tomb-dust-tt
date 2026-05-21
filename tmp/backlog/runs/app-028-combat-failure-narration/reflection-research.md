# Reflection: Research — APP-028 combat failure narration

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read AGENTS.md, ticket APP-028, domain specs `app-combat-play-spec.md` and `app-llm-orchestrator-spec.md`, dev-team research-brief template.
- Traced exploration `_llm_loop`, combat `_combat_turn` / `_combat_llm_loop_inner`, `_handle_combat_trigger`, `pending_start` branch, bridge combat wrappers, and beat `combat_trigger` emission.
- Confirmed `registry_gap: false` — combat play spec + orchestrator spec cover scope; ticket Expected files ⊆ orchestrator.
- Mapped primary failure mode: silent `start_combat_from_trigger` after successful `process_beat` / `combat_trigger` with `combat: null`.
- Documented secondary leak: `all_failed` returns append assistant `content` (success fiction) in both exploration and combat LLM loops.
- Listed engine tests vs missing app-layer narration tests; noted session JSONL gitignored / absent.

## Self-critique

- Did not run pytest (environment not exercised); traces are static read + grep.
- Did not read full `orchestrator.py` (2100+ lines) — focused combat-related symbols and `process_turn` exploration exit.
- Session log `app/logs/session-2026-05-20.jsonl` not available — grave-ghoul COMBAT_START inferred from code + user context, not replayed.
- Did not trace `cast_spell` / `fortune_spend` failure narration in combat-adjacent beats — flagged as tool-inventory risk for PM.
- `pending_start` never set: confirmed via repo-wide grep; did not audit git history for removed writers.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths: trigger, LLM loops, pending_start, bridge errors
- [x] Tests / AC mapping
- [ ] `openrouter.py` transcript sanitize interaction with failed tool messages (APP-031) — out of ticket scope but may affect retry behavior
- [ ] UI/TTS strip of `[Mechanics failed — …]` — not researched; ticket is orchestrator-only

## Handoff

**Ready for:** PM run-local `spec.md` — define deterministic failure narration for: (1) `_handle_combat_trigger` start failure, (2) exploration/combat `all_failed` content stripping, (3) enumerated combat tools + `process_beat` trigger contract; align with APP-027/APP-026 boundaries.

**Escalate human if:** Product wants beat layer to return `ok: false` when combat start fails (engine change) vs app-only narration fix — research assumes app/orchestrator fix first per Expected files.
