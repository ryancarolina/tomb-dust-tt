# Reflection: QA — playtest (APP-017)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-017 (single AC), run `spec.md` R1–R5, domain spec § Reconcile empty roster on load, `qa-implementation-pass.md`, and `test_reconcile_empty_roster_on_load.py` (T-017a–f, T-017c2).
- Mapped manual cases to ticket AC and automated tests; followed dev-team template § human-test-plan and APP-016 / APP-065 table format.
- Wrote TC-0 pytest gate plus five PyGame TCs: mid-creation desk resume (T-017a), equipment chips (T-017e), post-finalize non-regression (T-017c), legacy load (T-017d), JSON null-creation_state + saved snapshot (T-017b).
- Documented pre-017 failure signals, APP-018/071 boundaries, and automated-only T-017f / T-017c2 so testers do not false-fail.

## Self-critique

- Did not run manual PyGame — plan derived from spec, impl QA pass, orchestrator load/sync traces, and APP-016 playtest patterns; human must execute on target OS.
- TC-1 step 7 allows two valid post-load narrations (APP-071 variant B vs creation resume turn) — intentional softness; TC-2 is the hard chip assertion for force-active.
- TC-5 / APP-018 boundary may confuse testers when step resets to NAME after null `creation_state` — called out explicitly in TC-5 note and out-of-scope.
- Commit hash left `pending` — APP-017 may ship in a batch commit without isolated hash at Stage 7.

## Did I miss anything?

| Check | Status |
|-------|--------|
| Ticket scope / Expected files | OK — manual play only; no claim that UI or save write paths changed |
| Domain spec R1–R5 / T-017 mapping | OK — AC sign-off table links TCs to R1, R2, T-017e |
| Load path (`_load_session` + `process_turn load game`) | OK — both invoke `_sync_creation_from_status` / reconcile |
| APP-018 merge order | OK — out-of-scope for step restore failures |
| APP-064 boot vs load game | OK — prerequisites note |
| Regression post-finalize | OK — TC-3 |
| pytest before manual | OK — TC-0 |

## Handoff

- **Ready for:** Stage 7 human execution after APP-017 commit; tick `status.md` human-test-plan checklist.
- **Escalate human if:** TC-0 passes but TC-2 shows empty equipment chips after load (reconcile not reaching UI), or TC-3 forces NAME desk after finalize (R1 row 2 regression).
