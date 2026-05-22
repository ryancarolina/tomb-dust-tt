# APP-060: Auto-scroll narration on player input and GM response

| Field | Value |
|-------|-------|
| **ID** | APP-060 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

After the player submits input, they must **manually scroll** the narration panel to see their line and the GM reply. The UI already calls `_smooth_scroll_to_bottom()` on queue events, but **`scroll_to_bottom()` runs before layout rebuild** — `_total_height` stays stale until `draw()` runs `_rebuild()`, so the scroll offset does not reach the new content (especially long GM replies and markdown tables).

## Problem (root cause)

In [`app/ui/panels/narration.py`](../../app/ui/panels/narration.py):

- `add_line` / `add_lines` set `_dirty = True` but defer `_rebuild()`.
- `scroll_to_bottom()` uses `_total_height` from the **previous** layout.

In [`app/ui/app.py`](../../app/ui/app.py) `_process_ui_queue`, scroll is triggered immediately after `add_line(s)` — too early.

## Acceptance criteria

- [x] After **player submit**, narration scrolls so the player's line is visible (preferably pinned to bottom of panel).
- [x] After **GM response** (`narration`, `narration_text`, `error`), narration scrolls to show the **full** new content including wrapped text and tables.
- [x] Fix is layout-correct: scroll position computed **after** content height is known (rebuild-before-scroll, `_follow_tail` flag in `draw()`, or equivalent).
- [x] Long creation tables and multi-paragraph GM replies no longer require manual wheel scroll to read the latest line.
- [x] Manual scroll **up** to read history still works; on **new** player/GM content, view returns to bottom (document in spec; optional enhancement: only auto-scroll if user was already near bottom — implementer picks one approach and documents it).
- [x] Domain spec updated: [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) § Narration scroll behavior.

## Expected files

- `app/ui/panels/narration.py`
- `app/ui/app.py`
- `tmp/app-pygame-ui-spec.md`
- `app/tests/test_narration_scroll.py` — unit test rebuild + scroll offset (player, narration, error paths; headless pygame init)

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) controls/behavior + changelog.

## Notes

### Suggested implementation

1. Add `NarrationPanel.scroll_to_bottom_after_rebuild()` — call `_rebuild()` if `_dirty`, then set `_scroll_offset`.
2. Or set `_stick_to_bottom = True` on add; in `draw()` after `_rebuild()`, apply bottom scroll when flag set.
3. Replace `_smooth_scroll_to_bottom()` calls to use the fixed path (name is misleading today — it does not animate).

### Related

- [APP-059](app-059-standardize-creation-table-outputs.md) — taller tables make this bug more visible during creation.
- Wheel scroll (`MOUSEWHEEL` → `_scroll_velocity`) should remain independent for history reading.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-060 --task auto-scroll-narration
python tmp/backlog/claim_ticket.py release APP-060 --done
```
