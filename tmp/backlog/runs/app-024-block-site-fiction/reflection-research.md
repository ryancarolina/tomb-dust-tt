# Reflection: Research — APP-024 block site fiction

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read AGENTS.md, ticket APP-024, domain spec `app-exploration-delve-spec.md`, orchestrator spec mechanical-truth §, dev-team templates.
- Traced `process_turn` → `_llm_loop` → `_execute_tool` for `enter_dungeon` and `site_enter`; both bridge paths and engine commit (`mode=dungeon` vs `mode=site`).
- Mapped narration emit path (`_emit_narration`) and confirmed no exploration fiction sanitizer today.
- Compared creation sanitize/drift, combat tool gate, and combat two-phase narrate patterns.
- Confirmed `registry_gap: false` — exploration-delve spec + master registry own behavior.
- Documented primary leak paths (no-tool early return, `all_failed and content`), test gap, APP-077/APP-022 relationships.

## Self-critique

- Did not replay session JSONL cited in domain spec — file gitignored / absent locally; relied on spec problem bullets and ticket notes.
- Did not run pytest or import orchestrator in REPL — static read only.
- Did not fully trace `process_beat` auto site-enter path (`test_beat.py` shows mechanical `site_enter` action) — may affect "last tool" semantics if beat bundles entry; flagged as unknown for PM.
- `site_enter` vs `enter_dungeon` prompt inconsistency noted but not deep-read `process_beat` handler in bridge.

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py` only)
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths: dispatch, narration emit, gating patterns
- [x] Tests mapped (engine yes, app none)
- [ ] `process_beat` / `advance_scene` as indirect entry — may need explicit non-goals or inclusion in gate design
- [ ] Exact regex/marker list for site-entry fiction — deferred to PM/Dev spec

## Handoff

**Ready for:** PM spec draft (`spec.md`) — define gate trigger (surface-only vs global), authorized tools (`enter_dungeon` + `site_enter`), sanitizer contract, interaction with `_llm_loop` early-return paths, mock-LLM tests, changelog entries for exploration-delve + llm-orchestrator specs.

**Escalate human if:** Product wants to deprecate `site_enter` in favor of `enter_dungeon` only — would change AC tool list and bridge surface.
