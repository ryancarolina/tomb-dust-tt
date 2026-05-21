# Dev implementation reflection — APP-028

**Ticket:** APP-028 combat tool failure narration  
**Run folder:** `tmp/backlog/runs/app-028-combat-failure-narration/`  
**Date:** 2026-05-21

## Summary

Implemented R1–R4 and R8 in `app/gm/orchestrator.py` plus T1–T11 in a new test module. Combat and exploration tool failures no longer append LLM success fiction when mechanics fail.

## Changes made

### R1 — Beat-trigger propagation
- Added `_beat_combat_start_failure: str | None` on `Orchestrator.__init__`; reset at `_llm_loop` depth 0.
- `_handle_combat_trigger` now returns `str | None`; on `start_combat_from_trigger` failure sets `combat.active = False` and returns canonical two-line copy (`combat start` label).
- `_execute_tool("process_beat")` stores failure string on instance flag.
- `_llm_loop` short-circuits after tool batch when flag set — no content append, no depth+1 recurse.

### R2 — Exploration `all_failed` strip
- `_llm_loop` `all_failed and content` path returns `[Mechanics failed — …]` prefix only.
- Per-tool `TOOL FAILED` system injection unchanged for partial-failure / retry turns.
- Note: file had newer APP-024 exploration-gate composition on this path; replaced with strip per spec.

### R3/R4 — Combat inner loop
- `_combat_llm_loop_inner` injects `TOOL FAILED ({fn_name})` system message before tool result on `ok: false`.
- `all_failed` returns prefix only (fallback `\n\nYour action did not resolve.` when failures list empty).

### R8 — Logging
- `log_error("llm_loop", …)` on beat short-circuit and exploration content strip.
- `log_error("combat_llm_loop", …)` on combat inner content strip.

## Tests

| ID | Status | Notes |
|----|--------|-------|
| T1 | PASS | Direct `_handle_combat_trigger`; asserts no `run_combat_monster_turns` |
| T2 | PASS | E2E `_llm_loop` beat path; single `chat_completion`; no ghoul fiction |
| T3–T7 | PASS | Parametrized exploration tools; banned substrings absent |
| T8 | PASS | Combat inner all-failed strips hit fiction |
| T9 | PASS | Wrong tool name in combat inner loop |
| T10 | PASS | Partial failure: `TOOL FAILED` before matching tool message |
| T11 | PASS | `log_error` spy on beat-failure path |

**Command:** `python -m pytest app/tests/test_combat_failure_narration.py -v` → **11 passed**

## Deviations / notes

- No DRY helper for failure prefix formatting — inline join matched existing style.
- Domain spec changelog deferred to ticket close per plan.
- `_handle_combat_trigger` success path unchanged; `pending_start` branch untouched (Flow D).

## Verification checklist

- [x] R1: failed start never calls `run_combat_monster_turns()`
- [x] R1: player sees canonical failure same turn as `process_beat`
- [x] R2/R3: no `\n\n{assistant content}` on `all_failed`
- [x] R4: `TOOL FAILED` before tool result on partial combat failure
- [x] T1–T11 green
- [ ] `tmp/app-combat-play-spec.md` checklist + changelog on `release --done` (out of impl scope)

## Risks / follow-ups

- Same-batch `process_beat` + other tool in one LLM response may still run other tools before R1 short-circuit — accepted per plan.
- Engine regression suite not run in this pass (`play/tomb_gm/tests/test_combat*.py`).
