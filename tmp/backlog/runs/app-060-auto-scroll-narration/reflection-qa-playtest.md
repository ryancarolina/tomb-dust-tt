# Reflection: QA human playtest plan — APP-060

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-060  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-060 AC, run `spec.md` R1–R4, `qa-implementation-pass.md`, domain spec § [Narration scroll behavior](../../../app-pygame-ui-spec.md#narration-scroll-behavior-app-060), and shipped code in `app/ui/panels/narration.py` / `app/ui/app.py`.
- Authored `human-test-plan.md` with six test cases: pytest gate (TC-1), **creation tall-table submit** repro (TC-2), long GM reply (TC-3), wheel-up-then-submit always-follow (TC-4), **error tail pin** (TC-5), startup batch narration (TC-6).
- Mapped each ticket AC and spec R2/R3 rows to explicit manual steps, pass/fail signals, and bad/good visual table.
- Documented out-of-scope items (session load, resize re-pin, animated scroll) per domain spec so testers do not false-fail.
- Provided two error-provocation paths (invalid API key vs temporary `process_turn` inject) — impl QA did not run live error repro.

## Self-critique

- **Did not run manual playtest** — plan artifact only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA reported 6 + 10 green); TC-1 delegates to tester.
- **Commit hash** left pending — Stage 7 commit may land after this plan; tester should use commit containing `_follow_tail` / `test_narration_scroll.py`.
- TC-2 table height depends on LLM flavor + APP-059 formatters; pass/fail hinges on **scroll position after submit**, not exact table rows.
- TC-3 long-reply length is LLM-dependent; short replies may not stress viewport — tester may need a second prompt if first response is brief.
- TC-6 resize step is observational only (out of scope) — could confuse testers; labeled explicitly as non-failure.

## Not verified (explicit)

- [ ] Live PyGame creation-table submit without wheel
- [ ] Long exploration GM reply tail visibility
- [ ] Wheel momentum feel / scrollbar thumb accuracy under rapid scroll
- [ ] Error path with invalid key vs inject (panel visibility only in plan)
- [ ] Session **Continue** load scroll position (documented out of scope — no TC)
- [ ] Window resize mid-turn re-pin behavior
- [ ] TTS playback interaction with scroll pin (should be independent; not in scope)
- [ ] `add_lines` batch-only failure mode (unit tests cover tall table via `add_line`; startup TC-6 is manual proxy)

## Handoff

**Orchestrator:** Stage 7 — human executes `human-test-plan.md`, fills sign-off, commit if not done, update `status.md` Stage 7 ✅ with commit hash; then `release APP-060 --done` if not already released.

**If TC-2 fails (primary repro):** P1 regression — tail pin still stale; verify `draw()` applies `scroll_to_bottom()` after `_rebuild()` when `_follow_tail` is set, and queue handlers call `request_follow_tail()` not bare `scroll_to_bottom()`.

**If TC-4 fails but TC-2 passes:** Check wheel handler (`MOUSEWHEEL` → `_scroll_velocity`) or always-follow not wired on `player` path.

**If TC-5 fails only:** Inspect `error` handler in `app/ui/app.py` — must call `_smooth_scroll_to_bottom()` after `add_line`.

**Blockers from this gate:** None (plan artifact only).
