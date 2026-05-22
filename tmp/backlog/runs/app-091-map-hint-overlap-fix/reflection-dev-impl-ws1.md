# Dev reflection — APP-091 WS1 (implementation)

**Ticket:** APP-091  
**Workstream:** layout-only MapView hint placement fix  
**Date:** 2026-05-22

## What was implemented

1. **`app/ui/panels/map_view.py`**
   - Added `_HINT_PAD` / `_HINT_LINE_GAP` module constants.
   - Extracted `_compute_surface_grid()` so `_draw_surface` and `_surface_grid_metrics()` share one layout formula (avoids drift per plan risk mitigation).
   - Added `_wrap_hint_lines`, `_layout_hint_placements`, `_travel_block_hint_rect` — shared layout path for draw + test.
   - Refactored `_draw_travel_block_overlay(screen, overlay_rect, *, hint_outside=None)`:
     - **Surface:** wrap + center hint inside `overlay_rect`.
     - **Dungeon:** `hint_outside=(x, y + 4)` preserves legacy single-line absolute blit.
   - Updated `_draw_surface` call — dropped footer-row `(x, info_y)` hint coords.
   - Updated `_draw_dungeon` call — uses `hint_outside=` kwarg.

2. **`app/tests/test_ui_map_creation_gate.py`**
   - Added `test_map_view_hint_blit_inside_overlay_not_footer_row` — asserts hint union rect is inside grid overlay, strictly above footer `info_y`, vertically centered; validates wrap helper produces ≥2 lines.

## Deviations / notes

- **Wrap assert font sensitivity:** At 240×320 with Consolas 11px, default hint width equals `grid_w - 12` exactly (168px) — one line, not two as plan math assumed. Test uses `wrap_w = max_w - 1` when hint fits in one line at `max_w`, forcing multi-line wrap without changing the 240px placement fixture. Documented in qa-plan-pass note 7.

## Out of scope (unchanged)

- APP-037 gate behavior, orchestrator, sidebar, app.py, theme.py, rich_text.py.
- Domain spec changelog — finalize on ticket close (R5).

## Test results

```text
python -m pytest app/tests/test_ui_map_creation_gate.py -v
11 passed
```

All 10 existing APP-037 tests green; new placement test passes.

## Manual follow-up

Human playtest at `32-C` during creation: hint inside grey grid overlay; "Breley Keep" + scene line legible below (contrast check per human-test-plan.md).
