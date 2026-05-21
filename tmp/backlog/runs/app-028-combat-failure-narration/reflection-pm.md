# Reflection: PM — APP-028 spec

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-combat-play-spec.md` (§ Combat tool failure narration APP-028, tests T1–T6, checklist), `reflection-pm.md`

## Completed

- Wrote run-local `spec.md`: problem/goals/non-goals, R1–R8, combat tool inventory, AC mapping, pytest + human playtest hints, `registry_gap: false`.
- Updated domain spec with durable behavior: beat-trigger (`_handle_combat_trigger`), exploration `_llm_loop` strip + TOOL FAILED retention, combat `_combat_llm_loop_inner` strip + injection, `pending_start` alignment, state truth, logging note, tests T1–T6.
- Explicitly scoped `process_beat` under R1 (not a combat tool); called out APP-026/027/030 non-goals to avoid duplicate work.

## Self-critique

- Did not re-read full `orchestrator.py` beyond research line refs — PM relied on research-brief traces for `all_failed` and `pending_start` grep.
- `cast_spell` / `fortune_spend` failure cases in combat-active exploration (if routed through `_execute_tool` combat gate) are covered by wrong-tool / combat_action paths; edge case of spell during active combat may need QA adversarial pass.
- Suggested new test file not yet added to ticket **Expected files** — Dev should extend ticket at impl if hook enforces path list.
- Session log not verified locally (gitignored).

## Did I miss anything?

- [x] Ticket scope / Expected files — `orchestrator.py` primary; test file noted for impl
- [x] Domain spec / registry_gap / AGENTS.md — combat spec owner; no new domain spec
- [x] Code paths — research paths A–F mapped to R1–R5
- [x] Tests or AC not mapped — T1–T6 + ticket AC table
- [ ] `app-llm-orchestrator-spec.md` cross-update — deferred; APP-028 already listed as open work there

## Handoff

**Ready for:** QA spec review (adversarial gate round 1)  
**Escalate human if:** QA requires mandatory `pending_start` wiring vs inline trigger failure, or wants `process_beat` engine `ok: false` as the only acceptable R1 implementation
