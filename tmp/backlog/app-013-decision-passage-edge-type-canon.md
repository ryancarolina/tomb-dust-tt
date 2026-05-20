# APP-013: Decision: passage edge type canon

| Field | Value |
|-------|-------|
| **ID** | APP-013 |
| **Type** | decision |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Spec lists two options: remap passage→archway or add passage to SITE_EDGE_TYPES.

## Acceptance criteria

- [x] Pick one approach and document in exploration spec.
- [x] Unblocks APP-001 implementation.

## Expected files

- `play/tomb_gm/world/sites.py`
- `tmp/app-exploration-delve-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-013-decision-passage-edge-canon`

_Add implementation notes, blockers, or PR links here._
