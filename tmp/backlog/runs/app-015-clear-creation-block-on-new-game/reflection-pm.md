# Reflection: PM — APP-015 clear-creation-block-on-new-game

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-session-persistence-spec.md` § New game — creation block clear (APP-015)

## Completed

- Wrote run-local `spec.md` (summary, goals, non-goals, AC mapping, test/playtest pointers).
- Added domain spec § **New game — creation block clear (APP-015)** with C1–C4, batch table vs APP-014/016/018, non-regression, and tests **T-015a–c** (IDs chosen to avoid APP-016’s T4a–d).
- Updated domain spec top-level `new game` bullet, task checklist (deduped duplicate APP-014/015/016 lines), file map, changelog.
- Marked `status.md` PM spec draft complete.

## Self-critique

- APP-014 § **setup_new_game lifecycle** now exists in the domain spec; APP-015 § is inserted after it with explicit **before L1 / L2** ordering to align with L1–L7 table. Parallel impl on `orchestrator.py` needs merge discipline.
- Chose **surgical** `creation_state` write as preferred over start-only `unlink` to satisfy APP-016 forward-compat; Dev may still use unlink+write if simpler — spec allows both.
- Ticket **Expected files** is vague (“session persistence layer”); spec pins `orchestrator.py` + `app/tests/` — within reasonable interpretation.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator-primary; UI secondary
- [x] Domain spec / registry_gap false — no new `tmp/app-*-spec.md`
- [x] Code paths from research-brief — early return, autosave finally, `_is_mid_creation_resume_failure`
- [x] Tests / AC mapped — T-015a–c + manual hints
- [x] Batch APP-014 (lifecycle order) and APP-016 (engine_status field) boundaries documented
- [x] APP-014 lifecycle section present; C1–C2 ordered before L1/L2

## Handoff

**Ready for:** QA spec review (adversarial PASS/FAIL on `spec.md` + domain § APP-015)

**Escalate human if:** QA requires creation block = `null` (inactive) instead of active NAME export — would change APP-071 variant B semantics at boot after failed `new game`
