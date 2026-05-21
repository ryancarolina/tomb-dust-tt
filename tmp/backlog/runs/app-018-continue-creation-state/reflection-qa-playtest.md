# Reflection: QA human playtest plan — APP-018

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-018  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-018, run `spec.md`, `qa-implementation-pass.md`, domain spec § Creation restore (G1–G3, T-018a–f), and APP-071 variant B / APP-064 boot notes.
- Authored `human-test-plan.md` with eight test cases covering: pytest gate (TC-1), RACE relaunch + **continue** (TC-2), RACE relaunch + desk input / G3a (TC-3), SKILLS relaunch + **continue** (TC-4), in-session **load game** variant B (TC-5), post-finalize regression (TC-6), **new game** wipe / no stale restore (TC-7), APP-064 boot non-regression (TC-8).
- Mapped ticket AC and spec R2–R6 to explicit manual steps, failure signals, and optional `session_state.json` checks.
- Documented commit as **pending** (APP-018 impl QA passed; Stage 7 git commit not yet recorded in `status.md`).

## Self-critique

- **Did not run manual playtest** — plan only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA reported 67 green); TC-1 delegates to tester.
- **T-018c resume success** during mid-creation is thin on manual steps — engine roster save mid-creation is uncommon; pytest owns T-018c; noted in plan Notes.
- **T-018d legacy JSON** (no `engine_status` on disk) is not isolated in a manual TC — would require hand-editing `session_state.json`; pytest T-018d covers it.
- **G1d live-roster-only** gate (non-empty live roster, empty snapshot) not given a dedicated TC — overlaps T-018e / TC-6 post-finalize path.

## Not verified (explicit)

- [ ] Live PyGame relaunch at RACE and SKILLS with **continue** and desk input
- [ ] Variant B step phrase vs footer after restore on real LLM narration
- [ ] UI `_load_session` race with orchestrator restore (watch item only)
- [ ] Resume **success** mid-creation with living slotted save (T-018c manual)
- [ ] Legacy save file without `engine_status` field (T-018d manual)
- [ ] 60s autosave relaunch (plan uses Escape quit; autosave-only quit is equivalent but not duplicated)

## Handoff

**Orchestrator:** Stage 7 — human executes `human-test-plan.md`, fills sign-off, then git commit with APP-018 in message; update `status.md` Stage 7 ✅ with commit hash.

**If TC-2/TC-5 fail (NAME after RACE save):** P1 regression — check `_restore_creation_from_session_state` call order in `process_turn`, NAME clobber on resume success path, and `_creation_disk_restore_done` once-only guard.

**If TC-3 fails but TC-2 passes:** G3a first-turn desk routing — restore may not run before non-resume `process_turn` input.

**If TC-7 fails:** APP-015 disk wipe / `_reset_creation_for_new_game` — stale SKILLS block survived **new game**.

**Blockers from this gate:** None (plan artifact only).
