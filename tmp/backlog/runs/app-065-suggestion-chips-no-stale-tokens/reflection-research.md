# Reflection: Research — APP-065 suggestion chips

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read ticket repro and acceptance criteria; traced `app/ui/app.py` `_extract_suggestions`, `_process_turn` suggestion gate, startup hardcoded chips, and `input_box.set_suggestions` / click submit path.
- Read `play/tomb_gm/suggest.py` and `bridge.suggest()` — confirmed prompts are GM/CLI context, not player chip text; no granular creation-step coverage.
- Mapped creation footers (`format_creation_status`, `_auto_finalize`), LLM system prompt bracket status line, and `strip_llm_status_tags` gaps vs combined `[…| Awaiting: …]` lines.
- Cross-referenced APP-066, APP-073 batch ordering and `CREATION_STATUS_LABELS` vocabulary.
- Set `registry_gap: false` with master-spec row citation; documented recommended fix shape and AC mapping.

## Self-critique

- Did not run manual PyGame repro or inspect Bumpy session logs (not in workspace); conclusions are code-contract based, aligned with ticket narrative.
- Exploration/combat chip policy is underspecified — flagged as PM/spec decision rather than inventing a full map.
- Did not verify whether any test already mocks `_extract_suggestions` (grep showed none).

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths: app.py, input_box.py, suggest.py, creation footers, orchestrator finalize
- [x] Tests / AC mapping
- [ ] Live session log for Bumpy repro (absent from repo)

## Handoff

**Ready for:** PM spec draft — expand `app-pygame-ui-spec.md` Input section with chip source-of-truth, blocklist, per-creation-step policy; coordinate APP-073 ordering in batch.
**Escalate human if:** Product wants rich exploration/combat chips beyond empty-default — needs playtest-driven chip catalog.
