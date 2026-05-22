# Reflection: PM — APP-091 map-hint-overlap-fix

**Agent:** PM
**Round:** 1
**Deliverables:** spec.md, tmp/app-pygame-ui-spec.md (§ Hint placement APP-091), reflection-pm.md

## Completed

- Wrote run-local `spec.md` with R1–R5: inside-overlay hint placement, footer row reservation, dungeon non-regression, APP-037 behavior unchanged, placement unit test, domain spec sync on close.
- Updated `tmp/app-pygame-ui-spec.md`: APP-091 cross-ref on § Map travel during creation; new **Hint placement (APP-091)** subsection with placement table; Layers/Implementation files/Tests/File map aligned; draft changelog.
- Confirmed `registry_gap: false` — pygame-ui-spec owns layout; no new domain file.
- Run `spec.md` is summary + pointers only; long-form truth lives in domain spec § Hint placement.

## Self-critique

- **API shape left to Dev:** spec mandates inside-overlay placement but does not require removing `hint_x`/`hint_y` params from `_draw_travel_block_overlay` — Dev may refactor to rect-only hint draw or compute center from `overlay_rect` internally.
- **Testability:** no existing blit-position test pattern; R4 allows helper extraction or mock blit — QA plan should confirm test fails on current main before impl merges.
- **Contrast:** hint on semi-transparent overlay may need human playtest for muted-on-muted readability; not blocking for spec pass.

## Did I miss anything?

- [x] Ticket scope / Expected files — all three paths in spec file map
- [x] Domain spec / registry_gap / AGENTS.md — pygame-ui-spec only; APP-037 parent cited
- [x] Code paths traced — research-brief collision at L210/L226 reused
- [x] Tests or AC mapped — pytest module + manual repro from ticket
- [x] APP-062 narrow-column wrap called out in domain spec and R1

## Handoff

**Ready for:** QA spec gate (round 1)
**Escalate human if:** QA requires hint below footer (would need footer height budget change) or APP-063 scope creep
