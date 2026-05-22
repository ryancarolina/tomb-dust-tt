# APP-023: Friendly travel name to AV-GRID

| Field | Value |
|-------|-------|
| **ID** | APP-023 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Surface travel needs map from friendly names to grid addresses.

## Acceptance criteria

- [x] Map friendly place names to AV-GRID for surface travel via engine world.py.

## Expected files

- `play/tomb_gm/services/world.py`
- `play/tomb_gm/services/beat.py` _(shared resolver when `_find_address` misses)_
- `play/tomb_gm/tests/test_world.py`
- `play/tomb_gm/tests/test_beat.py`
- `app/gm/bridge.py` _(travel resolution hook)_
- `app/gm/tools.py` _(optional: tool description on close)_
- `build/data/av-grid/av-grid.json` _(only if alias/schema change needed — not required for MVP)_

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-023-friendly-travel-av-grid`

_Add implementation notes, blockers, or PR links here._
