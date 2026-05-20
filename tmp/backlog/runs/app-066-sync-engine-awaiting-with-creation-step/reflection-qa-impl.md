# Reflection: QA — APP-066 implementation (round 1)

**backlog_ticket:** APP-066  
**date:** 2026-05-20  
**verdict:** FAIL  
**report:** qa-implementation-report.md

## What I verified

- Read ticket AC, run `spec.md`, `plan.md`, domain/logging spec § APP-066.
- Inspected `app/gm/orchestrator.py` `_check_creation_drift` and imports; `app/tests/test_creation_flow.py`.
- Ran mandated pytest commands from repo root.
- Compared `git diff HEAD` on expected files vs dev reflections WS1/WS2.

## Key finding

**Spec/code drift on implementation, not on PM docs:** Domain specs describe the correct two-layer awaiting model and drift semantics, but `orchestrator.py` still uses the pre-fix `engine_awaiting` comparison. Dev reflections describe the fix as shipped; the workspace does not match — likely batch overwrite (APP-068 diff on same files) or edits never saved to disk.

## Test interpretation

- `test_campaign_session.py` green — expected (no engine change).
- `test_creation_flow.py` green — **misleading for APP-066** without drift collector; passing tests do not prove AC “no drift every healthy turn.”

## What would have passed

1. WS1: `CREATION_STATUS_LABELS` import, `_expected_creation_awaiting_label()`, awaiting branch per plan §3, optional `expected_awaiting` payload, remove `engine_awaiting` compare.
2. WS2: `drift_events == []` in `test_full_creation_apprentice_caster` after updating ticket Expected files.
3. Re-run pytest + spot-check JSONL on golden path.

## Process notes

- Initial read of `orchestrator.py` in session appeared to show the fix (possible stale buffer); re-read from disk before FAIL verdict — always anchor QA on saved file + `git diff`.
- Transient `format_roll_stats_table` ImportError when pytest ran from repo root before conftest path setup; not APP-066-specific; retest green.

## Next QA round focus

- Confirm L202–203 no longer reference `engine_awaiting` for awaiting mismatch when `creation.active`.
- Confirm `drift_events == []` in integration test.
- Optional: negative `_check_creation_drift` unit probe.
- Release-stage: spec changelogs “APP-066 done” + ticket checkboxes (out of impl QA round 1 scope if code still missing).
