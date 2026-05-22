# Reflection: QA — playtest (APP-022)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-022 AC, run `spec.md` § Human playtest hints, domain spec § Failed set_phase(delve) hint (APP-022), `qa-implementation-pass.md` (6/6 pytest green), and `test_exploration_set_phase_delve_hint.py` (T1–T6).
- Mapped manual cases to ticket AC, spec R1–R5, and impl QA handoff (surface wrong-tool repro, recovery path, happy-path no spam, APP-024 compose overlap).
- Wrote TC-1 pytest gate plus six PyGame TCs (Breley `32-C` setup, failed `set_phase(delve)` hint, recovery, successful entry regression, APP-024 coexistence, optional ingress negative).
- Pinned exact `_delve_entry_tool_hint` core copy and compose order (failure prefix → hint → sanitized content) for human observers.
- Documented LLM variance (probabilistic `set_phase(delve)` trigger), optional R4 below-address suffix, and TC-7 as pytest-primary for non-delve failures.

## Self-critique

- Did **not** run manual PyGame — plan derived from spec, domain spec, impl QA pass, orchestrator hint strings, and APP-024 playtest patterns.
- TC-3 is **probabilistic** with live LLM — model may call **`enter_dungeon`** on first prompt; plan allows retry phrasing and collapses TC-4 into TC-5 when that happens.
- Did **not** include dedicated combat-batch R3 suppress manual case — spec Flow E; code review + impl QA only.
- Commit hash left **`pending`** — APP-022 impl may ship in batch commit APP-022/APP-026/APP-034 per batch board.
- No JSONL assertion for R1/R2 (`hint` field in tool result / system `TOOL FAILED` inject) — player-visible R3 is the manual focus; transcript checks optional in TC-3 step 6.

## Did I miss anything?

| Check | Status |
|-------|--------|
| Ticket scope / Expected files | OK — manual play only; orchestrator hint behavior |
| Domain spec § APP-022 | OK — trigger, hint text, injection R1–R3, compose order |
| Ticket AC (compass_exits + enter_dungeon on fail) | OK — TC-3, TC-1 |
| Recovery path | OK — TC-4 |
| Successful entry no hint spam | OK — TC-5 |
| APP-024 regression / overlap | OK — TC-1, TC-6 |
| Partial success no R3 banner | OK — noted; pytest T5 |
| pytest before manual | OK — TC-1 |
| Play entry `cd app && python main.py` | OK — prerequisites + TC-2 step 1 |

## Handoff

- **Ready for:** Stage 7 human execution after APP-022 commit; tick run-folder `status.md` human-test-plan checklist.
- **Escalate human if:** TC-1 passes but TC-3 never shows `compass_exits` / `enter_dungeon` after 3 deliberate `set phase delve` attempts; TC-5 shows full hint on successful entry; TC-6 shows interior success prose on surface after failed `set_phase` only (APP-024 regression).
