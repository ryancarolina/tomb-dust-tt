# Reflection: QA — APP-091 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, domain spec checklist + changelog sync, ticket AC + close, `reflection-qa-drift.md`

## Completed

- Compared `MapView._draw_surface`, `_draw_travel_block_overlay`, `_travel_block_hint_rect`, and hint layout helpers against run `spec.md` R1–R5, domain § Hint placement (APP-091), and ticket AC.
- Ran `pytest tests/test_ui_map_creation_gate.py tests/test_creation_flow.py -q` — **19 passed**.
- Promoted domain spec changelog **APP-091 draft → done**; added task checklist row **APP-091 done**.
- Marked ticket AC checkboxes, Status `done`, Closed 2026-05-22.

## Self-critique

- Did not run PyGame human playtest (live hover at `32-C`, muted-on-muted contrast); deferred to Stage 7 per pipeline.
- Did not run `claim_ticket.py release APP-091 --done` — out of scope for drift subagent per prior run convention.
- Did not add automated dungeon travel-block hint test; surface path is ticket primary AC; dungeon branch preserved via `hint_outside` only.

## Did I miss anything?

- [x] Ticket scope / Expected files only
- [x] Domain spec / AGENTS.md drift policy
- [x] Code paths traced (surface overlay hint, footer reservation, wrap, dungeon kwarg branch)
- [x] Tests mapped to AC (11 unit + creation-flow regression)
- [ ] Human playtest — deferred to Stage 7
- [ ] `release --done` — orchestrator handoff

## Handoff

**Ready for:** Orchestrator `release APP-091 --done`, Stage 7 commit + `human-test-plan.md`  
**Escalate human if:** Hover hint still overlaps **Breley Keep** / scene line at `32-C` during creation, or APP-037 gate regresses (clicks submit travel while blocked)
