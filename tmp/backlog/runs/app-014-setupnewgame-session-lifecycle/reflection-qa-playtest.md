# Reflection: QA — APP-014 playtest plan

**Agent:** QA
**Round:** 1
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Wrote Stage 7 `human-test-plan.md` per `templates.md` § human-test-plan: prerequisites, five TCs with pass columns, sign-off, notes for follow-on tickets.
- Mapped manual cases to ticket AC (`session end → wipe → campaign → session start`), domain spec § Tests APP-014 manual hint, and pytest IDs T-014a–c where player-visible.
- **TC-1** targets the pre-fix player symptom (APP-064 partial-creation boot → **`new game`** → NAME, no setup error) — primary validation that L1/L1b run before wipe.
- **TC-2** covers in-session retry without relaunch; **TC-3** cold-start regression; **TC-4** load-game non-regression; **TC-5** optional death restart aligned with T-014c.
- Documented commit as `pending` because `orchestrator.py` + `test_setup_new_game_lifecycle.py` are not yet on git (drift-check / impl QA noted same).
- Cross-referenced APP-015 disk clear (TC-2 optional JSON check), APP-019 error surfacing, APP-018 continue scope in Notes.

## Self-critique

- **TC-5 (death)** may be skipped in practice — lethal play is slow and environment-dependent; plan defers to T-014c but human coverage of death path is thin if skipped.
- Did not run manual playtest myself (QA plan author only); steps assume APP-064 boot behavior from domain spec — not re-verified in live PyGame this round.
- Optional DB/JSONL checks help developers more than casual testers; kept optional to avoid blocking sign-off on tooling.
- TC-1 setup requires LLM-backed creation steps; flaky LLM narration could confuse "footer step" assertions — mitigated by focusing on absence of **Could not start game** as hard fail.

## Did I miss anything?

- [x] Ticket scope / Expected files — manual plan stays PyGame + player-visible; no code edits
- [x] Domain spec / registry_gap / AGENTS.md — aligned with § setup_new_game lifecycle (APP-014) and spec human hints
- [x] Code paths not traced — plan follows plan.md traces A (UI `new game`) and D/E (death / run_ended) for TC-5 wording
- [x] Tests or AC not mapped — TC-1↔T-014a, TC-5↔T-014c, TC-3↔non-regression; T-014b is engine-only (no dedicated manual TC; covered indirectly by TC-1/2)
- [ ] **run_ended resume path** — no dedicated TC; low player frequency; E-path shares `setup_new_game` with TC-1 semantics

## Handoff

**Ready for:** Human tester after Stage 7 commit; orchestrator `release APP-014 --done` if not already cleared
**Escalate human if:** TC-1 or TC-2 reproduces **Could not start game** after partial creation — treat as APP-014 regression blocker
