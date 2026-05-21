# Reflection: QA human playtest plan — APP-028

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-028  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-028, run `spec.md`, `plan.md`, `qa-implementation-pass.md`, domain spec § Combat tool failure narration, and `app/tests/test_combat_failure_narration.py` (T1–T11 contracts).
- Authored `human-test-plan.md` with eight test cases: pytest gate (TC-1), undercrypt setup (TC-2), attack-outside-combat (TC-3), unknown monster start (TC-4), **beat-trigger grave-ghoul failure** with dev file-hide repro (TC-5), `combat_end` outside combat (TC-6), in-combat invalid action (TC-7), optional `cast_spell` / `fortune_spend` (TC-8).
- Mapped ticket AC and spec R1–R6 to explicit manual steps, global pass/fail signals, and banned success-fiction substrings aligned with pytest banned lists.
- Documented dual-channel beat path (`process_beat` ok:true + player failure-only text) and canonical `[Mechanics failed — combat start: …]` / `Combat could not begin.` shape from T1/T2.

## Self-critique

- **Did not run manual playtest** — plan only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA already reported 11 green); TC-1 delegates to tester.
- **Commit hash** taken from current `HEAD` (`5135958`); Stage 7 may land a different hash — tester should use the commit containing APP-028 orchestrator changes if drifted.
- **TC-5 requires temporary monster file rename** because canon `grave-ghoul.json` exists — live beat triggers normally **succeed**. Without that step, grave-ghoul path only validates success regression (noted as optional smoke).
- TC-7 turn-timing depends on initiative order — pass/fail hinges on failure prefix + no hit fiction, not reproducing a specific turn error on first try.

## Not verified (explicit)

- [ ] Live PyGame session for any TC
- [ ] TC-5 with `grave-ghoul.json` hidden end-to-end
- [ ] TTS reads failure prefix aloud (APP-041 strip scope — not APP-028 AC)
- [ ] Partial-failure second narrate pass quality when one tool ok + one fail (T10 — unit test only)
- [ ] R8 `log_error` copy on exploration strip path (cosmetic per impl QA)
- [ ] Mixed-batch `process_beat` + `combat_attack` same turn (accepted rare edge per plan)

## Handoff

**Orchestrator:** Stage 7 — human executes `human-test-plan.md`, fills sign-off, then commit if not already done; update `status.md` Stage 7 ✅ with commit hash.

**If TC-5 fails:** Treat as P1 regression — beat short-circuit not firing; compare `_beat_combat_start_failure` / `_llm_loop` return before second `chat_completion`.

**If TC-3 fails but TC-1 passes:** Likely LLM still narrates success after prefix — check `_COMBAT_TOOL_NAMES` intersection branch in `_llm_loop` (R2 strip).

**If TC-5 passes but TC-7 fails:** Combat inner `_combat_llm_loop_inner` `all_failed` strip or wrong-tool path regression — separate from beat-trigger R1.

**Blockers from this gate:** None (plan artifact only).
