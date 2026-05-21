# APP-017: Reconcile empty roster on load

| Field | Value |
|-------|-------|
| **ID** | APP-017 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-21 |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Load with empty roster but inactive creation should force creation.

## Acceptance criteria

- [x] If engine roster empty, creation inactive, and `awaiting == CHARACTER_CREATION` (live or saved) → force creation mode.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_reconcile_empty_roster_on_load.py` — T-017a–f, T-017c2

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Consumer:** reads `engine_status` from `session_state.json` when present (written by APP-016; cleared on **`new game`** by APP-015). See domain spec § Engine status snapshot on save (APP-016) — Consumers.
