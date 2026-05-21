# Reflection: PM — APP-028 combat failure narration (r2)

**Agent:** PM  
**Round:** 2 (QA spec revision)  
**Deliverables:** `spec.md` (r2), `tmp/app-combat-play-spec.md`, ticket Expected files, `reflection-pm-r2.md`

## Completed

- **TICKET-001:** Extended ticket Expected files with `app/tests/test_combat_failure_narration.py` and `tmp/app-combat-play-spec.md`; run `spec.md` Affected paths aligned.
- **SPEC-001:** Named single R1 propagation contract — `_handle_combat_trigger` returns failure string → `_execute_tool` stores `_beat_combat_start_failure` → `_llm_loop` same-turn short-circuit (no silent `-> None`, no invented test-only state).
- **SPEC-002:** Test plan T3–T7 cover all five exploration combat tools (`start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend`) with per-tool banned fiction; domain spec T3–T7 mirror.
- **SPEC-003:** Added T10 / domain T10 — partial failure in `_combat_llm_loop_inner` must inject `TOOL FAILED (combat_action)` system line before tool result when loop continues.
- **SPEC-004:** Dual-channel explicit — tool-role `process_beat` may stay `ok: true`; player channel is `_llm_loop` return; T2 E2E asserts no second `chat_completion` and no ghoul fiction.
- **SPEC-005 (minor):** Optional T11 / caplog for R8 logging noted in run spec and domain spec.

## Self-critique

- Instance field name `_beat_combat_start_failure` is illustrative — Dev may rename if a return tuple from `_execute_tool` is cleaner, as long as observable contract matches.
- T10 setup (partial ok vs depth retry) left flexible — QA wanted R4 mapped, not one fixed mock shape.
- Did not update `app-llm-orchestrator-spec.md` cross-ref beyond existing open-work pointer (same defer as r1).

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 resolved
- [x] Domain spec / registry_gap / AGENTS.md — combat-play spec synced; `registry_gap: false`
- [x] Code paths — R1 contract tied to `_handle_combat_trigger` / `_llm_loop` / `_execute_tool` call chain
- [x] Tests or AC mapped — T1–T10 (+ optional T11); all five exploration tools + R4
- [x] QA round 1 blockers — TICKET-001, SPEC-001–003 addressed; SPEC-004–005 included

## Handoff

**Ready for:** QA spec re-review (round 2)

**Escalate human if:** QA requires amending `process_beat` engine `ok: false` as the only acceptable R1 fix (spec allows but does not require), or wants `pending_start` mandatory instead of short-circuit flag.
