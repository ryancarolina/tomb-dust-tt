# Dev reflection: APP-066 fix round 1

**backlog_ticket:** APP-066  
**Round:** QA impl FAIL → re-impl (WS1 + WS2)  
**Date:** 2026-05-20

## Context

QA implementation report (round 1) found WS1/WS2 described in `reflection-dev-impl-WS1.md` / `WS2.md` but **not on disk**: `_check_creation_drift` still compared narrated `Awaiting:` to engine `CHARACTER_CREATION`, causing false `awaiting_mismatch` every healthy creation turn.

## Changes landed

### WS1 — `app/gm/orchestrator.py`

1. Imported `CREATION_STATUS_LABELS` from `gm.creation`.
2. Added `_expected_creation_awaiting_label()` before `_creation_drift_scope` — mirrors `format_creation_status()` (`CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()`).
3. Rewrote awaiting branch in `_check_creation_drift`:
   - When `creation.active` and `narrated_awaiting`: compare to expected label, not `status["awaiting"]`.
   - When not `creation.active` but still in drift scope (resume edge): **no** awaiting compare.
4. Drift payload: build `payload` dict; add `expected_awaiting` when computed (R5). Removed dead `engine_awaiting` local.
5. Left `_creation_drift_scope`, phase guards, and coarse `awaiting` in payload unchanged.

### WS2 — `app/tests/test_creation_flow.py`

- Ticket **Expected files** already listed `app/tests/test_creation_flow.py` (no ticket edit needed).
- `test_full_creation_apprentice_caster`: monkeypatch `gm.orchestrator.log_creation_drift` into `drift_events`; after `INPUTS` loop, `assert drift_events == []`.

## Verification

| Command | Result |
|---------|--------|
| `git diff app/gm/orchestrator.py app/tests/test_creation_flow.py` | Shows APP-066 hunks (import, helper, awaiting branch, payload, test assert) |
| `python -m pytest app/tests/test_creation_flow.py -q` | 2 passed |
| `python -m pytest play/tomb_gm/tests/test_campaign_session.py -q` | 1 passed |

## Risks / follow-up

- **Not done this round:** domain spec changelogs (`done` row), `release APP-066 --done`, manual JSONL grep — ticket release / PM hygiene.
- **Batch noise:** `orchestrator.py` / `test_creation_flow.py` may still carry unrelated APP-068 diffs in wider `git diff HEAD`; APP-066 hunks are isolated in paths above.
- **Re-test:** Implementation QA should re-run round 1 against `spec.md` R2–R6 and IMPL-001/002.

## Handoff

Ready for **QA implementation round 2**. Blockers IMPL-001 and IMPL-002 addressed in working tree.
