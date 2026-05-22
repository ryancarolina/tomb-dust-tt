# Reflection: QA — APP-032 playtest (Stage 7)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-032 AC, run `spec.md` Stage 7 hints, `qa-implementation-pass.md`, `drift-check.md`, domain spec § Reactive 400 retry (APP-032), and APP-031 human-test-plan for structure reuse.
- Built playtest plan on APP-031 template (prerequisites, bad/good table, JSONL guide, AC sign-off) with APP-032-specific scope:
  - **TC-1** — pytest gate for `test_transcript_400_retry.py` (19 tests) + `test_transcript_sanitize.py` (12 regression).
  - **TC-3** — Holt multi-tool exploration (`remember_fact` + `enter_dungeon`) as primary live regression for depth ≥1 400 recovery.
  - **TC-4** — failed `enter_dungeon` / invalid travel with same-turn narration (TOOL FAILED + retry path).
  - **TC-5** — optional combat illegal action narrate pass.
  - **TC-6** — session JSONL sweep for malformed-transcript 400 strings and `"The GM falters"`.
- Mapped manual TCs to ticket AC and run spec R1–R5; documented that retry is **not directly observable** in PyGame — pass = turn survival, fail = API error fallback.
- Anchored quest path to Holt / Breley / `32-C-UG-1` (same canonical regression as APP-031 session 2026-05-20).
- Noted R5 `transcript_400_retry` JSONL deferred to APP-034 (non-failure if absent).
- Minimum bar: TC-1 + TC-3 + TC-4 + TC-6.

## Self-critique

- Did not run PyGame playtest — plan only; human executes after Stage 7 commit.
- Commit hash left `pending` per `status.md` (Stage 7 commit not yet recorded by orchestrator).
- Cannot force malformed-transcript 400 in manual play; explicitly deferred to pytest R1–R7 with live symptom watch (no `"The GM falters"` mid-chain).
- TC-3 combined accept+enter prompt may split across two LLM turns — plan allows alternate 3a/3b with per-turn pass criteria (same as APP-031).
- TC-5 combat path optional and encounter-dependent; minimum bar documented without it.
- Did not add a dev-only monkeypatch TC — out of scope for human playtest; unit tests cover forced 400→success.
- Unrelated 400 / non-400 no-retry behavior is pytest-only (TC-1) — not manually verifiable without breaking API config.

## Did I miss anything?

- [x] Ticket AC: malformed transcript 400 → truncate + retry once
- [x] Run spec Stage 7 hints: residual 400 after APP-031, multi-tool depth ≥1, tool failure mid-chain, log watch
- [x] Play entry `cd app && python main.py`
- [x] Pass/fail checkboxes per step
- [x] JSONL inspection guide (400 strings, GM falters, tool chain)
- [x] Automated pytest gate before manual play (APP-032 + APP-031 regression)
- [x] APP-031 pairing clarified (proactive vs reactive layers)
- [x] APP-034 observability deferral noted
- [x] Retry invisibility documented (pass ≠ proof retry fired)
- [ ] Live session execution — deferred to human tester
- [ ] `status.md` Stage 7 checkbox — orchestrator task

## Handoff

**Ready for:** Human tester after APP-032 commit; orchestrator updates `status.md` when playtest plan is accepted.  
**Escalate human if:** TC-3 or TC-4 shows `The GM falters. (API error:` after a multi-tool or failed-tool turn, or TC-6 finds `Tool-call assistant message produced no valid function calls` in JSONL despite APP-031+032 landed.  
**Minimum bar:** TC-1 + TC-3 + TC-4 + TC-6 pass before considering APP-032 verified at the table.
