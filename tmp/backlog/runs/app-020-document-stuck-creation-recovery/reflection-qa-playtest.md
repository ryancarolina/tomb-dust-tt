# Reflection: QA — APP-020 Stage 7 human playtest plan

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Wrote `human-test-plan.md` per `templates.md` § human-test-plan.md: doc-first prerequisites split (required read vs optional PyGame), four test cases, AC mapping table (ticket AC + R-020a–g + T-020b), sign-off with minimum pass bar (TC-1 + TC-2).
- **TC-1:** Stuck subsection, symptoms, retry-once, **`new game`** recovery + wipe warning, forbidden hand-edit/CLI paths (R-020a–c, D1–D3).
- **TC-2:** Partial vs finished save, command table, grep gates (`auto-resumes`, `session_state.json`), Quick Start + Features persistence corrections (R-020d–f, D4–D6).
- **TC-3 (optional):** T-020b / APP-014 TC-1 cross-check — partial creation → README-only guidance → **`new game`** → NAME desk.
- **TC-4 (optional):** Finished-save **`load game`** non-regression (doc read + optional in-game).
- Commit set to `1b45332` from `git log` for APP-020 README change; play entry marked optional per doc-only scope.
- Cross-linked APP-018, APP-019, APP-071, APP-064 in Notes — avoids false failures on resume-without-reset and load-failure copy.

## Self-critique

- **Did not execute** manual README walk or PyGame session in this round — plan is an executable checklist for a human tester post-commit.
- **TC-3/TC-4** require API key and time; minimum sign-off is doc-only TC-1 + TC-2, which matches impl QA deferral of T-020b.
- Grep steps assume repo checkout; a tester reading README on GitHub must mentally substitute "search in file" for `rg`.
- Line numbers (~L15, ~L17) are approximate — README edits after `1b45332` may shift; section headings are the stable anchors.

## Did I miss anything?

- [x] Ticket scope / Expected files — `app/README.md` only; no code paths in plan
- [x] Domain spec § APP-020 — R-020a–g and T-020a–b mapped to TC-1–TC-4
- [x] qa-implementation-pass.md evidence echoed in TC steps (grep checks, section names)
- [x] Tests or AC not mapped — acceptance sign-off table + per-TC goals
- [x] Commit hash — `1b45332` recorded
- [x] Doc-only vs optional play — explicit in scope note and prerequisites
- [ ] **Live human execution** — no tester sign-off yet; `status.md` Stage 7 playtest checkbox still open

## Handoff

**Ready for:** Human tester — required: read-through TC-1 + TC-2; optional: TC-3/TC-4 before batch board marks APP-020 complete  
**Escalate human if:** TC-1/TC-2 fail while `qa-implementation-pass.md` claims R-020 pass — verify working tree matches `1b45332` README; or TC-3 fails (README says **`new game`** but game returns setup error) indicating doc/behavior drift vs APP-014/015
