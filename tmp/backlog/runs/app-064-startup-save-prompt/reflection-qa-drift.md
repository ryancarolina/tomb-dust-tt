# Reflection: QA — APP-064 drift check (Stage 6)

**backlog_ticket:** APP-064  
**date:** 2026-05-20  
**verdict:** PASS  
**report:** drift-check.md

## What I verified

- Re-read domain spec § **Startup save-detection (APP-064)** (S1–S4, tests T1–T2) and top-level boot behavior bullets.
- Confirmed `git diff` removes the only widening site in `_init_orchestrator`; no other `has_save` mutation in `app/`.
- Verified S2/S3 narration and suggestion branches unchanged except eligibility input.
- Confirmed `GameBridge.has_save()` → `has_save_session` / `find_save_campaign` engine contract.
- Re-ran mandated pytest: `app/tests` (11 passed) and `play/tomb_gm/tests -k session` (5 passed).
- Marked all ticket AC checkboxes in backlog ticket file.

## Key finding

**No spec ↔ code drift** for APP-064. Startup prompt eligibility is engine-only (`bridge.has_save()`); the active-session OR override that caused the Supa repro is gone. Domain spec documents detection rule, UI table, engine-vs-app-save boundary, and changelog entry matching the implementation.

## Contrast with round 1 impl QA

| Item | Impl QA R1 | Drift check |
|------|------------|-------------|
| S1–S4 mapping | PASS | Re-verified on disk — still PASS |
| Ticket AC | Unchecked in ticket file | All [x] |
| pytest | 8 app / 5 session | 11 app / 5 session (APP-071 tests added; no APP-064 regression) |
| Manual T1a–T1c | Deferred Stage 7 | Still deferred — not drift blocker |

## Process notes

- Drift PASS does not set ticket **Status** `done` — orchestrator runs `release APP-064 --done`.
- Empty-rooster boot path relies on engine `has_save()` returning false + removal of UI override; no automated T1a — acceptable per plan/spec optional T2.
- Domain spec bundles APP-071 content in same file; drift scope limited to APP-064 § and boot bullet; APP-071 evaluated only where it shares launch wording.

## Handoff

Orchestrator: `release APP-064 --done`, Stage 7 `human-test-plan.md` (T1a–T1c Supa repro + regression), batch board update.
