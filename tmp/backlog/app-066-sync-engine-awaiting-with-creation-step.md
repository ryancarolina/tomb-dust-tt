# APP-066: Sync engine awaiting with creation step

| Field | Value |
|-------|-------|
| **ID** | APP-066 |
| **Type** | bug |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

During character creation, `bridge.status()["awaiting"]` stays `CHARACTER_CREATION` and `party.phase` stays `preparation` while narration footers use granular labels (`SKILLS_INPUT`, `SPELL_SCHOOLS_INPUT`, etc.). Every turn in `session-2026-05-20.jsonl` emits `creation_drift` with `awaiting_mismatch` and often `phase_mismatch` — noise that hides real regressions.

## Evidence (session log vs code)

- Log: 30+ `creation_drift` events on 2026-05-20, e.g. step `SKILLS`, `awaiting: CHARACTER_CREATION`, `narrated_awaiting: SKILLS_INPUT`, `engine_phase: preparation`.
- Code: `format_creation_status()` in `creation.py` emits step-specific `Awaiting:` labels; `_check_creation_drift()` compares those to engine `status["awaiting"]` (`orchestrator.py` ~184–221).
- APP-002 only **logs** drift; it does not fix the underlying contract.

## Acceptance criteria

- [x] While `creation.active`, engine `awaiting` reflects the current creation step (or drift check compares `creation.step` → `CREATION_STATUS_LABELS` instead of engine `CHARACTER_CREATION`).
- [x] `creation_drift` does **not** fire on every healthy creation turn after fix.
- [x] Domain spec documents engine vs narration awaiting contract.
- [x] `app/tests/test_creation_flow.py` (APP-057) asserts no drift on golden-path turns (optional assert in test).

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/bridge.py` and/or `play/tomb_gm/` session status (if awaiting is engine-owned)
- `app/gm/creation.py`
- `app/tests/test_creation_flow.py`
- `tmp/app-character-creation-spec.md`
- `tmp/app-logging-qa-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update domain spec changelog for awaiting/phase contract.
3. Update logging spec if drift semantics change.

## Notes

**Session:** `app/logs/session-2026-05-20.jsonl`  
**Related:** APP-002 (logging), APP-007 (code-owned footer labels), APP-036 (UI badge from engine).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-057 | test should cover post-fix |
