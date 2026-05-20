# QA PASS: plan

**Task:** APP-015-clear-creation-block-on-new-game  
**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**Round:** 2  
**domain_spec_creation:** not_needed

## Round 1 blocker resolution

| ID | Round 1 issue | Round 2 status |
|----|---------------|----------------|
| **PLAN-001** | C2 preserved `engine_status` (contradicted domain) | **Fixed** — WS1 §3 `data.pop("engine_status", None)`; Approach § strategy; batch rationale vs APP-016 write path |
| **PLAN-002** | T-015d missing from test plan | **Fixed** — WS2 table, `seed_stale_creation(with_engine_status=…)`, pytest + manual Stage 7 bullets |
| **PLAN-003** | Run `spec.md` still indexed T-015a–c only | **Acknowledged** — plan cites domain **T-015a–d**; run `spec.md` C5 pointer still a–c (PM optional; domain spec is authority) |

No remaining “preserve `engine_status`” language in `plan.md` (grep verified).

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches plan (`tmp/app-session-persistence-spec.md` § New game — creation block clear, T-015d)
- [x] Acceptance criteria testable — C1–C2 at `setup_new_game` entry; T-015a–d + AC mapping table
- [x] Code traces match repo — Traces A–E unchanged; F–H planned; line refs consistent with round 1 independent traces
- [x] AGENTS.md / canon compliance — app-only; no `build/` edits
- [x] Tests/commands listed — `test_creation_block_on_new_game.py`, `-k` filters, manual `engine_status` check
- [x] Plan files ⊆ ticket Expected files — `app/gm/orchestrator.py`, `app/tests/` (optional `conftest.py`)
- [x] APP-014 merge order — **C1 → C2 → L1 → L1b → L2 … → L7** documented
- [x] Domain C2 alignment — remove `engine_status` on every `setup_new_game` entry; absent/null until next save (APP-016)

## Notes

- **T-015d** early-return path: plan allows success **or** mocked failure after C1–C2 — matches domain § Tests APP-015 (entry after prepend).
- **T-015b** in-memory assertion retained from QA spec follow-up.
- Run `spec.md` § Requirements C5 / Non-goals still defer APP-016 write to non-goals; domain already owns clear-on-new-game under APP-015 — no plan blocker.
- Optional Dev follow-up: shared `SAVE_PATH` between orchestrator and UI (plan Open Q #4) — out of scope, documented.

**Verdict:** PASS — ready for Stage 4 implementation (subject to batch `impl-check` for APP-014/016 deps).
