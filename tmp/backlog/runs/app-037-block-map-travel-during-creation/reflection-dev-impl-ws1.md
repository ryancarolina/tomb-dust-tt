# Dev reflection — APP-037 implementation (ws1)

**Ticket:** APP-037  
**Agent:** Dev  
**Date:** 2026-05-22

## What was implemented

1. **`Orchestrator.is_map_travel_blocked()`** — dual-condition block signal (`creation.active` OR desync guard) per spec R1 truth table.
2. **`app.py` status enrichment** — `_enrich_status_for_ui`, `_queue_turn_status` in `_process_turn` `finally` (APP-065 parity); removed success-only raw status put; init path enriched; click guard via `_map_travel_blocked()`.
3. **`MapView`** — `set_travel_blocked`, gated `handle_click`, hover tracking, semi-transparent overlay + hint on surface/dungeon draw.
4. **`Sidebar`** — forwards blocked flag from status; caches on instance for `_do_layout` resize survival; belt-and-suspenders click short-circuit.
5. **Tests** — 10 cases in `test_ui_map_creation_gate.py` covering orchestrator table, MapView, sidebar resize, enrich helper, exception-path status queue.
6. **Domain spec** — changelog entry for APP-037 done.

## Deviations / notes

- **Naming:** Plan used `self._map_travel_blocked` for both cached bool and method. Implemented cache as `_map_travel_blocked_flag` to avoid shadowing the `_map_travel_blocked()` guard method.
- **`_load_session`:** No enriched status push on resume (per plan open Q2 — deferred; first turn `finally` refreshes gate).
- **Finally-only status:** Success path no longer pushes raw status; single enriched push from `finally` matches APP-065 chip pattern.

## Verification

```text
python -m pytest app/tests/test_ui_map_creation_gate.py -v  → 10 passed
python -m pytest app/tests/test_ui_suggestions.py app/tests/test_creation_flow.py -q  → 25 passed
```

## TurnTruth gate

No LLM narration paths touched — N/A for APP-037.

## Risks for QA

- Hover hint blit placement is headless-tested via state only; manual hover check during creation recommended.
- Resume mid-creation before first post-load turn may briefly show unblocked map until `_queue_turn_status` runs.
