# Drift Check: app-091-map-hint-overlap-fix

**backlog_ticket:** APP-091  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) | was yes (draft changelog, no checklist row) | **Synced:** § Hint placement (APP-091) matches code; task checklist `[x]` APP-091; changelog **APP-091 done** |
| Run [`spec.md`](./spec.md) R1–R5 | no | Verified against `map_view.py`, `test_ui_map_creation_gate.py` |
| Ticket [`app-091-map-travel-block-hint-overlap-fix.md`](../../app-091-map-travel-block-hint-overlap-fix.md) | no | All AC checked; status `done`; Closed 2026-05-22 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **Draw inside overlay** — hint centered in grid `overlay_rect` | `_draw_travel_block_overlay` surface branch: `_wrap_hint_lines` + `_layout_hint_placements`; no `hint_outside` on surface path | yes |
| **Footer reserved** — `displayName` + scene line at `info_y` | `_draw_surface` blits footer L275–287 before overlay L289–291 | yes |
| **No footer-row hint** — surface path | Pre-fix `(x, grid_y + grid_h + 16)` removed; `_compute_surface_grid` shared via `_surface_grid_metrics` | yes |
| **Wrap on narrow column** | `_wrap_hint_lines` with `_HINT_PAD`; test at 240×320 forces multi-line wrap | yes |
| **Copy unchanged** | `travel_blocked_hint = "Finish Registry intake first"`; `test_map_view_default_hint_string` | yes |
| **Dungeon path** — no regression | `_draw_dungeon` → `hint_outside=(x, y + 4)` kwarg branch L360–363 | yes |
| **Gate behavior unchanged** | No orchestrator/app/sidebar edits; APP-037 tests pass | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Hover hint does not overlap `displayName` or scene line | ✓ hint inside `grid_rect`; `hint_rect.bottom < info_y` in `test_map_view_hint_blit_inside_overlay_not_footer_row` |
| Hint readable on narrow sidebar (APP-062) | ✓ word-wrap + vertical center; test forces `len(wrapped) >= 2` at 240×320 |
| Default hint string unchanged | ✓ `test_map_view_default_hint_string` |
| Unit test asserts hint outside footer row / inside overlay | ✓ `_travel_block_hint_rect` + `grid_rect.contains(hint_rect)` |
| Domain spec § + changelog on close | ✓ § Hint placement (APP-091); changelog **done**; checklist row added |

## Run spec R1–R5 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | Surface hint inside grid overlay; footer reserved; wrap | **PASS** |
| **R2** | Dungeon path no regression | **PASS** |
| **R3** | APP-037 gate unchanged | **PASS** |
| **R4** | Placement unit test fail-pre / pass-post | **PASS** |
| **R5** | Domain spec sync on close | **PASS** |

## Tests run

```bash
cd app; python -m pytest tests/test_ui_map_creation_gate.py tests/test_creation_flow.py -q
```

**Result:** 19 passed (3.97s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_ui_map_creation_gate.py` | 11 — blocked helper, MapView gate, hint placement, default copy, enrich, sidebar, exception status | ✓ |
| `app/tests/test_creation_flow.py` | 8 — APP-037 post-finalize regression | ✓ |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| Shared layout math | `_surface_grid_metrics` / `_travel_block_hint_rect` use same `_compute_surface_grid` as `_draw_surface` | ✓ |
| Shared draw + test layout | `_draw_travel_block_overlay` (surface) and `_travel_block_hint_rect` both call `_wrap_hint_lines` + `_layout_hint_placements` | ✓ |
| Footer draw order | `displayName` + scene blitted before `if self.travel_blocked: _draw_travel_block_overlay` | ✓ |
| Vertical centering | `_layout_hint_placements` centers block; test asserts `grid_rect.top <= hint_rect.centery <= grid_rect.bottom` | ✓ |
| Scope limited to Expected files | Only `map_view.py`, `test_ui_map_creation_gate.py`, domain spec touched | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog — **APP-091 done**
- [x] Spec ↔ code — no functional drift
- [ ] `python tmp/backlog/claim_ticket.py release APP-091 --done` — **orchestrator** (QA drift: not run per convention)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- **Non-blocking:** Headless geometry tests cover placement; live hover at `32-C` deferred to Stage 7 human playtest.
- **Dungeon draw test:** No automated dungeon travel-block blit test; surface-only repro per ticket; `hint_outside` API branch preserved.
- **Tall wrap edge case:** If wrapped hint exceeds overlay height, `grid_rect.contains(hint_rect)` would fail — unlikely at sidebar sizes; acceptable guard per qa-implementation-pass.
