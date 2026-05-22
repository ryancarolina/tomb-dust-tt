# APP-091: Map travel-block hint must not overlap location label

| Field | Value |
|-------|-------|
| **ID** | APP-091 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-22 |

## Summary

During character creation, hovering the sidebar map shows **"Finish Registry intake first"** at the same Y as the location name below the 3×3 grid (e.g. **Breley Keep**), so the strings overlap and are unreadable. [APP-037](app-037-block-map-travel-during-creation.md) shipped the overlay + hint but did not reserve layout space for both hint and footer labels.

## Problem (observed)

| Issue | Detail |
|-------|--------|
| **Shared row** | `_draw_surface` blits `displayName` at `grid_y + grid_h + 16`; `_draw_travel_block_overlay` blits hover hint at the same coordinates |
| **Player impact** | Registry intake hover hides current cell name on hub map during creation |
| **Regression of** | APP-037 hover hint AC — copy is visible but layout is wrong |

## Acceptance criteria

- [x] Hover hint **does not overlap** `displayName` or scene-progress line below the grid during creation travel block.
- [x] Hint remains readable on narrow sidebar map column ([APP-062](app-062-left-character-panel-inventory-spells-tabs.md) layout).
- [x] Default hint string unchanged: **"Finish Registry intake first"** (unless spec explicitly allows equivalent wording).
- [x] Unit test asserts hint blit positions stay outside the location-label row (or inside overlay rect only).
- [x] Domain spec § Map travel during creation updated with hint placement rule + changelog on close.

## Expected files

- `app/ui/panels/map_view.py`
- `app/tests/test_ui_map_creation_gate.py`
- `tmp/app-pygame-ui-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) § Map travel during creation (hint placement) + changelog.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-037 | Parent feature — travel block + hint; this ticket fixes layout only |
| APP-063 | Unrelated full map UX redesign — do not expand scope |

## Notes

**Suggested fix direction (dev-team may adjust in spec):** draw hover hint centered inside the muted grid overlay (word-wrap if needed), not on the footer label row.

**Repro:** `new game` → hover map during creation at Registry hub (`32-C`) → hint overlaps **Breley Keep**.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-091 --task map-hint-overlap-fix
python tmp/backlog/claim_ticket.py release APP-091 --done
```
