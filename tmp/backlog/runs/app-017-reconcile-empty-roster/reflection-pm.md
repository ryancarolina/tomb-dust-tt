# Reflection: PM — APP-017 reconcile-empty-roster

**Agent:** PM
**Round:** 1
**Deliverables:** `spec.md`, `tmp/app-session-persistence-spec.md` § Reconcile empty roster on load (APP-017), `reflection-pm.md`

## Completed

- Wrote run-local `spec.md` with R1–R4, T-017a–e, human playtest hints, pointers to research/batch/018.
- Added domain spec § **Reconcile empty roster on load (APP-017)** with R1–R3, ticket AC mapping table, batch boundary vs APP-018 (017 → `creation.active`; 018 → step + fields), tests, non-regression.
- Updated domain checklist (APP-017 open, APP-018 pointer), APP-016 Consumers table, file map, changelog draft.
- Marked `status.md` PM stage complete.

## Self-critique

- **`characters` vs `roster`:** Research flagged engine `ROSTER_SETUP` when unslotted rows exist; ticket AC says "empty roster" — spec follows roster-only for force-active; Dev may need explicit handling for orphan characters (not expanded in AC).
- **Ticket Expected files** lists orchestrator only; spec recommends tests in `app/tests/` — Dev should extend ticket before adding test files (same pattern as APP-071).
- **WORLD_INTRO → NAME** minimal exception may overlap APP-018 if both touch step on same load — batch merge order documented but QA should watch for double-reset.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator-primary; UI avoided via internal disk read
- [x] Domain spec / registry_gap false — no new `tmp/app-*-spec.md`
- [x] Code paths from research-brief — `_load_session`, `_sync_creation_from_status`, `_restore_history`, T4a desync
- [x] Tests / AC mapped — ticket AC → R1 + domain T-017a–e
- [x] APP-018 boundary — active vs step/fields split in R3 and domain § batch table
- [x] APP-016 consumer link updated

## Handoff

**Ready for:** QA spec review (adversarial PASS/FAIL on `spec.md` + domain § APP-017)

**Escalate human if:** Product wants APP-017 to also restore step (would absorb APP-018) or requires `ui/app.py` changes for reconcile visibility
