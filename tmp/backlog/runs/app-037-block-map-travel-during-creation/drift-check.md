# Drift Check: app-037-block-map-travel-during-creation

**backlog_ticket:** APP-037  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) | was yes (open-work list still cited APP-037) | **Synced:** § Map travel during creation matches code; checklist `[x]` APP-037; open work trimmed; changelog **APP-037 done** confirmed |
| Run [`spec.md`](./spec.md) R1–R7 | no | Verified against `orchestrator.py`, `app.py`, `sidebar.py`, `map_view.py`, `test_ui_map_creation_gate.py` |
| Ticket [`app-037-block-map-travel-during-creation.md`](../../app-037-block-map-travel-during-creation.md) | no | All AC checked; status `done`; Closed 2026-05-22 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **Source** — `Orchestrator.is_map_travel_blocked()` | `orchestrator.py` L348–355 | yes |
| **Block when** — `creation.active` or `CHARACTER_CREATION` + empty roster | dual-condition in `is_map_travel_blocked()` | yes |
| **Do not block** — post-finalize / resume with roster | `test_is_map_travel_blocked_post_finalize`, `test_is_map_travel_blocked_resume_edge` | yes |
| **UI refresh** — init + turn `finally` enriched status | `_init_orchestrator` L127–128; `_queue_turn_status` in `_process_turn` `finally` L320–322 | yes |
| **Exception path** — status queue on error | `test_process_turn_exception_queues_enriched_status` | yes |
| **App guard** — skip `_submit` when blocked | L72 `not self._map_travel_blocked()`; flag cached L175 | yes |
| **MapView** — overlay, hint, gated click | `set_travel_blocked`, `_draw_travel_block_overlay`, `handle_click` L103–104 | yes |
| **Sidebar** — forward flag, resize cache, click short-circuit | `_map_travel_blocked` cache; `_do_layout` L31; `handle_map_click` L55–56 | yes |
| **Hint copy** — "Finish Registry intake first" | `MAP_TRAVEL_BLOCKED_HINT`; `MapView.travel_blocked_hint` default | yes |
| **Display preserved** — grid + party address while blocked | `draw` unchanged; `update_from_status` still calls `update_position` | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Map travel disabled during creation / creation-scoped desync | ✓ three-layer gate (orchestrator signal, MapView/sidebar, app submit guard) |
| Tooltip *"Finish Registry intake first"* | ✓ default hint + hover blit; `test_map_view_default_hint_string` |
| Re-enable after finalize | ✓ `test_is_map_travel_blocked_post_finalize`; creation-flow regression |
| Map displays; travel actions blocked only | ✓ overlay on grid; position updates while blocked |
| APP-062 resize compatible | ✓ sidebar cached flag survives `_do_layout`; `test_sidebar_resize_preserves_blocked` |

## Run spec R1–R7 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | `is_map_travel_blocked()` truth table on orchestrator | **PASS** |
| **R2** | Enriched status init + turn refresh (incl. exception) | **PASS** |
| **R3** | App skip `_submit` when blocked | **PASS** |
| **R4** | MapView display on, travel off, hover hint | **PASS** |
| **R5** | Sidebar forward + resize + position updates | **PASS** |
| **R6** | Post-finalize unblock | **PASS** |
| **R7** | Domain spec sync on close | **PASS** |

## Tests run

```bash
cd app; python -m pytest tests/test_ui_map_creation_gate.py tests/test_creation_flow.py -q
```

**Result:** 18 passed (3.49s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_ui_map_creation_gate.py` | 10 — blocked helper, MapView, enrich, sidebar, exception status | ✓ |
| `app/tests/test_creation_flow.py` | 8 — post-finalize regression | ✓ |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| Orchestrator owns signal | `is_map_travel_blocked()` in `orchestrator.py`; not duplicated in `app.py` | ✓ |
| Status enrichment helper | `_enrich_status_for_ui` adds `map_travel_blocked` / hint | ✓ |
| Finally parity with APP-065 | `_queue_turn_status` called from `_process_turn` `finally` | ✓ |
| No narration inference | Block reads `creation.active` + `bridge.status()` only | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog — **APP-037 done**
- [x] Spec ↔ code — no functional drift
- [ ] `python tmp/backlog/claim_ticket.py release APP-037 --done` — **orchestrator** (QA drift: not run per convention)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- **Non-blocking:** `_load_session` does not push enriched status immediately; first turn `finally` refreshes gate (documented in qa-implementation-pass).
- **APP-063:** `MapView.handle_click` still returns `None` when unblocked (hit-test stub); app submit guard is ready when APP-063 lands.
- **Human playtest:** Hover hint placement and overlay visibility deferred to Stage 7 `human-test-plan.md`.
- **Batch bleed:** Other hunks in `orchestrator.py` working tree are out of APP-037 scope; travel-block surface is isolated.
