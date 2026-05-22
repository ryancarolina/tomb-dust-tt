# Research Brief: APP-091-map-hint-overlap-fix

**Date:** 2026-05-22
**Question:** Why does the creation travel-block hover hint overlap the map footer labels, and what code paths must change to fix layout without altering APP-037 gate behavior?

**backlog_ticket:** APP-091
**ticket_path:** tmp/backlog/app-091-map-travel-block-hint-overlap-fix.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md), which owns `app/ui/**` per [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **PyGame UI**. APP-091 is a layout bugfix within the existing § Map travel during creation (APP-037) — hint placement only. No new domain file or registry row required; PM adds hint-placement bullets + changelog to the same spec section on close.

## Summary

During Registry intake, `MapView._draw_surface` draws the location footer (`displayName`, scene progress) **then** calls `_draw_travel_block_overlay` with `hint_y = grid_y + grid_h + 16` — the **same Y** as `displayName` (`info_y`). On hover, the hint `"Finish Registry intake first"` is blitted at `(x, hint_y)`, directly on top of e.g. **Breley Keep** at hub `32-C`.

APP-037 shipped overlay + hover hint AC but did not reserve separate layout rows. The domain spec says “hover shows hint” and “display preserved” but does not define hint vs footer placement — human playtest TC-3 (“below/near grid”) was ambiguous enough to pass while strings overlap.

Fix scope is **`map_view.py` layout/draw only** (plus a position assertion test). Orchestrator gate, enriched status, sidebar resize cache, and default hint string stay unchanged. Ticket suggests drawing the hint **inside** the muted grid overlay (centered, word-wrap if needed) — aligns with overlay rect already passed to `_draw_travel_block_overlay`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Bug — surface draw + hint Y | `app/ui/panels/map_view.py` L209–226, L278–291 | Shared `grid_y + grid_h + 16` for `displayName` and hover hint |
| Dungeon draw path (secondary) | `app/ui/panels/map_view.py` L269–276 | Overlay on content; hint at `y + 4` after address — creation uses surface mode at `32-C` |
| Sidebar → map block state | `app/ui/panels/sidebar.py` L16–17, L33, L46–52, L60–62 | Forwards `map_travel_blocked` / hint; `_do_layout` preserves flags on resize |
| Status enrich + click guard | `app/ui/app.py` L19, L69, L339–349 | `MAP_TRAVEL_BLOCKED_HINT`; hover via `sidebar.handle_hover`; not involved in overlap |
| Block signal (unchanged) | `app/gm/orchestrator.py` `is_map_travel_blocked()` | APP-037 — out of APP-091 scope |
| Unit tests | `app/tests/test_ui_map_creation_gate.py` | 10 tests — gate, hint string, enrich, resize; **no draw-position tests** |
| Domain spec | `tmp/app-pygame-ui-spec.md` § Map travel during creation (APP-037) | Documents overlay + hint; **no hint placement rule** yet |
| Parent ticket | `tmp/backlog/app-037-block-map-travel-during-creation.md` | Done 2026-05-22; AC did not require non-overlapping hint |
| Layout context | `tmp/backlog/app-062-…` | Future narrower sidebar — hint inside grid must wrap on short overlay width |

## Code-path traces

### Creation travel block — surface map draw (repro path)

1. Entry: `App.run` → `sidebar.draw` → `map.draw` → `_draw_surface` (`map_view.py:107–115, 117–226`).
2. Grid layout: `info_y = grid_y + grid_h + 16` (`L210`).
3. Footer: `displayName` blitted at `(x, info_y)` (`L211–213`); scene line at `info_y + name_height + 3` (`L214–222`).
4. When `travel_blocked`: `grid_rect = Rect(grid_x, grid_y, grid_w, grid_h)`; overlay fill on grid only (`L224–225, L285–288`).
5. Hover hint: `_draw_travel_block_overlay(..., hint_x=x, hint_y=grid_y + grid_h + 16)` (`L226`) → if `_hovering`, blit hint at `(hint_x, hint_y)` (`L289–291`) — **collides with step 3**.

### Hover signal

1. `App.run` `MOUSEMOTION` / move handling → `sidebar.handle_hover(pos)` (`app.py:69`).
2. `Sidebar.handle_hover` → `map.handle_hover` if point in map rect (`sidebar.py:60–62`).
3. `MapView.handle_hover` sets `_hovering = rect.collidepoint(pos)` (`map_view.py:99–100`) — full map panel, not grid-only.

### Status → blocked flag (unchanged by APP-091)

1. `_enrich_status_for_ui` adds `map_travel_blocked` + hint when `is_map_travel_blocked()` (`app.py:346–349`).
2. `Sidebar.update_from_status` → `map.set_travel_blocked` (`sidebar.py:46–52`).
3. Resize: `_do_layout` re-applies cached block flags (`sidebar.py:33, 71–73`) — existing test `test_sidebar_resize_preserves_blocked`.

### Dungeon path (out of creation repro, same helper)

1. `_draw_dungeon` builds `content_rect` overlay; calls `_draw_travel_block_overlay(screen, content_rect, x, y + 4)` (`L269–276`).
2. Hint Y is after address line, not grid footer — different layout; impl should avoid regressing if dungeon ever blocked.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) § Map travel during creation (APP-037) — overlay, hover hint, default copy; Layout (APP-062) says sidebar height formula unchanged.
- Parent: [`tmp/backlog/app-037-block-map-travel-during-creation.md`](../../app-037-block-map-travel-during-creation.md) — done; tooltip AC satisfied by visible copy, not placement.
- APP-037 human TC-3: “Hint text appears below/near grid” — did not assert non-overlap with `displayName`.
- Non-goals: [`tmp/backlog/app-063-map-ux-redesign-useful-navigation.md`](../../app-063-map-ux-redesign-useful-navigation.md) — full map UX redesign.
- [`AGENTS.md`](../../../AGENTS.md) — app change requires ticket + spec changelog on close.

## Tests & commands

```bash
# Current regression (10 passed 2026-05-22) — no layout assertions
python -m pytest app/tests/test_ui_map_creation_gate.py -q

# Post-impl (per ticket AC): add test that hint blit Y (or rect) stays outside
# location-label row — e.g. inside overlay_rect or y < info_y / y > scene row

# Manual repro (ticket)
cd app && python main.py
# new game → hover MAP during creation at 32-C → hint overlapped "Breley Keep"
```

**Test gap:** `test_map_view_default_hint_string` checks string only; no test calls `draw()` with `_hovering=True` or inspects blit coordinates.

## Risks & unknowns

- **Narrow sidebar (APP-062):** `cell_size = min(..., 60)`; overlay width ≈ `3 * cell_size`. Long hint inside grid may need multi-line wrap + vertical centering — verify at ~30% window width.
- **Footer reserve:** `_draw_surface` subtracts `60` from available height for footer (`L135`) — moving hint off footer row is fine; moving hint **below** footer would need height budget change.
- **Draw-order / readability:** Hint inside semi-transparent overlay (alpha 102) improves separation from `displayName` but muted-on-muted contrast should be checked in human playtest.
- **Dungeon blocked path:** Same `_draw_travel_block_overlay` API; surface fix should not break dungeon hint placement if travel block ever applies there.
- **Testability:** No existing pattern for pygame blit positions — may need helper (e.g. return hint rect from draw path) or mock `screen.blit` in unit test.
- **Scope creep:** APP-063 hit-testing, orchestrator gates, or hint copy changes are out of scope.

## Raw notes

- Collision coordinates (`map_view.py`):
  - `info_y = grid_y + grid_h + 16` (L210)
  - `_draw_travel_block_overlay(..., x, grid_y + grid_h + 16)` (L226)
- Hub repro: `32-C` `displayName` = `"Breley Keep"` in `build/data/av-grid/av-grid.json`.
- `_font_small` = Consolas `max(9, FONT_SIZE_SMALL - 2)` → 11px when `FONT_SIZE_SMALL=13`.
- Overlay covers grid only; hint currently drawn **outside** overlay bounds on footer row.
- APP-037 impl files match ticket Expected files; APP-091 Expected files ⊆ same map test + spec paths.
