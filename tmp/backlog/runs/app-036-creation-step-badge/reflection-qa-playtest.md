# Reflection: QA — APP-036 human playtest plan

**Agent:** QA (playtest gate)  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-036 AC, run `spec.md` (R1–R6), `qa-implementation-pass.md`, domain spec § Creation step badge (APP-036), and human-test-plan templates from APP-037, APP-065, APP-057, APP-018.
- Mapped seven manual TCs to ticket AC and spec requirements: pytest preflight (TC-1), badge at creation start (TC-2), human-label vs footer-token policy (TC-3), step advance through CLASS/SKILLS (TC-4), post-finalize hide via APP-057 inputs (TC-5), resize cache (TC-6), mid-creation resume badge (TC-7).
- Documented **display map table** and **good/bad** checklist so testers can distinguish `Registry: Race` from `RACE_INPUT` without reading code.
- Wrote **`human-test-plan.md`** with prerequisites, AC sign-off table, minimum pass bar (TC-2 + TC-3 + TC-5), and cross-ticket notes (APP-037, APP-065, APP-062, APP-007).

## Self-critique

- Did **not** run manual PyGame play or pytest in this session — plan targets Stage 7 human execution; commit still pending per `status.md`.
- TC-4 step 2 documents expected **`Registry: Class`** after ROLL_STATS chain (not `Roll Stats`) — matches live FSM where ROLL_STATS auto-chains; tester may briefly see Roll Stats if status push lands mid-chain; noted in TC-4 note.
- TC-7 resume badge timing may lag one turn (impl QA flagged `test_creation_restore.py` as optional); marked optional with escalation note rather than blocking primary sign-off.
- Headless tests cover state/enrich paths only — clerk-green pixel rendering relies on human TC-2 step 3.

## Did I miss anything?

- [x] Ticket scope — visible badge, human labels, orchestrator source, post-finalize hide, APP-062 placement
- [x] Domain spec — `Registry:` prefix, stats panel top, enriched keys, footer-token prohibition
- [x] APP-065 alignment — badge must not show `*_INPUT` / `*_CONFIRMATION` tokens
- [x] APP-037 coexistence — map unblock after finalize optional check in TC-5
- [x] APP-057 golden path — TC-5 reuses eight-input Dumpy apprentice path for finalize hide proof
- [x] Sidebar resize — TC-6 mirrors APP-037 resize preserve pattern
- [x] Session resume — TC-7 optional per spec human playtest hints
- [x] AC mapping — sign-off table ties TCs to ticket + spec R1–R4

## Handoff

**Ready for:** Human tester after Stage 7 commit; minimum sign-off TC-2 + TC-3 + TC-5; tick `status.md` Stage 7 human-test-plan checkbox.

**Escalate human if:** Badge missing during creation (TC-2 fail), shows footer tokens (TC-3 fail), or persists after finalize (TC-5 fail) — likely `_enrich_status_for_ui` or `get_creation_step_badge()` regression; re-run TC-1 pytest gate and compare enriched status in JSONL logs.
