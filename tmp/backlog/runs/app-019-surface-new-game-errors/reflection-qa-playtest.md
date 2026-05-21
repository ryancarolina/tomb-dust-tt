# Reflection: QA — APP-019 Stage 7 human playtest plan

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-019, run `spec.md` (R0–R7, TC-A/B/C/D hints), `plan.md`, `qa-implementation-pass.md`, domain spec § New game failure (APP-019), and APP-065 / APP-014 human-test-plan examples.
- Wrote **`human-test-plan.md`** per `templates.md` § human-test-plan: prerequisites, good/bad table, dev inject block, JSONL grep (PowerShell + ripgrep), five test cases.
- **TC-0:** pytest gate mapping T-019a–f + APP-071 regression.
- **TC-A:** Context A — explicit **`new game`** failure visibility (R2): friendly lead, mapped cause, retry + relaunch hint, chips, chip retry, dual JSONL.
- **TC-B:** Context B — death restart failure (R3): corpse line preserved, no false success; pytest fallback documented when combat death impractical.
- **TC-C:** Context C — `run_ended` resume failure (R4): ended-run save setup, **`load game`** with inject, alias note for `continue`/`resume`.
- **TC-D:** R7 success regression — revert inject, NAME desk, optional death/run_ended success paths.
- AC sign-off table ties TCs to ticket AC and R1–R7; R6 optional UI documented as non-failure.

## Self-critique

- **Did not execute** manual PyGame session or live JSONL tail in this round — plan is an executable checklist for human Stage 7 post-commit.
- **Commit hash** left `pending` — impl QA PASS on disk; tester must align commit after orchestrator lands in git history.
- **Dev inject stub** is the primary failure trigger — requires temporary orchestrator edit; documented DB-lock alternative for real `database is locked` but not validated live here.
- **TC-B** may be skipped in time-boxed runs — explicit minimum bar (TC-0 + TC-A + TC-D) with pytest backstop for B/C may under-test combat caller `already_emitted` in UI (T-019c covers in automation).
- **run_ended save setup** (TC-C) depends on tester producing a 0 HP ended run — steps documented but environment-dependent.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator + tests; no required `app/ui/app.py` unless R6 follow-up
- [x] Domain spec § New game failure — contexts A/B/C, cause map, dual JSONL, forbidden success copy
- [x] Spec R1b death caller contract — TC-B JSONL asserts single narration; pytest fallback noted
- [x] Tests / AC mapped — TC-0 ↔ T-019a–f; sign-off table for R2–R4/R7
- [x] APP-071 boundary — resume-no-save called out as separate ticket
- [ ] Live verification that `clear_narration` before **`new game`** still leaves failure copy readable — human judgment in TC-A; R6 escalation path only
- [ ] Windows DB-lock alternative — documented but not step-by-step scripted

## Handoff

**Ready for:** Human tester after Stage 7 commit; update `status.md` Stage 7 checkbox; replace `pending` commit in `human-test-plan.md`.  
**Escalate human if:** TC-A shows raw `Could not start game:` despite green pytest; TC-B shows duplicate narration in JSONL; TC-D **`new game`** fails without inject (APP-014 regression).
