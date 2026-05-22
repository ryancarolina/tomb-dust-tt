# Reflection: PM — APP-065 suggestion-chips (r2)

**Agent:** PM
**Round:** 2 (QA spec revision)
**Deliverables:** `spec.md` (r2), `tmp/app-pygame-ui-spec.md`, ticket Expected files, `reflection-pm-r2.md`

## Completed

- **TICKET-001:** Extended ticket Expected files with `app/ui/suggestions.py` and `app/tests/test_ui_suggestions.py`; aligned run `spec.md` Affected paths.
- **SPEC-001:** Documented equipment objection chip as **non-confirm** path (`not is_equipment_confirm`) matching `orchestrator.py` ~1004–1008; removed AC requiring `EQUIPMENT_OBJECTION_RE` match; added unit-test guidance to avoid wrong regex extension.
- **SPEC-002:** Clarified lookup when `creation.active` is false — ignore stale `creation.step`; `CHARACTER_CREATION` awaiting row → `[]` when inactive; post-finalize chips from engine `awaiting` only.
- **SPEC-003:** R1 now requires suggestion refresh on `_process_turn` exception (finally / before early return), not only success path.
- **SPEC-004:** Domain spec Tests § lists APP-065 pytest commands; file map adds `tests/test_ui_suggestions.py`.

## Self-critique

- Error-path refresh placement left to Dev (`finally` vs duplicated call in except) — acceptable; AC is outcome-based (queue receives update).
- Did not add explicit `creation_active` parameter to `build_player_suggestions` signature in spec — test plan uses it conceptually; Dev may gate in orchestrator only (simpler).
- `CHARACTER_CREATION` + inactive + resume desync still returns `[]` — correct per ticket (no chips mid-creation after desync without active flag); edge case may need follow-up if product wants recovery chips.

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 resolved
- [x] Domain spec / registry_gap / AGENTS.md — pygame-ui spec synced; no new domain file
- [x] Code paths — equipment handler, finalize `active=False`, except path cited
- [x] Tests or AC mapped — new cases for inactive creation, non-confirm, error path
- [x] QA round 1 blockers — all four findings addressed (SPEC-004 minor included)

## Handoff

**Ready for:** QA spec re-review (round 2)

**Escalate human if:** Product wants `CHARACTER_CREATION` + inactive to show recovery chips (not in ticket AC) or wants `EQUIPMENT_OBJECTION_RE` expanded to match chip phrase (explicitly out of scope).
