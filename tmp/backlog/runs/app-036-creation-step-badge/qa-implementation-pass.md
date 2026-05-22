# QA PASS: implementation — round 1

**Task:** app-036-creation-step-badge  
**backlog_ticket:** APP-036  
**ticket_path:** [tmp/backlog/app-036-creation-step-badge-in-ui.md](../../app-036-creation-step-badge-in-ui.md)  
**Round:** 1  
**domain_spec:** synced — § Creation step badge (APP-036) in `tmp/app-pygame-ui-spec.md`; checklist `[x]` + changelog **done** row present

## Verdict

**PASS** — Engine-sourced creation step badge via `_enrich_status_for_ui`; step-keyed display labels separate from footer tokens; StatsPanel render + sidebar resize cache; automated tests green.

## Automated tests

```text
cd app && python -m pytest tests/test_ui_creation_badge.py tests/test_ui_map_creation_gate.py tests/test_creation_flow.py -q
...........................                                              [100%]
27 passed in 4.86s
```

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_ui_creation_badge.py` | display map, helper, enrich, panel, sidebar resize, exception path | ✓ 9 |
| `app/tests/test_ui_map_creation_gate.py` | enrich regression (`get_creation_step_badge.return_value = None`) | ✓ 10 |
| `app/tests/test_creation_flow.py` | full creation FSM regression | ✓ 8 |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| Badge source is orchestrator, not narration | `_enrich_status_for_ui` → `get_creation_step_badge()` in `app/ui/app.py` L350–356 | ✓ |
| No narration scrape for badge | No `creation_step` / `Awaiting:` parse in `stats.py`, `sidebar.py`, or badge enrich path | ✓ |
| Display labels ≠ footer tokens | `test_creation_step_display_covers_all_steps` asserts no overlap with `CREATION_STATUS_LABELS.values()` | ✓ |
| Init + turn `finally` enrich cadence | `_init_orchestrator` L127; `_process_turn` `finally` L321–323 → `_queue_turn_status` | ✓ |
| Map-gate mock fix applied | `test_enrich_status_for_ui_payload` + `test_process_turn_exception_queues_enriched_status` set `get_creation_step_badge.return_value = None` | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Visible badge during `creation.active` with human label | `CREATION_STEP_DISPLAY` + `StatsPanel.draw` `Registry: {label}`; `test_stats_panel_shows_badge_from_status` | ✓ |
| Badge hidden post-finalize / live roster | `get_creation_step_badge` returns `None` when `creation.active == False`; `test_get_creation_step_badge_inactive` | ✓ |
| Data from orchestrator / engine — never narration scrape | `get_creation_step_badge()` reads `creation.active` + `creation.step`; enrich on status queue only | ✓ |
| Placement compatible with APP-062 layout | Badge at top of `StatsPanel` in sidebar stats half; `test_sidebar_resize_preserves_creation_badge` | ✓ |

## Spec R1–R6 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | `CREATION_STEP_DISPLAY` step-keyed; ≠ footer tokens | `creation.py` L98–109; invariant test | ✓ |
| **R1** | Unknown step title-case fallback | `format_creation_step_display`; `test_format_creation_step_display_fallback` | ✓ |
| **R2** | `get_creation_step_badge()` on orchestrator | `orchestrator.py` L385–389 | ✓ |
| **R2** | Active → `{step, display_label}`; inactive → `None` | `test_get_creation_step_badge_active` / `_inactive` | ✓ |
| **R3** | Enrich keys on every status push (init + turn success/exception) | `_enrich_status_for_ui`; `test_enrich_status_for_ui_creation_fields`; `test_process_turn_exception_queues_creation_badge` | ✓ |
| **R4** | StatsPanel top badge; clear when `None` | `stats.py` L95–104; show/clear tests | ✓ |
| **R4** | Sidebar resize preserves badge | `sidebar.py` cache + re-apply in `_do_layout`; resize test | ✓ |
| **R5** | APP-062 layout — stats region, draw-only | `_do_layout` height formula unchanged; badge is panel state | ✓ |
| **R6** | Domain spec sync | `tmp/app-pygame-ui-spec.md` § Creation step badge; checklist L283; changelog L342 | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/gm/creation.py` | `CREATION_STEP_DISPLAY`, `format_creation_step_display` | ✓ |
| `app/gm/orchestrator.py` | `get_creation_step_badge()` | ✓ |
| `app/ui/app.py` | Extend `_enrich_status_for_ui` | ✓ |
| `app/ui/panels/stats.py` | Badge state + `Registry:` render | ✓ |
| `app/ui/panels/sidebar.py` | Badge cache + resize re-apply | ✓ |
| `app/tests/test_ui_creation_badge.py` | 9 unit tests | ✓ |
| `app/tests/test_ui_map_creation_gate.py` | Mock `get_creation_step_badge.return_value = None` | ✓ |
| `tmp/app-pygame-ui-spec.md` | § Creation step badge + changelog | ✓ |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **`test_creation_flow.py`** | Regression only — no explicit `creation_step_display` asserts; inactive-badge logic covered in dedicated module tests. |
| **`test_creation_restore.py`** | Spec lists as optional regression for resume badge; not in round-1 command — recommend Stage 6 or human playtest. |
| **`test_enrich_status_for_ui_payload`** | Sets badge mock to `None` but does not assert `creation_step*` keys — enrich still correct; optional hardening. |
| **Ticket backlog checkboxes** | AC boxes in `app-036-creation-step-badge-in-ui.md` still `[ ]` — update on `release APP-036 --done`. |
| **Human playtest** | Live PyGame badge visibility / step advance not run in QA; defer to Stage 7 `human-test-plan.md`. |
| **Headless draw** | Badge draw path not pixel-tested; state + enrich paths covered. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-036 --done` (ticket AC ticks).  
**Stage 7:** Manual new-game → step advance → finalize badge hide; mid-creation resume per run spec.
