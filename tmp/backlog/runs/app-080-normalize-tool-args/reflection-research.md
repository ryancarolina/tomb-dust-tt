# Reflection: Research — APP-080 normalize-tool-args

**Agent:** Research
**Round:** 1
**Deliverables:** `research-brief.md`, `reflection-research.md`

## Completed

- Read ticket, domain spec draft, `AGENTS.md` / app-master registry row.
- Traced `_llm_loop`, `_combat_llm_loop_inner`, `_creation_llm_loop`, `_execute_tool`, and `json.loads` sites in `orchestrator.py`.
- Traced `bridge.remember_fact` → `semantic.remember` and `memory_recall` / APP-048.
- Compared creation **narration** sanitizers (`strip_llm_status_tags`, etc.) vs missing tool-arg layer.
- Verified Fatty/Holt failure in local `app/logs/session-2026-05-20.jsonl` (gitignored but present on disk).
- Set `registry_gap: false` with master-spec justification.

## Self-critique

- Did not enumerate every tool in `tools.py` for a full coercion matrix — ticket says v1 minimum is enough; PM may expand table.
- Combat/creation loop normalization value is asserted from code structure, not playtested.
- Did not run pytest (no `test_tool_args.py` yet) — appropriate for research-only stage.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (`_llm_loop` primary)
- [x] Tests / AC mapped to proposed `test_tool_args.py`
- [ ] Full provider raw `tool_calls` JSON at 19:51:38 — logger only stores tool names in `llm_response`; args confirmed via `tool_call` log entry only

## Handoff

**Ready for:** PM spec draft (`spec.md` in run folder) — promote orchestrator § Tool argument normalization; clarify creation/combat loop wiring and `fortune_spend` field list vs schema.

**Escalate human if:** Product requires quest memory recovery for already-played Fatty saves (out of scope — forward fix only per ticket non-goals).
