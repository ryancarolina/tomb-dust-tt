# Reflection: Research — APP-060 auto-scroll-narration

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read ticket APP-060, domain spec `app-pygame-ui-spec.md`, dev-team templates.
- Traced `NarrationPanel` add → dirty → rebuild-in-draw → scroll offset lifecycle in `app/ui/panels/narration.py`.
- Traced `_process_ui_queue`, `_submit`, `_process_turn`, wheel scroll, error, and `_load_session` paths in `app/ui/app.py`.
- Confirmed root cause: `scroll_to_bottom()` runs on stale `_total_height` before `_rebuild()` in `draw()`.
- Documented secondary gaps (error path no scroll, load session no scroll, misnamed `_smooth_scroll_to_bottom`, dead `_target_scroll`).
- Set `registry_gap: false` with master-spec + pygame-ui ownership citation.
- Mapped test gap and suggested optional `test_narration_scroll.py` approach.

## Self-critique

- Did not run manual playtest in PyGame window — conclusion is from static trace only; frame-order analysis should be sufficient for this bug class but human playtest remains the acceptance gate.
- Did not measure typical `_total_height` deltas for creation tables; relied on ticket + APP-059 context.
- Near-bottom vs always-scroll policy left for PM — ticket AC explicitly defers to implementer/spec.

## Did I miss anything?

- [x] Ticket scope / Expected files — narration.py, app.py, pygame-ui spec, optional test file only
- [x] Domain spec / registry_gap / AGENTS.md — PyGame UI row owns `ui/**`; no new spec
- [x] Code paths not traced — covered queue, submit, turn worker, draw order, wheel, error, load
- [x] Tests or AC not mapped — error scroll gap noted; manual + optional unit test documented
- [ ] APP-036 in-flight changes to app.py — not read diff; batch board warns sequential close only

## Handoff

**Ready for:** PM spec draft (§ Narration scroll behavior, scroll policy choice, error-path AC)
**Escalate human if:** playtest shows a second root cause (e.g. scroll corrected then wheel velocity resets view) — not seen in code review
