# Reflection: Research — APP-091 map-hint-overlap-fix

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md

## Completed

- Read ticket APP-091, domain spec § APP-037, APP-037 ticket and human-test-plan, AGENTS.md registry rules.
- Traced `MapView._draw_surface` vs `_draw_travel_block_overlay` Y coordinates — confirmed identical `grid_y + grid_h + 16` for `displayName` and hover hint.
- Reviewed `test_ui_map_creation_gate.py` (10 tests, all green); mapped gap — no draw-position or overlap assertions.
- Verified sidebar resize/block forwarding and hover wiring in `app.py` / `sidebar.py`.
- Set `registry_gap: false` with app-master-spec PyGame UI row justification.

## Self-critique

- Did not run manual PyGame repro (`new game` + hover) — conclusion is from static code trace plus ticket report; overlap is deterministic from shared Y.
- Dungeon-path hint placement (`y + 4`) noted but not playtested; low priority for creation hub scenario.
- Did not measure exact pixel widths at APP-062 sidebar ratios — flagged as risk for in-overlay word wrap only.

## Did I miss anything?

- [x] Ticket scope / Expected files — layout fix in `map_view.py`, tests, spec § only
- [x] Domain spec / registry_gap / AGENTS.md — false; pygame-ui-spec owns behavior
- [x] Code paths not traced — orchestrator gate traced for “unchanged”; hover path covered
- [x] Tests or AC not mapped — AC #4 (position test) and current 10-test suite documented
- [ ] AV-GRID load in headless tests — MapView without `content_root` still uses default address `32-C` and empty `_addresses`; repro name comes from grid JSON when loaded via sidebar content_root in app — minor nuance for unit test setup

## Handoff

**Ready for:** PM spec draft (hint placement rule in § Map travel during creation; echo ticket AC; non-goals APP-063)
**Escalate human if:** PM wants hint below footer instead of inside overlay — may require changing the `available_h - 60` footer reserve in `_draw_surface`
