# APP-001: Fix site passage edge types

| Field | Value |
|-------|-------|
| **ID** | APP-001 |
| **Type** | bug |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Site JSON uses edge type `passage` which fails validate_content / tomb_gm check.

## Acceptance criteria

- [x] Remap passage to archway in boydon-undercroft.json and shadowfen-vaults.json (or add passage to SITE_EDGE_TYPES per APP-013).
- [x] python build/tools/validate_content.py exits 0.
- [x] python -m tomb_gm --workspace play/workspace check has no site edge blocker.

## Expected files

- `build/data/sites/boydon-undercroft.json`
- `build/data/sites/shadowfen-vaults.json`
- `play/tomb_gm/world/sites.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-001-fix-site-passage-edge-types`

_Add implementation notes, blockers, or PR links here._
