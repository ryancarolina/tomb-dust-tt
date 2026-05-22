# Dev reflection — APP-036 implementation (ws1)

**Ticket:** APP-036  
**Agent:** Dev  
**Date:** 2026-05-22

## What was implemented

1. **`CREATION_STEP_DISPLAY` + `format_creation_step_display()`** in `app/gm/creation.py` — player-facing badge labels separate from `CREATION_STATUS_LABELS` footer tokens; title-case fallback for unknown slugs.
2. **`Orchestrator.get_creation_step_badge()`** — returns `{"step", "display_label"}` when `creation.active`; `None` when inactive (desync guard: stale step + `CHARACTER_CREATION` awaiting still hides badge).
3. **`app.py` status enrichment** — extended `_enrich_status_for_ui` with `creation_step` / `creation_step_display`; same init + turn `finally` cadence as APP-037.
4. **`StatsPanel`** — `creation_step_display` state; `Registry: {label}` pill at panel top using `COLOR_CLERK`; phase badge unchanged below name.
5. **`Sidebar` resize cache** — caches creation badge fields on `update_from_status`; unconditionally re-applies after `_do_layout` (mirrors APP-037 map-block pattern; clears correctly when both cached values are `None`).
6. **Tests** — 9 cases in `test_ui_creation_badge.py`; map-gate enrich mocks fixed for `get_creation_step_badge.return_value = None`.
7. **Domain spec** — changelog + checklist marked done.

## Deviations / notes

- **Sidebar re-apply:** Plan pseudocode gated re-apply on non-None cache; implemented unconditional re-apply so post-finalize `None` cache survives resize (same as map block always calling `set_travel_blocked`).
- **`_load_session`:** No immediate enriched status push on resume (per plan open Q1 — deferred; next init/turn `finally` carries badge).
- **Stats on resize:** Pre-existing APP-037 behavior — full roster stats still reset on resize until next status push; only badge + map block are cached.

## Verification

```text
python -m pytest app/tests/test_ui_creation_badge.py app/tests/test_ui_map_creation_gate.py -v  → 19 passed
```

## TurnTruth gate

No LLM narration paths touched — N/A for APP-036.

## Risks for QA

- Resume mid-creation before first post-load status push may briefly show no badge (same class of gap as APP-037 map gate).
- Manual: confirm badge shows `Registry: Name` at new game, advances with steps, disappears after finalize; never shows `SKILLS_INPUT` or other footer tokens.
