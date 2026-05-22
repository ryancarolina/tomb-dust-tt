# Reflection: PM — APP-036 creation-step-badge (r2)

**Agent:** PM
**Round:** 2 (QA plan revision)
**Deliverables:** ticket Expected files, `spec.md` (r2), `reflection-pm-r2.md`

## Completed

- **TICKET-001:** Added `app/ui/panels/sidebar.py` to ticket Expected files with APP-037 mirror note (cache + re-apply badge on `_do_layout`). Run `spec.md` § R4 and § File map no longer treat sidebar as optional — resize survival is required for R4 AC.
- **PLAN-002:** Added `app/tests/test_ui_map_creation_gate.py` to ticket Expected files; run spec documents mandatory one-line mock fix (`get_creation_step_badge.return_value = None`) in `test_enrich_status_for_ui_payload` so enrich regression does not fail after `_enrich_status_for_ui` calls the new helper.
- **Spec sync:** Added `test_sidebar_resize_preserves_creation_badge` to suggested test matrix; file map lists both sidebar cache work and map-gate mock fix.

## Self-critique

- Did not edit `tmp/app-pygame-ui-spec.md` § Implementation files in this round — domain spec already states resize must not drop badge state; ticket/run spec now name `sidebar.py` explicitly. Dev may add domain file-map row on impl close if drift reviewers want parity with ticket list.
- Sidebar cache field names (`_creation_step_display` vs reusing status dict keys) left to Dev — spec describes behavior, not exact attribute names.
- Mock fix scope is minimal (one test, one line) but ticket-listed anyway so backlog hooks allow the edit in the same PR as enrich changes.

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 + PLAN-002 resolved (eight app paths + domain spec)
- [x] Domain spec / registry_gap / AGENTS.md — run spec aligned; domain spec unchanged this round (no registry gap)
- [x] Code paths — `Sidebar._do_layout` recreates `StatsPanel`; APP-037 `_map_travel_blocked` cache pattern cited
- [x] Tests or AC mapped — resize test + map-gate mock fix on ticket and in run spec § File map / test matrix
- [x] QA plan round 1 blockers — both findings addressed

## Handoff

**Ready for:** QA plan re-review (round 2)

**Escalate human if:** QA wants domain spec § Implementation files updated before impl (sidebar + map-gate test rows) or rejects sidebar cache as out of scope for APP-036
