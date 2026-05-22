# Reflection: QA human playtest plan — APP-030

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-030  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-030 AC, run `spec.md`, `plan.md`, `qa-implementation-pass.md`, domain spec § Combat integration golden path (APP-030), and `app/tests/test_combat_integration.py` (I1 step trace + fixture helpers).
- Cross-read APP-027 `human-test-plan.md` TC-6 and APP-028 TC-7 for undercrypt setup and grave-ghoul beat phrasing; scoped APP-030 manual plan to **happy path only** (no file-hide failure repros).
- Authored `human-test-plan.md` with six test cases: pytest gate **TC-1** (authoritative sign-off), undercrypt setup **TC-2**, combat start **TC-3**, PC attack **TC-4**, combat end **TC-5**, optional initiative smoke **TC-6**.
- Documented **layer difference**: I1 uses direct `bridge.combat_attack`; live PyGame routes PC attacks through **`combat_action`** during active combat — manual TC-4 validates production path, TC-1 validates bridge contract.
- Marked manual play **optional** per ticket scope (test-only AC; impl QA deferred human test to Stage 7).

## Self-critique

- **Did not run manual playtest** — plan only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA already reported 30/30 green); TC-1 delegates to tester.
- **Commit hash** left **pending** — `test_combat_integration.py` was untracked at authoring time; tester must use Stage 7 commit containing I1 + V4 removal.
- **TC-4 LLM flakiness:** Model may call wrong tool or act before PC turn — plan documents retry phrasing and optional early-turn negative check; pass/fail is mechanical ok on correct turn.
- **Did not manual-test `bridge.combat_attack` during active combat via PyGame** — orchestrator blocks that path by design; I1 owns bridge API; manual owns orchestrator routing.
- **Short plan vs APP-027/028:** Intentional — APP-030 AC is pytest I1; manual is optional smoke, not adversarial validation suite.

## Not verified (explicit)

- [ ] Live PyGame session for any TC
- [ ] TC-3 beat-trigger start with roster PC + grave-ghoul
- [ ] TC-4 `combat_action` ATTACK on PC turn
- [ ] TC-5 `combat_end` + DELVE phase restore
- [ ] JSONL tool chain start → action → end end-to-end
- [ ] APP-029 auto-chain behavior under load
- [ ] Initiative seed edge cases beyond I1 `_advance_to_pc_turn` cap

## Handoff

**Orchestrator:** Stage 7 — human may execute `human-test-plan.md` optionally; **TC-1 alone satisfies ticket AC**. Update `status.md` Stage 7 ✅ with commit hash when Stage 7a lands.

**If TC-1 fails:** Bridge golden path regression — inspect `_ensure_combat_roster_session`, `_advance_to_pc_turn`, or `grave-ghoul.json` content root.

**If TC-1 passes but TC-3 fails:** APP-027 validation or beat trigger regression — compare to APP-027 TC-6 optional smoke; ensure roster PC exists (not session-only).

**If TC-3 passes but TC-4 fails with `not your turn` on correct turn:** APP-029 auto-chain or turn sync — check `_combat_auto_chain` and engine initiative; I1 may still pass if bridge advance works.

**If TC-4 passes but TC-5 fails:** Orchestrator `combat_end` dispatch or status sync — file bug; I1 `bridge.combat_end()` may still pass in isolation.

**Blockers from this gate:** None (plan artifact only).
