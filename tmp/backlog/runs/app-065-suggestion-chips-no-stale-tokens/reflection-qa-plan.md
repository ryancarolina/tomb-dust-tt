# Reflection: QA plan — round 1

**Role:** QA (plan gate)  
**backlog_ticket:** APP-065  
**Deliverable:** `qa-plan-report-1.md` (FAIL)

## Completed

- Reviewed `plan.md` against ticket APP-065, `spec.md` (r2 / `qa-spec-pass.md`), `research-brief.md`, and live code in `app/ui/app.py`, `app/gm/orchestrator.py`, `app/gm/creation.py`.
- Verified line-level traces for stale `if suggestions:` gate, `_extract_suggestions`, equipment confirm handler, and domain spec § Suggestion chips alignment.
- Wrote `qa-plan-report-1.md` with verdict **FAIL**, two major findings (PLAN-001 exception-path tests, PLAN-002 except `return` preservation), one minor (PLAN-003 queue empty-list test).

## Self-critique

- Did not run pytest (no impl yet); review is static only.
- Did not deep-read `test_creation_flow.py` for conflicts with planned post-finalize test — assumed orchestrator fixture pattern from plan is sufficient.
- Blocklist regex `{2,}` vs spec `*` treated as aligned (domain spec already uses `{2,}`); not escalated.

## Missed?

- [x] Ticket Expected files vs plan file table
- [x] All ticket AC rows mapped in plan § Acceptance criteria mapping
- [x] Spec R1 exception AC vs plan §4 — **gap found (PLAN-001)**
- [x] Except-path TTS behavior — **gap found (PLAN-002)**
- [x] Batch APP-073 ordering note — present in plan
- [x] Import path open question — acceptable defer to impl if PLAN-001/002 fixed
- [ ] Pygame integration test feasibility — not probed; suggested helper/spy instead

## Handoff

**Needs Dev plan revision (round 2)** — update `plan.md` §3.2–§4 per report, then orchestrator dispatches QA plan round 2.

Do **not** dispatch implementation until `qa-plan-pass.md` exists.

**Blocker count:** 2 major, 1 minor.
