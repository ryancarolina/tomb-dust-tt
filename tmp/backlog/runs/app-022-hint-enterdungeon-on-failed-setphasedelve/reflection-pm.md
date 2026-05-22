# Reflection: PM — APP-022 hint enter_dungeon on failed set_phase(delve)

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-exploration-delve-spec.md` § APP-022, ticket Expected files, `status.md` stage update

## Completed

- Drafted run-local `spec.md` with trigger (`set_phase` + `phase=delve` + `ok: false`), hint text contract, dual injection R1–R3 (tool JSON, system TOOL FAILED, player `all_failed` banner).
- Added domain spec § **Failed set_phase(delve) hint (APP-022)** with compose order vs APP-024/APP-077, test command, and changelog entry (draft, not done).
- Extended ticket **Expected files** with `app/tests/test_exploration_set_phase_delve_hint.py` (T1–T6 mapped to AC).
- Confirmed `registry_gap: false` — exploration-delve spec owns behavior; orchestrator spec is coordination only.

## Self-critique

- Hint wording is prescriptive but not pinned as a single exported constant in spec — Dev may paraphrase slightly; tests should assert substrings `compass_exits` and `enter_dungeon` rather than exact prose.
- Optional `below_addresses` suffix (R4) is specified but not required for AC pass — could be dropped in impl if bridge call adds latency; core static hint satisfies ticket.
- Did not specify whether depth-1+ retries should re-emit hint on repeated failures — assumed idempotent re-fire is OK.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator + new test file only
- [x] Domain spec / registry_gap / AGENTS.md — exploration spec updated; no app/ code edits
- [x] Code paths traced — research brief paths A/E; `_llm_loop` L2443–2478
- [x] Tests or AC not mapped — T1–T6 in spec + domain table
- [x] APP-024 / APP-028 / APP-077 boundaries documented as non-goals or compose order
- [ ] Orchestrator spec open-work list — left for drift/close (APP-022 still in_progress)

## Handoff

**Ready for:** QA spec review (adversarial PASS/FAIL on `spec.md` + domain §)  
**Escalate human if:** QA wants player-only hint (no LLM tool field) or rejects dual injection as scope creep
