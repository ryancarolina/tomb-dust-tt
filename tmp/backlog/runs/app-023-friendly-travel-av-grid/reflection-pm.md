# Reflection: PM — APP-023 friendly-travel-av-grid

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-exploration-delve-spec.md` § APP-023, `reflection-pm.md`

## Completed

- Wrote run-local [spec.md](./spec.md) with problem/goals, R1–R7 summary, AC mapping, T1–T6, affected paths, playtest hints, pointers.
- Added durable behavior to [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md): § **Friendly surface travel resolution (APP-023)** — exit-scoped surface-only candidates, scoring table (`displayName` + `tradeRoute`), error codes (`AMBIGUOUS_ADDRESS`, `USE_ENTER_DUNGEON`), wiring for `world_travel` + `process_beat`, test matrix.
- Addressed research risks explicitly:
  - **Exit-scoped matching** — mandatory; no global grid scan.
  - **beat.py parity** — R6 + ticket Expected-files gap called out for Dev plan.
  - **Ambiguity** — tie → `AMBIGUOUS_ADDRESS` + `options`, no travel.
  - **UG vs enter_dungeon** — surface filter drops layered exits; layered-only intent → `USE_ENTER_DUNGEON`.
- Updated domain spec problem strikethrough, tests bullet, file map, open work, changelog (PM draft entry).

## Self-critique

- **`USE_ENTER_DUNGEON` error code** is new — not verified against existing engine error enums; Dev may prefer folding into `UNKNOWN_ADDRESS` with message-only hint. Spec allows either if message directs to `enter_dungeon`.
- **`tradeRoute` score 80** is PM-chosen; not validated against all grid cells with overlapping route names on adjacent exits.
- Did not draft `app-gamebridge-spec.md` bridge method bullets — deferred to ticket close per usual drift workflow.
- CLI parity (`cmd_world.py`) noted optional only; QA may ask for symmetry in plan review.

## Did I miss anything?

- [x] Ticket scope / Expected files — flagged `beat.py` gap for Dev
- [x] Domain spec / registry_gap / AGENTS.md — single owner, no new spec file
- [x] Code paths — world_travel, process_beat, site_resolve contrast, map unchanged
- [x] Tests or AC mapped — T1–T6 + pytest commands
- [ ] Exact `USE_ENTER_DUNGEON` vs message-only — Dev/QA may refine during plan QA

## Handoff

**Ready for:** QA spec review (adversarial) — round 1  
**Escalate human if:** Product wants UG addresses reachable via `world_travel` friendly names (conflicts with enter_dungeon split)
