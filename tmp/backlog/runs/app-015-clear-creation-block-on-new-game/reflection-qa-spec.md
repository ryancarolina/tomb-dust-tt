# Reflection: QA — APP-015 spec

**Agent:** QA
**Round:** 1
**Deliverables:** `qa-spec-pass.md`

## Completed

- Adversarial review of run `spec.md`, `research-brief.md`, domain spec § **New game — creation block clear (APP-015)**, ticket APP-015, and batch boundaries vs APP-014/APP-016.
- Verified code paths in `app/gm/orchestrator.py` (`setup_new_game` late clear + early return; `_is_mid_creation_resume_failure` disk read).
- Confirmed registry row in `tmp/app-master-spec.md`; `registry_gap: false` upheld.
- Issued **PASS** (round 1) with non-blocker notes for Dev plan.

## Self-critique

- Did not trace `CreationState.to_dict()` field-by-field for “no carry-over” — assumed FSM default NAME state matches export contract; Dev plan should confirm exported JSON lacks stale `name`/`roll_result`.
- T-015c integration with full `process_turn` + UI finally was reviewed at spec level only; no pytest exists yet (expected pre-impl).
- APP-016 missing section body noted as cross-ticket debt; did not deep-review APP-016 run artifacts.

## Did I miss anything?

- [x] Ticket scope / Expected files — vague ticket wording flagged; run spec pins orchestrator + tests
- [x] Domain spec / registry_gap / AGENTS.md — no drift on APP-015 scope
- [x] Code paths not traced — core failure + disk probe traced; UI `_save_session` finally noted
- [x] Tests or AC not mapped — T-015a–c cover C1–C3; minor T-015b memory assertion gap noted
- [x] Batch APP-014/016 boundaries — prepend order and surgical C2 vs APP-016 verified

## Handoff

**Ready for:** Dev plan (Stage 3) — `plan.md` with traces for `_clear_creation_block_on_disk` prepend in `setup_new_game`

**Escalate human if:** PM/Dev choose inactive `creation_state: null` instead of active NAME export on clear — would affect APP-071 variant B semantics (PM reflection already flagged)
