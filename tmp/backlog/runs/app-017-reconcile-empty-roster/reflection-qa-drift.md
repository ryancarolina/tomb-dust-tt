# Reflection: QA — APP-017 drift check (Stage 6)

**backlog_ticket:** APP-017  
**date:** 2026-05-21  
**verdict:** PASS  
**report:** drift-check.md

## Completed

- Re-read domain spec § **Reconcile empty roster on load (APP-017)** (R1–R3, tests T-017, batch merge order with APP-018).
- Compared `app/gm/orchestrator.py` reconcile helpers and `_sync_creation_from_status` against run `spec.md` R1–R5 and `qa-implementation-pass.md` — independent verification, not copy-paste trust.
- Confirmed `ui/app.py` `_load_session` delegates to `_sync_creation_from_status()` without APP-017-specific UI edits (R5).
- Confirmed `_sync_creation_from_status` no longer gates on `characters` (R1b).
- Re-ran pytest: `test_reconcile_empty_roster_on_load.py` 7 passed; focused filter 13 passed.
- Wrote `drift-check.md` with **PASS** verdict.
- Marked ticket AC `[x]`; ticket **Status** → `done`, **Closed** 2026-05-21.
- Updated domain spec: checklist APP-017 `[x]`, § AC `[x]`, changelog **APP-017 done** row.

## Key finding

**No spec ↔ code drift** for APP-017. Orchestrator reads saved `engine_status` when live `awaiting` is `SETUP`, forces `creation.active` when live `roster` is empty and effective awaiting is `CHARACTER_CREATION`, skips `ROSTER_SETUP`, and runs APP-018 restore before force-active in `_sync_creation_from_status`. All seven tests pass; focused filter green with APP-016/015 regressions.

## Contrast with impl QA

| Item | Impl QA R1 | Drift check |
|------|------------|-------------|
| R1–R3 mapping | PASS | Re-verified on disk — still PASS |
| Ticket AC | Unchecked in ticket file | `[x]` |
| Domain AC checkbox | Unchecked | `[x]` |
| Domain checklist APP-017 | Open | `[x]` |
| Changelog done row | Deferred | Added |
| pytest | 7 + 13 passed | Re-run — same counts |

## Self-critique

- Did not run PyGame manual mid-creation load/continue playtest (Stage 7) — drift scoped to spec↔code↔pytest.
- Did not run `claim_ticket.py release APP-017 --done` — orchestrator clears active session.
- Did not update run `status.md` Stage 6 checkbox — orchestrator at release/commit.
- Corrupt-disk reconcile path not separately pytest'd — documented advisory; code swallows parse errors.
- Resume-failure reconcile depends on UI `_load_session` queue ordering — verified in code review, not an end-to-end load-failure integration test.

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py`, tests, domain spec)
- [x] Domain spec drift policy (§ Reconcile empty roster ↔ implementation)
- [x] APP-016 write / APP-015 clear / APP-018 merge-order boundaries
- [x] R1b `roster` vs `characters` and ROSTER_SETUP no-op
- [x] R2 live-over-saved precedence (T-017b, T-017c2)
- [ ] Corrupt `session_state.json` pytest — advisory only
- [ ] Human playtest — deferred Stage 7

## Handoff

Orchestrator: `release APP-017 --done`, Stage 7 `human-test-plan.md` (mid-creation autosave → quit → relaunch → load game chips), batch board update, git commit including `test_reconcile_empty_roster_on_load.py`.
