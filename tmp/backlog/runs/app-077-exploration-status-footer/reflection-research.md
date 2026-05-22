# Reflection: Research — APP-077 exploration status footer

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read ticket AC, domain spec APP-024 compose-order notes, and orchestrator spec APP-077 cross-refs.
- Traced `process_turn` → `_llm_loop` → `_compose_exploration_narration` → `_emit_narration` for exploration; confirmed compose stub is APP-024-only despite APP-077 docstring.
- Traced `_combat_turn` / `_combat_llm_loop_inner` — no compose on success paths; identified all `_emit_narration` exits needing combat wiring.
- Mapped creation template: `strip_llm_status_tags`, `_compose_creation_narration`, `format_creation_status`, `_auto_finalize` bracket footer reference.
- Documented `bridge.status()` / `handle_status` fields for proposed footer mapping (Location, Phase, HP, Fortune, GP, Awaiting, combat block).
- Reviewed `system_prompt.py` status-line mandate, `_check_creation_drift` creation-only scope, APP-065 engine-sourced chips.
- Set `registry_gap: false` with master-spec row citation; mapped AC → test loci and risks (GP ambiguity, double-compose, strip gaps).

## Self-critique

- Did not inspect live session log (`app/logs/session-2026-05-22.jsonl` absent from workspace); wrong-GP and meta-leak evidence is ticket-cited only.
- GP mapping left as PM decision (`goldGp` vs `gold_in_transit`) rather than inferring from engine docs — correct deferral but footer golden fixture needs spec pin.
- Did not enumerate every `_emit_narration` call site outside exploration/combat (recovery paths use code-owned `[Awaiting: new game]` — out of ticket scope but noted briefly).

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths: `_llm_loop`, `_combat_llm_loop_inner`, `_compose_exploration_narration`, creation strip/footer, `bridge.status()`, `system_prompt.py`
- [x] Tests / AC mapping
- [x] APP-024 / APP-087 / APP-041 coordination
- [ ] Session log verification (file not in repo)

## Handoff

**Ready for:** PM spec draft — add § Code-owned status footer (exploration/combat) to `app-exploration-delve-spec.md`; pin footer field mapping (especially GP), combat footer subset, compose idempotency, and prompt contract change; cross-link compose pipeline in `app-llm-orchestrator-spec.md`.

**Escalate human if:** Product wants full bracket line spoken by TTS (conflicts with APP-041 strip) or multi-character HP aggregation in footer.
