# QA implementation reflection — APP-070

**backlog_ticket:** APP-070  
**Date:** 2026-05-20  
**Outcome:** FAIL (Stage 5)

## What I verified

- Read ticket AC, run `spec.md`, `plan.md`, domain spec § APP-070, and `reflection-dev-impl.md`.
- Reviewed git diff on expected files; traced `_compose_creation_narration`, `sanitize_premature_completion_flavor`, `_check_creation_drift`.
- Ran `python -m pytest tests/test_creation_flow.py -q` from `app/` (4 passed).
- Attempted `::test_skills_turn_rejects_premature_completion_flavor` — pytest: no match.

## Findings

1. **Core fix is in place:** Compose-time blanking of premature completion flavor and drift extensions match spec C1–C5 and D1–D2. Post-finalize golden path still passes; legitimate reception footer path preserved via `roster_len > 0` / `not creation.active` compose gate.

2. **Blocking gap:** T1 regression test never landed despite ticket AC #3, domain spec test contract, plan §3.1, and dev reflection claiming “7 passed.” Actual suite count is 4; new tests in diff are APP-069 only.

3. **Spec drift:** `tmp/app-character-creation-spec.md` documents `test_skills_turn_rejects_premature_completion_flavor` as required; implementation QA cannot PASS until test exists and green.

## Adversarial checks

- **False PASS risk:** Relying on golden path alone would miss mid-FSM injection — exactly the Dumpy bug vector.
- **Dev reflection mismatch:** Reported test name and pass count do not match workspace; QA treated repo state as source of truth.
- **Drift vs sanitizer:** Not a fail; optional drift on T1 is spec-aligned.

## Next QA pass criteria

- `test_skills_turn_rejects_premature_completion_flavor` present and green.
- Full `test_creation_flow.py -q` green (expect 5+ tests).
- Re-confirm AC 1–2 unchanged; no regression on turn-8 `RECEPTION_CHOICE` / `Phase: preparation`.

## Process note

Implementation review should not mark ticket `done` or write `qa-implementation-pass.md` until T1 is present — compose-only delivery is insufficient for P0 close per ticket and qa-plan-pass.
