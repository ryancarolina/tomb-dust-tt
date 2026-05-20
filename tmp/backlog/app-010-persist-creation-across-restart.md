# APP-010: Persist creation across restart

| Field | Value |
|-------|-------|
| **ID** | APP-010 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Resume must restore exact creation step from session_state.json.

## Acceptance criteria

- [x] Resume exact step from session_state.json.
- [x] Sync if engine already has roster (skip redundant steps).

## Expected files

- `app/session_state.json schema`
- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
