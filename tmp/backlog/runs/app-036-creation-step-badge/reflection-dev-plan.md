# Reflection: Dev — APP-036 plan

**Agent:** Dev  
**Round:** 1  
**Deliverables:** plan.md, reflection-dev-plan.md

## Completed

- Read PASS spec (R1–R6), qa-spec-pass.md, research-brief.md, ticket Expected files, domain spec § Creation step badge (APP-036)
- Traced APP-037 enrichment path: `_enrich_status_for_ui` L341–349, `_queue_turn_status` L351–358, init push L127–128, exception test in `test_ui_map_creation_gate.py`
- Traced creation FSM vocabulary: `CREATION_STEPS` L20–31, `CREATION_STATUS_LABELS` L85–96 (footer tokens — not badge text)
- Traced orchestrator: `export_creation_state` L446–449, `is_map_travel_blocked` L348–355 as placement template for `get_creation_step_badge()`
- Traced StatsPanel: phase badge pattern L95–101; planned Registry pill **above** character name per spec R4
- Identified **resize hazard**: `Sidebar._do_layout` recreates `StatsPanel` — plan requires sidebar-level badge cache + re-apply (APP-037 map precedent)
- Mapped QA adversarial notes: resume refresh via turn `finally`; `WORLD_INTRO` hide when inactive; headless state tests OK
- Documented `MagicMock` regression in existing `test_enrich_status_for_ui_payload` once enrich calls `get_creation_step_badge()`
- Test matrix for `test_ui_creation_badge.py` aligned to spec suggested cases

## Self-critique

- **Sidebar in scope:** Ticket Expected files omit `sidebar.py`, but resize survival is an AC (R4/R5). Plan explicitly adds minimal cache wiring and flags as necessary — QA plan should accept or propose `stats.resize()` refactor instead.
- **Resume badge timing:** Plan defers immediate `_load_session` status push (same as APP-037 map overlay open question). If APP-018 restore path does not trigger turn `finally` before first paint, badge may be blank briefly — impl should verify with `test_creation_restore.py` and add load hook only if red.
- **Badge color:** Plan specifies `COLOR_CLERK` from theme; spec allows clerk green — exact RGB left to impl; no pixel tests.
- **Draw height during intake:** Badge adds a row at top when active; stats half height unchanged (`_do_layout` formula fixed). Long stat lists may clip slightly sooner during intake — acceptable for v1; no scroll in stats panel today.
- Did not run pytest (plan phase only).

## Did I miss anything?

- [x] Ticket scope / Expected files — all six ticket paths + sidebar resize wiring justified
- [x] Domain spec / registry_gap / AGENTS.md — UI reads orchestrator; no narration scrape; TurnTruth gate N/A (no LLM prose change)
- [x] Code paths traced — display map, helper, enrich extension, stats draw, resize, finalize hide, step advance
- [x] Tests / AC mapped — R1–R6, footer-token guard, exception path, regression commands
- [x] APP-037 / APP-065 / APP-066 / APP-062 cross-refs in plan

## Handoff

**Ready for:** QA plan PASS → workstreams → implementation (single stream; ~7 files)  
**Escalate human if:** Product wants badge in narration header instead of stats panel, or prefers showing raw step keys (`SKILLS`) instead of display map copy
