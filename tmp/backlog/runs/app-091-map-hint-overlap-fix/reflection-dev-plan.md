# Reflection: Dev — APP-091 plan

**Agent:** Dev  
**Round:** 1  
**Deliverables:** plan.md, reflection-dev-plan.md

## Completed

- Read ticket APP-091, PASS spec (R1–R5), qa-spec-pass.md, research-brief.md, domain spec § Hint placement (APP-091)
- Traced surface draw collision at `map_view.py` L210–226 and overlay helper L278–291 — confirmed shared `grid_y + grid_h + 16` for `displayName` and hover hint
- Traced hover path (`app.py` → `sidebar.handle_hover` → `MapView.handle_hover`) and status/enrich path — confirmed out of scope
- Traced dungeon branch L269–276 — planned `hint_outside=` kwarg to preserve absolute hint at `(x, y + 4)`
- Designed refactor: wrap + center inside `overlay_rect`; optional absolute hint for dungeon; testable `_travel_block_hint_rect` + `_surface_grid_metrics`
- Mapped narrow-sidebar wrap math (`240px` panel → `grid_w=180`, 2+ lines for default hint)
- Specified new test `test_map_view_hint_blit_inside_overlay_not_footer_row` with fail-pre/pass-post contract

## Self-critique

- **Layout helper drift:** `_surface_grid_metrics` duplicates `_draw_surface` math unless impl extracts `_compute_surface_grid` — plan recommends shared helper but leaves choice to impl agent; QA should verify metrics match live draw.
- **Contrast/readability:** Plan defers muted-on-muted legibility to human playtest; no fallback (e.g. `TEXT_PRIMARY` hint) specified — intentional scope lock per R3.
- **Dungeon regression coverage:** No automated dungeon travel-block draw test; R2 relies on unchanged `hint_outside` branch + existing suite green — acceptable per ticket surface-only repro.
- **Rich-text reuse:** Chose inline word-wrap over `render_wrapped_line` to avoid StyledSpan/font triple dependency in map panel — small duplication trade-off documented.
- Did not run pytest (plan phase only).

## Did I miss anything?

- [x] Ticket scope / Expected files — three paths only; no orchestrator/sidebar/app edits
- [x] Domain spec / registry_gap / AGENTS.md — layout-only; changelog on close; PM draft § Hint placement aligned
- [x] Code paths traced — surface collision, hover, status (unchanged), dungeon non-regression branch
- [x] Tests / AC mapped — placement test inside overlay + outside footer row; wrap assert on narrow width; existing 10 tests preserved
- [x] APP-037 / APP-062 / APP-063 cross-refs — parent gate unchanged; narrow wrap; no APP-063 scope

## Handoff

**Ready for:** QA plan PASS → implementation (single stream; 3 Expected files)  
**Escalate human if:** Hint unreadable inside overlay after impl — product may want contrast tweak (new ticket) or hint below footer (requires height budget change)
