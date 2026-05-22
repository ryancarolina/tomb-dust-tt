# Reflection: QA human playtest plan — APP-065

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-065  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-065, run `spec.md`, `qa-implementation-pass.md`, domain spec § Suggestion chips, and `app/ui/suggestions.py` maps.
- Authored `human-test-plan.md` with seven test cases covering: pytest gate (TC-1), startup chips (TC-2), equipment player phrases (TC-3), confirm click (TC-4), objection chip (TC-5), **Bumpy stale-chip repro** (TC-6), post-finalize empty chips (TC-7).
- Mapped each ticket AC and spec R1/R2/R3 to explicit manual steps and failure signals.
- Documented acceptable narration footer drift (APP-073) vs chip-row failures.

## Self-critique

- **Did not run manual playtest** — plan only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA already reported 17 + 11 green); TC-1 delegates to tester.
- **Commit hash** taken from current `HEAD` (`83ee79e`); Stage 7 may land a different hash — tester should use the commit that contains `suggestions.py` if drifted.
- TC-3 “reach equipment” is intentionally high-level; exact prompts vary with LLM — pass/fail hinges on chip labels at kit step, not verbatim narration.

## Not verified (explicit)

- [ ] Live PyGame session for Bumpy / equipment / finalize path
- [ ] `load game` chip with real workspace save vs empty workspace
- [ ] Exception-path chip refresh beside error line (covered by unit `test_process_turn_exception_refreshes_suggestions`, not manual TC)
- [ ] `SESSION_ENDED` → `new game` chip (no dedicated TC — low risk; same SETUP builder branch)
- [ ] Chip count cap at 4 (only two equipment chips in v1)
- [ ] TTS / narration panel interaction with chip clicks

## Handoff

**Orchestrator:** Stage 7 — human executes `human-test-plan.md`, fills sign-off, then commit if not already done; update `status.md` Stage 7 ✅ with commit hash.

**If TC-6 fails:** Treat as P1 regression — stale `if suggestions:` or inactive-creation map leak; compare `app/ui/app.py` `_queue_turn_suggestions` and `get_player_suggestions()` after finalize.

**If TC-3 passes but TC-4 fails:** Likely `is_equipment_confirm` / submit string mismatch, not chip builder.

**Blockers from this gate:** None (plan artifact only).
