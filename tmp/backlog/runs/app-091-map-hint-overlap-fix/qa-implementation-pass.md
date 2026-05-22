# QA PASS: implementation — round 1

**Task:** app-091-map-hint-overlap-fix  
**backlog_ticket:** APP-091  
**ticket_path:** [tmp/backlog/app-091-map-travel-block-hint-overlap-fix.md](../../app-091-map-travel-block-hint-overlap-fix.md)  
**Round:** 1  
**domain_spec_creation:** synced (§ Hint placement APP-091 drafted in `tmp/app-pygame-ui-spec.md`; ticket AC ticks + `release APP-091 --done` deferred to close stage)

## Verdict

**PASS** — Surface-map hover hint is drawn inside the muted grid overlay (wrap + center), footer `displayName` / scene rows are reserved, dungeon path preserved via `hint_outside`, APP-037 gate behavior unchanged, and placement unit test matches spec R1–R5.

## Automated tests

```text
python -m pytest app/tests/test_ui_map_creation_gate.py -v
11 passed in 2.22s
```

| Test | Focus | Result |
|------|-------|--------|
| `test_is_map_travel_blocked_*` (4) | APP-037 orchestrator truth table | ✓ |
| `test_map_view_click_blocked_returns_none` | Gated click unchanged | ✓ |
| `test_map_view_hint_blit_inside_overlay_not_footer_row` | **APP-091** — hint rect inside grid, above `info_y`, vertical center, wrap ≥2 lines | ✓ |
| `test_map_view_default_hint_string` | Default copy unchanged | ✓ |
| `test_enrich_status_for_ui_payload` | Enriched status unchanged | ✓ |
| `test_sidebar_update_from_status_forwards_block` | Sidebar forward unchanged | ✓ |
| `test_sidebar_resize_preserves_blocked` | Resize cache unchanged | ✓ |
| `test_process_turn_exception_queues_enriched_status` | Exception-path status unchanged | ✓ |

**Regression (spec command):**

```text
python -m pytest app/tests/test_creation_flow.py -q
8 passed in 1.75s
```

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Hover hint does not overlap `displayName` or scene line | `_draw_travel_block_overlay(screen, grid_rect)` — no footer-row Y; footer blitted before overlay; `hint_rect.bottom < info_y` in new test | ✓ |
| Hint readable on narrow sidebar (APP-062) | `_wrap_hint_lines` with `_HINT_PAD`; test at 240×320 forces `len(wrapped) >= 2` | ✓ |
| Default hint string unchanged | `travel_blocked_hint = "Finish Registry intake first"`; `test_map_view_default_hint_string` | ✓ |
| Unit test asserts hint outside footer row / inside overlay | `test_map_view_hint_blit_inside_overlay_not_footer_row` via `_travel_block_hint_rect` + `_surface_grid_metrics` | ✓ |
| Domain spec § + changelog | § Hint placement (APP-091) L134–148; changelog draft L361 — finalize on `release --done` | ✓ (close hygiene) |

## Spec R1–R5 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Surface hint inside grid overlay; footer reserved; wrap | `_compute_surface_grid`, `_wrap_hint_lines`, `_layout_hint_placements`; surface path calls overlay without footer coords | ✓ |
| **R2** | Dungeon path no regression | `_draw_dungeon` → `hint_outside=(x, y + 4)`; existing suite green | ✓ |
| **R3** | APP-037 gate unchanged | No orchestrator/app/sidebar edits; all 10 pre-existing tests pass | ✓ |
| **R4** | Placement unit test fail-pre / pass-post | `_travel_block_hint_rect` helper shared with draw path; rect assertions + wrap stress | ✓ |
| **R5** | Domain spec sync on close | PM draft in domain spec; ticket still `in_progress` | ✓ (close hygiene) |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/ui/panels/map_view.py` | Extract `_compute_surface_grid`; wrap/center hint inside overlay; refactor `_draw_travel_block_overlay` API (`hint_outside` kwarg); `_travel_block_hint_rect` test helper | ✓ |
| `app/tests/test_ui_map_creation_gate.py` | +1 test `test_map_view_hint_blit_inside_overlay_not_footer_row` | ✓ |
| `tmp/app-pygame-ui-spec.md` | § Hint placement (APP-091) + draft changelog (not in impl diff — pre-drafted) | ✓ |

## Code trace highlights

| Check | Evidence | Result |
|-------|----------|--------|
| Shared layout math | `_surface_grid_metrics` / `_travel_block_hint_rect` call same `_compute_surface_grid` as `_draw_surface` | ✓ |
| Shared draw + test layout | Both `_draw_travel_block_overlay` (surface branch) and `_travel_block_hint_rect` use `_wrap_hint_lines` + `_layout_hint_placements` | ✓ |
| Footer draw order | `displayName` + scene line blitted before `if self.travel_blocked: _draw_travel_block_overlay` | ✓ |
| No footer-row hint on surface | Pre-fix `_draw_travel_block_overlay(..., x, grid_y + grid_h + 16)` removed | ✓ |
| Vertical centering | `_layout_hint_placements` centers block in overlay; test asserts `grid_rect.top <= hint_rect.centery <= grid_rect.bottom` | ✓ |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Manual repro** | Headless tests cover geometry; live hover at `32-C` deferred to Stage 7 human playtest. |
| **Contrast / readability** | Muted-on-muted inside semi-transparent overlay — no color token change; human eyeball recommended. |
| **Dungeon draw test** | No automated dungeon travel-block blit test; surface-only repro per ticket; API branch preserved. |
| **Tall wrap edge case** | If wrapped hint exceeds overlay height, `grid_rect.contains(hint_rect)` would fail — unlikely at sidebar sizes; acceptable guard. |
| **Wrap assert font sensitivity** | `len(wrapped) >= 2` depends on Consolas 11px metrics; same dummy-SDL pattern as existing map tests. |
| **Close stage** | Ticket AC checkboxes still `[ ]`; run `release APP-091 --done` + promote changelog draft → done row. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-091 --done`.  
**Stage 7:** Manual `new game` → hover map at `32-C` during creation — confirm **Breley Keep** and scene line legible; hint inside grey grid.
