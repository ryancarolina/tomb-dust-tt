# Spec: app-037-block-map-travel-during-creation

**Status:** draft (r2 — QA spec revision)
**backlog_ticket:** APP-037
**ticket_path:** tmp/backlog/app-037-block-map-travel-during-creation.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-pygame-ui-spec.md

## Problem

The right-sidebar map panel can submit `travel to {address}` on cell clicks (`app/ui/app.py` → `_submit`). During **Registry intake** (`creation.active`), the orchestrator already hard-gates exploration (APP-008): `process_turn` routes to `_creation_turn`, and `_execute_tool` rejects non-creation tools. Players still see a clickable map affordance with no explanation, which is confusing and will become worse when [APP-063](../../../app-063-map-ux-redesign-useful-navigation.md) adds hit-testing.

`GameBridge.status()` / `get_status()` does **not** expose `creation.active`. Gating only on `StatsPanel.update_from_status` or `awaiting` alone is insufficient — chips already read `orchestrator.creation.active` via `get_player_suggestions()` (APP-065).

## Goals

- Block **travel actions** (click → `travel to …` submit) while Registry intake is active or engine is in a creation-scoped desync state.
- Show player-facing hint: **"Finish Registry intake first"** (tooltip on hover over map; optional muted label under grid).
- **Keep map display** — 3×3 grid, fog, hub cell (`party.address`), location name, scene dots still render.
- **Re-enable** travel after creation finalize (`creation.active == false` and live delver / `PLAYER_ACTIONS`).
- Document behavior in `tmp/app-pygame-ui-spec.md` (Map panel + creation gate).
- Defense in depth: UI block + existing APP-008 engine gate.

## Non-goals

- Implementing full map click hit-testing (APP-063) — APP-037 gates even when `handle_click` is still a stub.
- Changing orchestrator exploration rules (APP-008).
- Blocking typed `travel to …` in the input box (orchestrator already rejects; optional follow-up).
- Map UX redesign (layout, zoom, path preview) — APP-063.
- Left character panel / inventory tabs — APP-062 (layout must survive narrowed map column).

## Requirements

### R1: Travel-blocked signal (orchestrator-side)

Introduce a single boolean used by map UI and `app.py` submit guard:

```python
def is_map_travel_blocked(self) -> bool:
    status = self.bridge.status()
    roster = status.get("roster") or []
    if self.creation.active:
        return True
    if status.get("awaiting") == "CHARACTER_CREATION" and not roster:
        return True
    return False
```

| Condition | Block travel? | Rationale |
|-----------|---------------|-----------|
| `creation.active == True` | Yes | Registry intake in progress |
| `awaiting == "CHARACTER_CREATION"` and empty `roster` | Yes | APP-017/066 desync guard (mirror APP-065 inactive-creation chip policy) |
| `creation.active == False` and `awaiting == "PLAYER_ACTIONS"` | No | Post-finalize surface play |
| `creation.active == False` and `awaiting == "CHARACTER_CREATION"` but non-empty `roster` | No | Resume edge; engine may still say creation — travel allowed |

**Acceptance criteria**

- [ ] `is_map_travel_blocked()` lives on `Orchestrator` in `app/gm/orchestrator.py` (not a duplicate helper in `app.py`).
- [ ] Unit test: active creation → `True`; post-finalize `PLAYER_ACTIONS` → `False`; `CHARACTER_CREATION` + empty roster + inactive creation → `True`.

### R2: Push blocked flag to UI each turn

On every enriched `("status", …)` enqueue (init + post-turn), also refresh map gate state:

| Option (pick one) | Detail |
|-------------------|--------|
| **A (preferred)** | Enrich status payload: `status["map_travel_blocked"] = orchestrator.is_map_travel_blocked()` before `put(("status", …))` |
| **B** | Separate queue message `("map_gate", {"blocked": bool, "hint": str})` |

`Sidebar.update_from_status` (or dedicated `update_map_gate`) forwards blocked + hint to `MapView.set_travel_blocked(blocked, hint=...)`.

**Acceptance criteria**

- [ ] Map gate refreshes on startup `_init_orchestrator` status push and after every `process_turn` (success or exception — same path as suggestions APP-065).
- [ ] On `_process_turn` exception, queue enriched status in `finally` alongside `_queue_turn_suggestions(turn_id)` — do not rely on the success-path push at L299–300 only. Extract a small helper (e.g. `_queue_turn_status(turn_id)`) that enriches `get_status()` with `map_travel_blocked` / hint and `put(("status", …))` if `turn_id == self._current_turn_id` and orchestrator is set; call from success path **and** `finally` (mirror APP-065 chip refresh).
- [ ] UI does not infer `creation.active` from narration footers.

### R3: App layer — never submit travel when blocked

In `app/ui/app.py` map click handler:

```python
map_addr = self.sidebar.handle_map_click(event.pos)
if map_addr and self._can_submit() and not self._map_travel_blocked():
    self._submit(f"travel to {map_addr}")
```

`_map_travel_blocked()` reads cached flag from last status/map_gate message (or calls orchestrator on main thread only if already synchronized).

**Acceptance criteria**

- [ ] With blocked flag true, non-`None` `map_addr` does not call `_submit`.
- [ ] With blocked flag false, behavior unchanged from today.

### R4: MapView — display on, travel off

`MapView` gains:

- `travel_blocked: bool = False`
- `travel_blocked_hint: str = "Finish Registry intake first"`
- `set_travel_blocked(blocked: bool, hint: str | None = None)`

**When blocked**

| Behavior | Detail |
|----------|--------|
| `handle_click` | Always `None` (even after APP-063 hit-test) |
| `draw` | Full grid still drawn; add semi-transparent overlay or desaturate cell fills (muted `TEXT_MUTED` overlay acceptable) |
| `handle_hover` | If cursor over map rect, set internal hover flag; `draw` blits hint text (small font) below grid or centered in map panel |
| Tooltip copy | Default **"Finish Registry intake first"** — ticket allows "or similar"; do not paraphrase in tests |

**When not blocked**

- Existing draw/click/hover behavior (stub click returns `None` until APP-063).

**Acceptance criteria**

- [ ] `draw` still renders title, 3×3 cells, location name, scene dots when `travel_blocked`.
- [ ] `handle_click` returns `None` when `travel_blocked` regardless of hit-test.
- [ ] Hover over map while blocked shows hint string (headless test can assert `travel_blocked_hint` / hover state without pygame display if helper extracted).

### R5: Sidebar wiring

`Sidebar`:

- `update_from_status(status)` — if `map_travel_blocked` in status (Option A), call `map.set_travel_blocked(...)`.
- `handle_map_click` — may short-circuit to `None` when `map.travel_blocked` before delegating (belt-and-suspenders with R3).

Resize via `_do_layout` (APP-062) must not clear blocked state — only `rect` changes.

**Acceptance criteria**

- [ ] Sidebar resize during creation keeps blocked overlay + hint.
- [ ] `party.address` updates still call `map.update_position` when blocked (hub cell visible).

### R6: Re-enable after finalize

After `_auto_finalize` / `creation.active = False` and engine transitions to surface play (`PLAYER_ACTIONS`, roster non-empty):

- Next status push sets `map_travel_blocked == False`.
- Overlay and hint removed; clicks may submit travel again (subject to APP-063 hit-test).

**Acceptance criteria**

- [ ] Integration or creation-flow test: post-finalize status → `is_map_travel_blocked()` false.
- [ ] Manual: complete Registry intake → map no longer greyed; travel click allowed when APP-063 returns address.

### R7: Domain spec sync

Update `tmp/app-pygame-ui-spec.md` § Map travel during creation (APP-037) with signal table, layers, hint copy, tests (PM delivers in same change set as this file).

**Acceptance criteria**

- [ ] Ticket AC "Compatible with APP-062" noted — map height formula unchanged; gate is visual state on `MapView`.
- [ ] Cross-reference APP-008 in `tmp/app-character-creation-spec.md` unchanged; one line in pygame-ui-spec pointing to engine gate is enough.

## File map (implementation)

| Path | Change |
|------|--------|
| `app/gm/orchestrator.py` | `is_map_travel_blocked()` (or equivalent) |
| `app/ui/app.py` | Status enrichment (init, success, `_process_turn` `finally` via `_queue_turn_status` or equivalent) + `_map_travel_blocked` guard on map click |
| `app/ui/panels/sidebar.py` | Forward blocked flag to `MapView` |
| `app/ui/panels/map_view.py` | `set_travel_blocked`, overlay, hover hint, gated `handle_click` |
| `tmp/app-pygame-ui-spec.md` | Behavior + tests + changelog on close |
| `app/tests/test_ui_map_creation_gate.py` | New — blocked helper + MapView gate (suggested) |

## Tests & commands

```bash
python -m pytest app/tests/test_ui_map_creation_gate.py -q
python -m pytest app/tests/test_ui_suggestions.py app/tests/test_creation_flow.py -q
```

Manual (until APP-063 hit-test): start new game → during creation, hover map → hint visible; verify no `travel to` in logs if click path mocked to return address.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-008 | Engine gate — UI mirrors, does not replace |
| APP-065 | Same dual-condition pattern for inactive creation desync |
| APP-062 | Sidebar layout — gate must survive resize |
| APP-063 | Map clicks — R4 must gate before/after hit-test lands |

## Batch coordination

Batch board: `batch-board-APP-020-APP-031-APP-037.md`. Independent of APP-063 impl order; land APP-037 first so gate exists when clicks go live.
