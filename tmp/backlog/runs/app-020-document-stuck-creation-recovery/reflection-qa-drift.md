# Reflection: QA — APP-020 drift

**Agent:** QA (drift)  
**Round:** 1 (Stage 6)  
**Deliverables:** `drift-check.md`, domain spec open-work sync, ticket AC close

## Completed

- Read ticket APP-020, run `spec.md`, domain § APP-020 (R-020a–g, T-020a–b), prior `qa-implementation-pass.md`.
- Re-verified `app/README.md` against domain checklist independently (line refs + negative grep).
- Cross-checked README claims to live code: `orchestrator.py` (`process_turn`, `setup_new_game`, resume failure copy), `ui/app.py` (`_init_orchestrator` APP-064 branches, load/new aliases).
- Confirmed `git diff` scope — README + domain spec only; no `app/gm` or `app/ui` behavior changes.
- Wrote `drift-check.md` with **PASS** verdict; marked ticket AC complete.
- Updated domain spec **Open work** line (APP-014–APP-020 batch closed) + drift changelog row.

## Self-critique

- Did not run T-020b manual playtest (partial creation → relaunch → **`new game`** → NAME) — deferred to Stage 7 per pipeline; doc-only scope judged non-blocking for drift.
- Did not run `claim_ticket.py release APP-020 --done` — orchestrator owns session release per dev-team template.
- Did not update `tmp/backlog/README.md` status row — `release --done` script owns that.

## Did I miss anything?

- [x] Ticket AC — stuck creation → **`new game`** documented
- [x] R-020a–g ↔ README
- [x] README ↔ APP-014/015/064/071/019 code behavior (doc↔code, not new code)
- [x] Expected files only — no scope creep
- [x] Domain spec checklist + changelog
- [x] Forbidden recovery paths (hand-edit / CLI) — **Do not** only
- [ ] T-020b human playtest — Stage 7
- [ ] `release APP-020 --done` — orchestrator

## Handoff

**Verdict:** **PASS** — no spec↔README↔code drift for APP-020 scope.  
**AC complete:** **yes**  
**Next:** Orchestrator `release APP-020 --done`, Stage 7 commit + `human-test-plan.md` (T-020b).  
**Escalate human if:** README still implies boot auto-restore from app autosave alone, or stuck recovery prose contradicts APP-018 desk-resume when not broken.
