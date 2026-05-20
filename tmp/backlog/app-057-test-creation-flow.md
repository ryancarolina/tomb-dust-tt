# APP-057: test_creation_flow.py

| Field | Value |
|-------|-------|
| **ID** | APP-057 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Closed** | 2026-05-20 |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Automated test for the full character creation FSM through finalize with a non-empty roster, guarding against creation drift regressions.

## Acceptance criteria

- [x] `app/tests/test_creation_flow.py` exercises creation steps through finalize.
- [x] Test asserts engine roster non-empty after finalize.
- [x] `python -m pytest app/tests/test_creation_flow.py -q` passes.
- [x] Depends on APP-049 (app/tests package) if not yet present.

## Expected files

- `app/tests/test_creation_flow.py` (new integration test)
- `app/gm/orchestrator.py` (RACE/CLASS `*_table_shown` gating, NAME→RACE / ROLL_STATS→CLASS chain, execute guards)
- `app/gm/creation.py` (`CreationState`: `races_table_shown`, `classes_table_shown` + serialization)
- `app/tests/conftest.py` (only if a shared fixture is required; default unchanged)

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

Referenced in character-creation spec test commands section.

**Scope (2026-05-20, PM r2):** Expanded from test-only to include minimal `orchestrator.py` + `creation.py` fixes so the 8-input integration path reaches finalize (QA SPEC-001/002/SCOPE-001). See run `spec.md` R6 and `reflection-pm-r2.md`.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-049 | may block (tests package) |
| APP-006–APP-011 | tests should pass after creation hardening |
