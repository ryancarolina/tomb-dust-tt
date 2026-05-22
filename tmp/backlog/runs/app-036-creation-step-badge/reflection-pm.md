# Reflection: PM — APP-036 creation-step-badge

**Agent:** PM
**Round:** 1
**Deliverables:** `spec.md`, `tmp/app-pygame-ui-spec.md` § Creation step badge, ticket Expected files update

## Completed

- Drafted run-local `spec.md` with six requirements mirroring APP-037 `_enrich_status_for_ui` / `_queue_turn_status` cadence.
- Resolved ticket AC wording tension: human labels via new `CREATION_STEP_DISPLAY` keyed by `creation.step`, explicitly **not** `CREATION_STATUS_LABELS` footer tokens (APP-065 alignment).
- Specified `Orchestrator.get_creation_step_badge()` and enriched keys `creation_step` / `creation_step_display`.
- Chose StatsPanel top placement (`Registry: {label}`) above character name; phase badge coexists below name.
- Updated domain spec with signal table, display map, implementation files, tests, changelog draft.
- Expanded ticket Expected files: `creation.py`, `orchestrator.py`, `test_ui_creation_badge.py`.

## Self-critique

- **Display map duplication:** `CREATION_STEP_DISPLAY` adds a third vocabulary alongside `CREATION_STEPS` and `CREATION_STATUS_LABELS`. Justified for player-facing copy vs drift footers, but impl must keep keys in sync when FSM changes — test coverage for full `CREATION_STEPS` coverage is specified.
- **`WORLD_INTRO` label:** Badge shows "Reception" only while `creation.active` is still true at that step; post-finalize badge hides before reception narration matters — edge case is brief; may need QA playtest note if step/active ordering surprises.
- **Headless draw tests:** Spec allows StatsPanel state tests without pygame display (like partial APP-037 coverage); full pixel draw may stay manual until richer panel test harness exists.
- **Character-creation spec:** Did not edit `app-character-creation-spec.md` — step truth already documented; display map ownership could be cross-linked on impl close if drift reviewers want it in both specs.

## Did I miss anything?

- [x] Ticket scope / Expected files — expanded per user request
- [x] Domain spec / registry_gap / AGENTS.md — pygame-ui-spec owns UI; no registry gap
- [x] Code paths not traced — research-brief covered; spec references enrich + export_creation_state
- [x] Tests or AC not mapped — `test_ui_creation_badge.py` matrix + regression commands
- [ ] APP-062 left panel shipped state — spec assumes current two-column layout; badge in stats region should survive; QA should verify after APP-062 lands

## Handoff

**Ready for:** QA spec review (adversarial round 1)
**Escalate human if:** Product wants narration-header badge instead of stats top, or prefers showing raw step keys (`SKILLS`) instead of display map copy
