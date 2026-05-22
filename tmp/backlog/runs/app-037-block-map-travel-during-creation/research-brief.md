# Research Brief: APP-037-block-map-travel-during-creation

**Date:** 2026-05-22
**Question:** How should the PyGame map panel block travel during character creation while keeping display and mirroring APP-008 engine gates?

**backlog_ticket:** APP-037
**ticket_path:** tmp/backlog/app-037-block-map-travel-during-creation.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md), which owns `app/ui/**` per [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **PyGame UI**. Map travel blocking, tooltip copy, and sidebar wiring are UI concerns; engine hard-gate remains in [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) / orchestrator (APP-008). No new domain spec file required.

## Summary

APP-037 adds a **UI defense-in-depth** layer: the right-sidebar map must not submit travel while Registry intake (`creation.active`) is in progress, with copy *"Finish Registry intake first"* and greyed/no-op interaction, while the 3×3 grid **still renders** (hub cell, fog, labels).

**Engine is already safe (APP-008):** `process_turn` routes to `_creation_turn` when `self.creation.active`; `_llm_loop` is blocked; `_execute_tool` rejects all tools except `set_creation_choice`. Typed `travel to …` during creation never reaches `world_travel`.

**UI gap today:** `app/ui/app.py` submits `travel to {map_addr}` on any non-`None` map click, but `MapView.handle_click` is a **stub** (always `None`) — clicks do nothing until [APP-063](../../../app-063-map-ux-redesign-useful-navigation.md). APP-037 should still gate `app.py` and add map disabled state + tooltip so behavior is correct when hit-testing lands.

**Creation flag is not on `get_status()`:** `Orchestrator.get_status()` returns `bridge.status()` only — no `creation.active`. Chips already read `orchestrator.creation.active` via `get_player_suggestions()`. Map gating should use the same orchestrator-side signal (or merge `export_creation_state()` into the UI `("status", …)` payload), not `StatsPanel.update_from_status` alone.

**Secondary block (ticket AC):** Also block when engine `awaiting == "CHARACTER_CREATION"` and `roster` is empty but `creation.active` is false (APP-017/066 desync), matching suggestion-chip policy in pygame-ui-spec.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Map click → travel submit | `app/ui/app.py` L68–71 | `handle_map_click` → `_submit(f"travel to {map_addr}")` if `_can_submit()` |
| Map widget | `app/ui/panels/map_view.py` | `handle_click`/`handle_hover` stubbed; `draw` renders 3×3 surface grid |
| Sidebar compose | `app/ui/panels/sidebar.py` | `update_from_status` → stats + map position from `party.address` |
| Status to UI | `app/ui/app.py` L172–173, L299–300 | `("status", orchestrator.get_status())` after init + each turn |
| Creation FSM | `app/gm/orchestrator.py` | `creation.active`, `export_creation_state()`, `_creation_turn` |
| Engine gate (APP-008) | `app/gm/orchestrator.py` L2188–2191, L2333–2341 | `_llm_loop` + `_execute_tool` creation guards |
| Suggestions pattern | `app/ui/suggestions.py`, `get_player_suggestions()` | `creation_active` param — template for map gate |
| Exploration spec (cross-ref) | `tmp/app-exploration-delve-spec.md` | Owns map travel UX long-term; APP-063 implements clicks |

## Code-path traces

### Map click → orchestrator (current)

1. Entry: `App.run` `MOUSEBUTTONDOWN` → `sidebar.handle_map_click(pos)` (`app/ui/app.py:68–71`).
2. `Sidebar.handle_map_click` → `MapView.handle_click` (`sidebar.py:43–45`).
3. **Today:** `handle_click` returns `None` (`map_view.py:94–95`) — no travel string, no `_submit`.
4. **When APP-063 adds hit-test:** non-`None` address → `_submit("travel to {addr}")` → `_process_turn` → `orchestrator.process_turn`.
5. If `creation.active`: `process_turn` returns at L895–896 → `_creation_turn` — exploration tools never run.

### Creation.active exposure to UI

1. `Orchestrator.get_status()` → `self.bridge.status()` only (`orchestrator.py:222–223`) — fields: `awaiting`, `roster`, `party`, etc.; **no** `creation.active`.
2. `Orchestrator.get_player_suggestions()` reads `self.creation.active` + `self.creation.step` (`orchestrator.py:225–238`).
3. `export_creation_state()` → `{active, step, …}` when `creation.active` (`orchestrator.py:314–317`); persisted in `session_state.json` (`app.py:416–418`) but **not** pushed on each turn to sidebar/map.
4. `Sidebar.update_from_status`: map position only if `party.address` (`sidebar.py:32–34`) — hub `32-C` still shows after `session_start` during creation (engine `party` exists, `roster` empty).

### APP-008 engine gate (reference)

1. `process_turn`: `if self.creation.active: return self._creation_turn(player_input)` (`orchestrator.py:895–896`).
2. `_llm_loop`: early return + log if `creation.active` (`orchestrator.py:2189–2191`).
3. `_execute_tool`: only `set_creation_choice` allowed when `creation.active` (`orchestrator.py:2333–2341`).

### Recommended UI gate (implementation hint — not spec)

1. **Signal:** `travel_blocked = orchestrator.creation.active OR (awaiting == "CHARACTER_CREATION" and not roster)` — mirror APP-065 inactive-creation guard.
2. **Push:** On each `("status", …)` in `app.py`, attach `creation` from `export_creation_state()` or a small `get_ui_creation_flags()` on orchestrator.
3. **Layers:** (a) `app.py` skip `_submit` for map when blocked; (b) `MapView`/`Sidebar` grey grid + tooltip on hover; (c) `handle_click` return `None` when blocked even after APP-063 hit-test.
4. **Re-enable:** After `_auto_finalize` sets `creation.active = False` (`orchestrator.py:1642` area) and live delver on surface — map travel allowed when not blocked.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) — Map row says click → travel; open work lists APP-037.
- Creation gate: [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) — no exploration while `creation.active` (APP-008).
- Related tickets: APP-008 (engine), APP-036 (creation badge — same creation signal gap), APP-062 (sidebar layout), APP-063 (map clicks stubbed).
- [`AGENTS.md`](../../../AGENTS.md) — app changes require ticket + domain spec changelog on close.

## Tests & commands

```bash
# Existing UI / creation regressions
python -m pytest app/tests/test_ui_suggestions.py app/tests/test_creation_flow.py -q

# After impl: add focused tests (suggested)
# app/tests/test_ui_map_creation_gate.py — MapView/Sidebar blocked flag + app gate helper
```

No headless map panel tests exist today (`app-pygame-ui-spec.md` lists manual map click only).

## Risks & unknowns

- **`creation.active` not in `bridge.status()`** — implementers must not gate only on `update_from_status(status)`; need orchestrator or enriched status payload.
- **Map clicks currently inert** — APP-037 AC is partly forward-looking; human playtest should verify gate once APP-063 enables clicks (or test `handle_click` + app gate with mocks).
- **Dual condition drift** — `creation.active` false + `awaiting CHARACTER_CREATION` + empty roster: must block (ticket); post-finalize `creation.active` false + `PLAYER_ACTIONS` must **not** block.
- **Tooltip infrastructure** — `handle_hover` is `pass`; need mouse-over label drawing (no existing map tooltip pattern).
- **Grey styling** — no `DISABLED` color in `theme.py`; use muted overlay or desaturate grid cells.
- **APP-062 layout** — map height is `rect.height - npc_h - stats_h`; blocking UI must survive sidebar resize.
- **Spec overlap** — `app-exploration-delve-spec.md` owns map travel UX; pygame-ui-spec should own creation-time **input block**; PM may add one cross-reference line, not a registry split.

## Raw notes

- `grep handle_click map_view` → always `return None` (confirmed APP-063 research).
- Ticket tooltip: *"Finish Registry intake first"* (or similar).
- `WORLD_INTRO` with `not creation.active` auto-routes `process_turn("look around")` (`orchestrator.py:1185–1186`) — post-intake travel should be allowed.
- Batch board: `batch-board-APP-020-APP-031-APP-037.md`.
