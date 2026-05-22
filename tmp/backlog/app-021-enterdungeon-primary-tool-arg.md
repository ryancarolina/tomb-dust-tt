# APP-021: enter_dungeon primary tool arg

| Field | Value |
|-------|-------|
| **ID** | APP-021 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

Tool schema should document enter_dungeon(site_address) as primary arg.

## Acceptance criteria

- [x] Update tool schema/docs for enter_dungeon(site_address).

## Expected files

- `app/gm/tools.py`
- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Implemented:** `tools.py` documents `site_address` as primary param; `site_id` as alias. `orchestrator.py` maps `site_id` → `site_address` before `bridge.enter_dungeon()`. Verified in Fatty session (`breley-undercrypt` → `32-C-UG-1`).
