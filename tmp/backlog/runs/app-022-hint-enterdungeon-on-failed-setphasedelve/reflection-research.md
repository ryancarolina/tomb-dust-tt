# Reflection: Research — APP-022 hint enter_dungeon on failed set_phase(delve)

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read ticket APP-022, domain spec `app-exploration-delve-spec.md`, orchestrator spec open-work list, dev-team research template.
- Traced `set_phase(delve)` failure from `_llm_loop` → `_execute_tool` → `bridge.set_phase` → `extraction.set_phase` (preparation rejection).
- Contrasted with `enter_dungeon` + `advance_phase_for_dungeon_entry` success path and `compass_exits` tool/context data.
- Mapped existing guidance (tools.py, system_prompt.py) vs missing orchestrator enforcement.
- Confirmed `registry_gap: false`; documented test gap and APP-024/077/028 boundaries.
- Proposed implementation loci (tool result enrich, system message, all_failed prefix) for PM spec.

## Self-critique

- Did not replay session JSONL cited in domain spec — gitignored; relied on spec problem bullets and engine test `test_set_phase_rejects_preparation_to_delve`.
- Did not run pytest or live mock-LLM turn — static read only.
- Did not deep-read `process_beat` mechanical paths that might call phase changes indirectly — out of ticket scope but could affect “failed set_phase” frequency if beat ever emits phase tools (not found in grep).
- Left open whether hint is LLM-only vs player-visible — flagged for PM; APP-024 human test suggests player-visible may be intended.

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py` only)
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths: dispatch, failure inject, all_failed banner, compass context
- [x] Tests mapped (engine yes, app none for APP-022)
- [x] Related tickets APP-024, APP-021, APP-077
- [ ] Exact hint copy and dynamic below-list inclusion — deferred to PM spec
- [ ] Whether `aftermath→delve` failure gets same hint — flagged as PM decision

## Handoff

**Ready for:** PM spec draft (`spec.md`) — define hint trigger (`set_phase` + `phase=delve` + `ok: false`), hint audience (LLM tool payload, system line, player banner), optional compass-backed below addresses, mock-LLM test AC, changelog entry in `app-exploration-delve-spec.md`.

**Escalate human if:** Product wants hints in `tools.py` / `system_prompt.py` instead of orchestrator-only — conflicts with ticket Expected files unless ticket is amended.
