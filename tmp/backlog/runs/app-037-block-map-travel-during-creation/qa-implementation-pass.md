# QA PASS: implementation — round 1

**Task:** app-037-block-map-travel-during-creation  
**backlog_ticket:** APP-037  
**ticket_path:** [tmp/backlog/app-037-block-map-travel-during-creation.md](../../app-037-block-map-travel-during-creation.md)  
**Round:** 1  
**domain_spec_creation:** synced (§ Map travel during creation in `tmp/app-pygame-ui-spec.md`; ticket AC ticks + `release APP-037 --done` deferred to close stage)

## Verdict

**PASS** — Orchestrator-owned travel-block signal, enriched status refresh (init + turn `finally`, exception path), three-layer UI gate (app submit guard, sidebar/MapView click short-circuit, overlay + hint), resize survival, and automated tests match spec R1–R6 and plan flows A–F.

## Automated tests

```text
python -m pytest app/tests/test_ui_map_creation_gate.py app/tests/test_ui_suggestions.py app/tests/test_creation_flow.py -q
...................................                                      [100%]
35 passed in 3.89s
```

| Module | Focus | Result |
|--------|-------|--------|
| `app/tests/test_ui_map_creation_gate.py` | 10 tests — `is_map_travel_blocked` truth table, MapView gated click + hint, enrich helper, sidebar forward/resize, exception-path status queue | ✓ |
| `app/tests/test_ui_suggestions.py` | APP-065 regression — turn `finally` refresh pattern unchanged | ✓ |
| `app/tests/test_creation_flow.py` | Post-finalize creation flow regression | ✓ |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| `is_map_travel_blocked()` on orchestrator | `orchestrator.py` L348–355 — exact dual-condition logic from spec R1 | ✓ |
| Status enrichment on init | `_init_orchestrator` L127–128 → `_enrich_status_for_ui` before `put(("status", …))` | ✓ |
| Finally-only enriched status (APP-065 parity) | `_process_turn` L320–322 — `_queue_turn_status` in `finally`; success-only raw status put removed | ✓ |
| Cached flag + click guard | `_map_travel_blocked_flag` cached L175; L72 `not self._map_travel_blocked()` | ✓ |
| Hint copy locked | `MAP_TRAVEL_BLOCKED_HINT = "Finish Registry intake first"`; default on `MapView` | ✓ |
| Resize survival | `Sidebar._do_layout` L31 re-applies cached block; `test_sidebar_resize_preserves_blocked` | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Map travel disabled during creation / desync | `is_map_travel_blocked()` + MapView/sidebar gated clicks + app submit guard | ✓ |
| Hint *"Finish Registry intake first"* | `MAP_TRAVEL_BLOCKED_HINT`; `test_map_view_default_hint_string` (exact string) | ✓ |
| Re-enable after finalize | `test_is_map_travel_blocked_post_finalize`; creation flow regression | ✓ |
| Map displays; travel actions blocked only | Grid draw unchanged; overlay in `_draw_travel_block_overlay`; `update_position` while blocked in sidebar | ✓ |
| APP-062 resize compatible | Cached `_map_travel_blocked` on sidebar; `_do_layout` re-applies after `MapView` recreation | ✓ |

## Spec R1–R7 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | `is_map_travel_blocked()` truth table | Method + 4 orchestrator unit tests | ✓ |
| **R2** | Enriched status init + turn refresh (incl. exception) | `_enrich_status_for_ui`, `_queue_turn_status`, `test_process_turn_exception_queues_enriched_status` | ✓ |
| **R3** | App skip `_submit` when blocked | L72 guard + cached flag from status queue | ✓ |
| **R4** | MapView display on, travel off, hover hint | `set_travel_blocked`, gated `handle_click`, overlay + `_hovering` hint blit | ✓ |
| **R5** | Sidebar forward + resize + position updates | `update_from_status`, `handle_map_click` short-circuit, resize test | ✓ |
| **R6** | Post-finalize unblock | `test_is_map_travel_blocked_post_finalize` | ✓ |
| **R7** | Domain spec sync | § Map travel during creation drafted; changelog row present — ticket still `in_progress` | ✓ (close hygiene) |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/gm/orchestrator.py` | `is_map_travel_blocked()` | ✓ |
| `app/ui/app.py` | Enrich status, `_queue_turn_status`, click guard, cache flag | ✓ |
| `app/ui/panels/map_view.py` | `set_travel_blocked`, overlay, hover hint, gated click | ✓ |
| `app/ui/panels/sidebar.py` | Forward flag, resize cache, click short-circuit | ✓ |
| `app/tests/test_ui_map_creation_gate.py` | 10 new tests | ✓ |
| `tmp/app-pygame-ui-spec.md` | § + changelog (done row pre-dated — update at release) | ✓ |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Finally-only status push** | Matches plan + APP-065; domain prose mentions “success path” separately — behavior equivalent. |
| **`_load_session` overlay lag** | No enriched status on resume; first turn `finally` refreshes gate (plan open Q2 — acceptable). |
| **App click guard unit test** | No mock returning non-`None` address through blocked sidebar; layers 2–4 return `None` today (APP-063 stub). App guard ready for hit-test. |
| **Draw regression** | No automated assert grid/title/scene dots visible under overlay; manual hover step in human-test plan. |
| **Close stage** | Ticket AC checkboxes still `[ ]`; run `release APP-037 --done` + confirm changelog date. |
| **Human playtest** | Hover hint blit placement not validated headless; defer to Stage 7. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-037 --done` (ticket AC ticks, changelog confirm).  
**Stage 7:** Manual creation-session map hover + verify no `travel to` in logs when APP-063 hit-test lands.
