# Reflection: QA — APP-027 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, ticket AC + close, domain spec changelog, `reflection-qa-drift.md`

## Completed

- Compared `validate_monster_specs` (R1), bridge pre-check (R2), `validate_tool_args("start_combat")` (R3), wire points (R4), APP-028 no-fiction contract (R5), and optional `tools.py` hygiene (R6) against domain spec § **Monster id validation at combat start (APP-027)** and run `spec.md`.
- Ran `python -m pytest app/tests/test_combat_monster_validation.py play/tomb_gm/tests/test_validate_monster_specs.py -v` — **11 passed, 1 skipped** (V4).
- Ran `python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q` — **1 passed** (APP-028 regression).
- Updated domain spec: checklist **APP-027** `[x]`, removed from open work, V1–V9 Pass column, file map de-planned, changelog **APP-027 done**.
- Marked ticket AC, Status `done`, Closed 2026-05-22; updated run `status.md` Stage 6.

## Self-critique

- Did not run full `test_combat_failure_narration.py` (11 tests) — only `-k start_combat` regression slice; impl QA reported full suite green earlier.
- Did not PyGame playtest unknown monster id → mechanics-failed prefix — deferred to Stage 7 `human-test-plan.md`.
- Did not run `claim_ticket.py release APP-027 --done` — orchestrator scope per prior drift convention.
- Did not update `tmp/backlog/README.md` ticket index row (still shows `open`) — orchestrator may sync on release.

## Did I miss anything?

- [x] Ticket scope / Expected files (`app/gm/`, `play/tomb_gm/`, test modules, domain spec)
- [x] Domain spec § APP-027 ↔ layered validation code
- [x] Stable error substrings for APP-028 sibling (`monster JSON not found: …`, `monster_specs required`, `invalid monster spec`)
- [x] V1–V9 pytest green (V4 skip documented)
- [x] Ticket AC + close metadata + domain changelog
- [ ] Human playtest (Stage 7)
- [ ] `release APP-027 --done` + git commit (Stage 7)
- [ ] Backlog README status sync

## Handoff

**Verdict:** PASS (no spec ↔ code drift)  
**Ready for:** Orchestrator `release APP-027 --done`, Stage 7 commit + `human-test-plan.md`  
**Escalate human if:** Playtest shows combat-start fiction or non-null `status.combat` when monster JSON is missing, or empty `monster_specs` reaches `bridge.start_combat` from the LLM loop.
