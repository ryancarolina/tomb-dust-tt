# Spec: app-091-map-hint-overlap-fix

**Status:** draft
**backlog_ticket:** APP-091
**ticket_path:** tmp/backlog/app-091-map-travel-block-hint-overlap-fix.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-pygame-ui-spec.md

## Summary

During Registry intake, hovering the sidebar map shows **"Finish Registry intake first"** at the same Y as the location `displayName` below the 3×3 grid (e.g. **Breley Keep** at `32-C`). APP-037 shipped overlay + hover hint but did not reserve separate rows. **APP-091** is a layout-only fix: draw the hint **inside** the muted grid overlay; keep footer labels always readable.

**Canonical behavior:** [tmp/app-pygame-ui-spec.md § Map travel during creation — Hint placement (APP-091)](../../../app-pygame-ui-spec.md#hint-placement-app-091)

## Problem

| Issue | Detail |
|-------|--------|
| **Shared row** | `_draw_surface` blits `displayName` at `grid_y + grid_h + 16`; `_draw_travel_block_overlay` blits hover hint at the same coordinates |
| **Player impact** | Registry intake hover hides current cell name on hub map |
| **Regression of** | APP-037 hover hint AC — copy visible but layout wrong |

## Goals

- Hover hint **does not overlap** `displayName` or scene-progress line during creation travel block.
- Hint remains readable on narrow sidebar map column (APP-062 layout).
- Default hint string unchanged: **"Finish Registry intake first"**.
- Unit test asserts hint blit positions stay outside the location-label row (or inside overlay rect only).
- Domain spec updated (PM draft; changelog finalized on close).

## Non-goals

- APP-037 gate behavior (`is_map_travel_blocked`, enriched status, gated click, overlay fill).
- APP-063 full map UX redesign (hit-testing, navigation).
- Hint copy changes, orchestrator changes, sidebar height formula changes.

## Requirements

### R1: Surface map — hint inside grid overlay

In `MapView._draw_surface`, when `travel_blocked` and `_hovering`:

| Rule | Detail |
|------|--------|
| **Overlay rect** | Keep existing `grid_rect = Rect(grid_x, grid_y, grid_w, grid_h)` semi-transparent fill |
| **Hint position** | Draw hint **inside** `grid_rect` — centered horizontally and vertically (multi-line OK) |
| **Footer untouched** | `displayName` and scene line drawn at `info_y = grid_y + grid_h + 16` and below **before** overlay; hint must not use that Y |
| **Wrap** | Word-wrap hint to overlay width minus padding when sidebar is narrow |

**Acceptance criteria**

- [ ] Manual repro fixed: `new game` → hover map at `32-C` during creation → **Breley Keep** legible; hint inside grey grid.
- [ ] `_draw_travel_block_overlay` no longer receives footer-row `hint_y` for surface path (refactor API if needed — e.g. draw hint from overlay rect only).

### R2: Dungeon path — no regression

`_draw_dungeon` uses a different overlay rect and hint Y (`y + 4` after address). Surface fix must not break dungeon hint if travel block ever applies there.

**Acceptance criteria**

- [ ] Dungeon draw path still calls overlay helper without surface footer collision (smoke: existing tests green).

### R3: Unchanged APP-037 behavior

No changes to: `is_map_travel_blocked()`, `_enrich_status_for_ui`, sidebar resize cache, `handle_click` gate, default hint string constant.

**Acceptance criteria**

- [ ] All existing `test_ui_map_creation_gate.py` tests pass without weakening assertions.

### R4: Placement unit test

Add test in `app/tests/test_ui_map_creation_gate.py` that asserts hint draw rect is **inside** grid overlay and **outside** footer label row — e.g. extract `hint_rect` helper from `_draw_travel_block_overlay` / `_draw_surface`, or mock `screen.blit` and inspect coordinates.

**Acceptance criteria**

- [ ] New test fails on pre-fix code (hint Y == `grid_y + grid_h + 16`) and passes after impl.
- [ ] Test covers `_hovering=True`, `travel_blocked=True`, surface draw path.

### R5: Domain spec sync on close

Mark ticket done; replace APP-091 draft changelog with **done** entry in `tmp/app-pygame-ui-spec.md`.

## File map

| Path | Change |
|------|--------|
| `app/ui/panels/map_view.py` | Hint layout inside grid overlay; refactor `_draw_travel_block_overlay` if needed |
| `app/tests/test_ui_map_creation_gate.py` | Hint placement assertion |
| `tmp/app-pygame-ui-spec.md` | § Hint placement (APP-091) — PM draft done; finalize changelog on close |

## Tests & commands

```bash
python -m pytest app/tests/test_ui_map_creation_gate.py -q
python -m pytest app/tests/test_creation_flow.py -q   # APP-037 regression
```

Manual: `cd app && python main.py` → new game → hover map during creation at `32-C`.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-037 | Parent — travel block + hint; APP-091 fixes layout only |
| APP-062 | Narrow sidebar — hint must wrap inside overlay |
| APP-063 | Out of scope — do not expand map UX |

## Pointers

- Research: [research-brief.md](research-brief.md)
- Parent spec: [APP-037 run spec](../app-037-block-map-travel-during-creation/spec.md)
- Collision site: `map_view.py` L210–226, L278–291
