# Reflection: Research — APP-036 creation-step-badge

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md

## Completed

- Read backlog ticket APP-036, domain spec `app-pygame-ui-spec.md`, and dev-team `templates.md`.
- Traced `CreationState`, `CREATION_STATUS_LABELS`, `export_creation_state()`, and `format_creation_status()` in `app/gm/creation.py` and `app/gm/orchestrator.py`.
- Traced UI status queue: `_enrich_status_for_ui`, `_queue_turn_status`, `Sidebar.update_from_status`, `StatsPanel.update_from_status` in `app/ui/app.py` and panel modules.
- Compared APP-037 map gate (done), APP-065 chip policy (done), APP-035 stats engine read (done), APP-066 awaiting contract, and APP-062 layout ticket (open).
- Set `registry_gap: false` with app-master-spec PyGame UI row justification.
- Documented label vocabulary tension (step keys vs footer tokens vs APP-065 blocklist) for PM.

## Self-critique

- Did not run pytest or launch PyGame — code traces are static reads only; line numbers may drift slightly but symbols were verified in-repo.
- Display copy recommendation is deliberately left open; assumed ticket examples (`RACE`, `SKILLS`) mean FSM step names formatted for humans, not literal `CREATION_STATUS_LABELS` values — PM should confirm.
- APP-062 character panel absence confirmed via glob, but did not read full `app.py` draw order for a narration-header alternative — stats placement is a recommendation, not a measured layout prototype.

## Did I miss anything?

- [x] Ticket scope / Expected files — covered `sidebar.py`, `stats.py`, `app.py`, domain spec
- [x] Domain spec / registry_gap / AGENTS.md — false gap; pygame-ui-spec owner cited
- [x] Code paths not traced — orchestrator export, UI enrich, stats draw, suggestions guard, APP-037 template
- [x] Tests or AC not mapped — listed existing pytest targets + suggested new module
- [ ] Live playtest of current UI during creation — out of scope for research; human-test-plan is Stage 7

## Handoff

**Ready for:** PM spec draft (`spec.md` in run folder) — resolve display label map, exact placement (stats vs narration header), and enrich payload field names
**Escalate human if:** Product wants footer tokens (`SKILLS_INPUT`) visible in sidebar — conflicts with APP-065 internal-token policy and chip blocklist
