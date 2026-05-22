# Implementation Plan: APP-037-block-map-travel-during-creation

**Status:** draft  
**backlog_ticket:** APP-037  
**ticket_path:** tmp/backlog/app-037-block-map-travel-during-creation.md  
**domain_spec:** tmp/app-pygame-ui-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add a **single orchestrator-owned travel-block signal** (`is_map_travel_blocked`) and push it to the UI on every status refresh (init + turn `finally`, mirroring APP-065). Three defense layers:

1. **Orchestrator** — boolean from `creation.active` + engine desync guard (same dual condition as APP-065 chips).
2. **UI submit + MapView** — no `travel to …` submit; `handle_click` → `None`; muted overlay + hover hint while grid still draws.
3. **Engine (APP-008)** — unchanged; UI does not replace `_creation_turn` / `_execute_tool` gates.

**Option A (preferred):** enrich `get_status()` dict with `map_travel_blocked` (+ optional `map_travel_blocked_hint`) before every `("status", …)` queue put — no separate `map_gate` message type.

**Resize hazard:** `Sidebar._do_layout` recreates `MapView` on every `resize()` — blocked state must live on `Sidebar` (or be re-applied from last enriched status) so APP-062 window resize does not drop the overlay mid-creation.

**Out of scope:** APP-063 hit-testing, typed input travel, orchestrator exploration rules, domain spec changelog (finalize on ticket close per R7 — PM draft already in domain spec).

---

## Code-path traces (current → planned)

### Flow A — `is_map_travel_blocked()` (new, orchestrator)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:get_status` | L222–223: `return self.bridge.status()` | unchanged |
| 2 | same (new) | — | **`is_map_travel_blocked()`** after `get_status` / near `get_player_suggestions` (L225) |
| 3 | new method | — | `status = self.bridge.status()`; `roster = status.get("roster") or []` |
| 4 | same | — | `if self.creation.active: return True` |
| 5 | same | — | `if status.get("awaiting") == "CHARACTER_CREATION" and not roster: return True` |
| 6 | same | — | `return False` |

**Truth table (must match spec R1 + APP-065 L95–96):**

| `creation.active` | `awaiting` | `roster` | Block? |
|-------------------|------------|----------|--------|
| True | any | any | Yes |
| False | `CHARACTER_CREATION` | `[]` | Yes (desync guard) |
| False | `CHARACTER_CREATION` | non-empty | No (resume edge) |
| False | `PLAYER_ACTIONS` | non-empty | No (post-finalize) |

**Related orchestrator paths (unchanged, reference only):**

| Step | File:symbol | L | Role |
|------|-------------|---|------|
| Route creation input | `process_turn` | L895–896 | `if self.creation.active: return self._creation_turn(...)` |
| Block LLM explore | `_llm_loop` | L2189–2191 | early return when `creation.active` |
| Block tools | `_execute_tool` | L2333–2341 | only `set_creation_choice` when `creation.active` |
| Finalize clears flag | `_auto_finalize` | L1642–1643 | `creation.active = False`; `step = WORLD_INTRO` |
| Reconcile sets flag | `_sync_creation_from_status` | L301–312 | empty roster + `CHARACTER_CREATION` → `creation.active = True` |

**Chip parity:** `build_player_suggestions` L95–96 returns `[]` when `awaiting == "CHARACTER_CREATION" and not creation_active` — map block uses the **inverse** (block travel when that desync holds).

---

### Flow B — Status enrichment + refresh (APP-065 parity)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `app.py:_init_orchestrator` | L125–126: raw `get_status()` → `put(("status", status))` | **`_enrich_status_for_ui(status)`** before put |
| 2 | `app.py:_process_turn` try | L299–300: raw status put on success only | **Remove** raw put; keep `map_update` in try using enriched or fresh `get_status()` |
| 3 | `app.py:_process_turn` except | L315–318: error put; `return` — **no status refresh** | unchanged except `finally` now refreshes status |
| 4 | `app.py:_process_turn` finally | L319–320: `_queue_turn_suggestions` only | **Add** `_queue_turn_status(turn_id)` |
| 5 | `app.py` (new) | — | `_enrich_status_for_ui(status) -> dict` copies status, sets `map_travel_blocked`, hint when blocked |
| 6 | `app.py` (new) | — | `_queue_turn_status(turn_id)` — guard `turn_id == _current_turn_id` + orchestrator; `put(("status", enriched))` |
| 7 | `app.py:_process_ui_queue` | L172–173: `sidebar.update_from_status(data)` | Also **`self._map_travel_blocked = bool(data.get("map_travel_blocked"))`** |
| 8 | `app.py:_load_session` | L456–465: direct map position patch; **no status queue** | Optional follow-up: queue enriched status after sync — **not required by R2** (next turn `finally` refreshes) |

**Planned `_process_turn` status refresh (pseudocode):**

```python
MAP_TRAVEL_BLOCKED_HINT = "Finish Registry intake first"

def _enrich_status_for_ui(self, status: dict) -> dict:
    if not self._orchestrator:
        return status
    out = dict(status)
    blocked = self._orchestrator.is_map_travel_blocked()
    out["map_travel_blocked"] = blocked
    if blocked:
        out["map_travel_blocked_hint"] = MAP_TRAVEL_BLOCKED_HINT
    return out

def _queue_turn_status(self, turn_id: int) -> None:
    if turn_id != self._current_turn_id or not self._orchestrator:
        return
    try:
        status = self._enrich_status_for_ui(self._orchestrator.get_status())
    except Exception:
        return
    self._ui_queue.put(("status", status))

def _process_turn(self, text, turn_id):
    narration = None
    try:
        ...
        narration = self._orchestrator.process_turn(text)
        ...
        self._ui_queue.put(("narration_text", narration))
        # map_update unchanged — party from get_status()
        status = self._orchestrator.get_status()
        party = status.get("party")
        if party and party.get("address"):
            self._ui_queue.put(("map_update", {...}))
    except Exception as exc:
        if turn_id == self._current_turn_id:
            self._ui_queue.put(("error", str(exc)))
        return
    finally:
        self._queue_turn_suggestions(turn_id)
        self._queue_turn_status(turn_id)
        ...
```

- **`except return` preserved** — TTS/`turn_idle` still skipped on error; `finally` runs first → status + suggestions refresh on exception (fixes L299–300 success-only gap).
- **Success path:** UI queue order ≈ `narration_text` → `map_update` → (`suggestions`, `status`) from `finally` — map position then gate flag is fine.
- **Stale turn_id** early returns inside `try` before `process_turn`: `_queue_turn_status` no-ops (same guard as APP-065).

---

### Flow C — Map click → travel submit (three layers)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `app.py:run` MOUSEBUTTONDOWN | L68–71 | `if map_addr and self._can_submit() and not self._map_travel_blocked():` |
| 2 | `app.py` (new) | — | `_map_travel_blocked() -> bool` returns cached `self._map_travel_blocked` (default False until first status) |
| 3 | `sidebar.py:handle_map_click` | L43–45 | **If** `self.map.travel_blocked`: return `None` before delegate |
| 4 | `map_view.py:handle_click` | L94–95: always `None` (APP-063 stub) | **If** `self.travel_blocked`: return `None`; else existing stub / future hit-test |
| 5 | `app.py:_submit` | L250+ | unchanged — never reached when gated |
| 6 | Engine | `process_turn` L895+ | unchanged APP-008 backstop if gate bypassed |

**Future APP-063:** hit-test returns address → layer 1 still blocks `_submit`; layer 3–4 return `None`.

---

### Flow D — MapView display + hover hint

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `map_view.py:__init__` | L46–61 | Add `travel_blocked=False`, `travel_blocked_hint="Finish Registry intake first"`, `_hovering=False` |
| 2 | same (new) | — | `set_travel_blocked(blocked, hint=None)` |
| 3 | `handle_hover` | L91–92: `pass` | If `pos` in `self.rect`: set `_hovering=True`; else False (always track for hint when blocked) |
| 4 | `draw` / `_draw_surface` | L107–212 | After grid + name + scene dots: if `travel_blocked`, blit semi-transparent overlay on grid area (`TEXT_MUTED` tint ~40% alpha) |
| 5 | same | — | If `travel_blocked and _hovering`: render `travel_blocked_hint` below grid (reuse `_font_small`, `TEXT_MUTED`) |
| 6 | `update_position` | L74–86 | unchanged — hub cell updates while blocked |
| 7 | `resize` | L88–89 | unchanged — only `rect` |

**Dungeon mode:** apply same overlay/hint pattern in `_draw_dungeon` when blocked (creation is surface-only today; cheap symmetry).

---

### Flow E — Sidebar wiring + resize survival

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `sidebar.py:update_from_status` | L30–34 | After stats: read `map_travel_blocked`, optional `map_travel_blocked_hint`; call `map.set_travel_blocked(...)`; **cache** on `self._map_travel_blocked` / `_map_travel_blocked_hint` |
| 2 | `update_from_status` | L32–34 | **`update_position` still runs** when `party.address` present (blocked or not) |
| 3 | `_do_layout` | L18–28 | After new `MapView(...)`: **`map.set_travel_blocked(self._map_travel_blocked, self._map_travel_blocked_hint)`** |
| 4 | `resize` | L48–50 | unchanged formula (`npc_h`, `stats_h`, `map_h`) |

---

### Flow F — Re-enable after finalize

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `_auto_finalize` | `creation.active = False` (L1642) |
| 2 | Next `_process_turn` `finally` | `_queue_turn_status` → `map_travel_blocked=False` |
| 3 | `MapView.draw` | No overlay; `handle_click` obeys APP-063 only |
| 4 | `app.py` map click | `_map_travel_blocked()` false → submit allowed |

---

## Task breakdown

### 1. `Orchestrator.is_map_travel_blocked()` — `app/gm/orchestrator.py`

Add method per spec R1 (exact logic). Place adjacent to `get_player_suggestions()` (~L225).

No changes to `get_status()` return shape at source — enrichment happens in `app.py` only.

---

### 2. Status helpers — `app/ui/app.py`

1. Module-level or class constant: `MAP_TRAVEL_BLOCKED_HINT = "Finish Registry intake first"`.
2. `__init__`: `self._map_travel_blocked = False`.
3. Implement `_enrich_status_for_ui`, `_queue_turn_status`, `_map_travel_blocked`.
4. Wire `_init_orchestrator` init push through `_enrich_status_for_ui`.
5. Refactor `_process_turn`: remove L299–300 status put; add `_queue_turn_status` in `finally` next to `_queue_turn_suggestions`.
6. Update `_process_ui_queue` `"status"` branch to cache `_map_travel_blocked`.
7. Guard map click at L68–71 per R3.

---

### 3. `MapView` gate UI — `app/ui/panels/map_view.py`

1. State + `set_travel_blocked`.
2. Gated `handle_click`.
3. `handle_hover` hover flag.
4. Overlay + hint in `draw` (surface + dungeon).
5. Use existing theme colors (`TEXT_MUTED`, `BG_SIDEBAR`) — no new `theme.py` tokens required.

---

### 4. `Sidebar` forward + resize — `app/ui/panels/sidebar.py`

1. Cache blocked fields on sidebar instance.
2. `update_from_status` forwards to map + cache.
3. `handle_map_click` short-circuit when blocked.
4. `_do_layout` re-applies cached gate after `MapView` recreation.

---

### 5. Tests — `app/tests/test_ui_map_creation_gate.py` (new)

| Test | Covers |
|------|--------|
| `test_is_map_travel_blocked_active_creation` | `creation.active=True` → True |
| `test_is_map_travel_blocked_desync_guard` | inactive + `CHARACTER_CREATION` + empty roster → True |
| `test_is_map_travel_blocked_resume_edge` | inactive + `CHARACTER_CREATION` + roster → False |
| `test_is_map_travel_blocked_post_finalize` | Run `INPUTS` from `test_creation_flow` → False at end |
| `test_map_view_click_blocked_returns_none` | Headless: `set_travel_blocked(True)`; `handle_click` → None |
| `test_map_view_default_hint_string` | Default hint equals ticket copy (exact string) |
| `test_enrich_status_for_ui_payload` | App helper adds keys when orchestrator mocked blocked |
| `test_sidebar_update_from_status_forwards_block` | Status dict → `map.travel_blocked` |
| `test_sidebar_resize_preserves_blocked` | `update_from_status` blocked → `resize` → map still blocked |
| `test_process_turn_exception_queues_enriched_status` | Mock `process_turn` raise; assert `("status", {...})` with `map_travel_blocked` in queue (extend APP-065 pattern) |

Use `orchestrator` fixture from `conftest.py`; pygame dummy driver for App tests (see `test_ui_suggestions.py`).

---

### 6. Domain spec — `tmp/app-pygame-ui-spec.md`

PM draft complete (§ Map travel during creation). **Impl:** no prose edits unless behavior diverges; append changelog date on **`release APP-037 --done`** only.

---

## Files (must ⊆ ticket Expected files)

| Path | Change |
|------|--------|
| `app/gm/orchestrator.py` | `is_map_travel_blocked()` |
| `app/ui/app.py` | Enrich status, `_queue_turn_status`, click guard, cache |
| `app/ui/panels/map_view.py` | `set_travel_blocked`, overlay, hover hint, gated click |
| `app/ui/panels/sidebar.py` | Forward flag, resize re-apply, click short-circuit |
| `app/tests/test_ui_map_creation_gate.py` | New unit/integration tests |
| `tmp/app-pygame-ui-spec.md` | Changelog on close only |

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| Focused | `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | All new tests green |
| Regression | `python -m pytest app/tests/test_ui_suggestions.py app/tests/test_creation_flow.py -q` | No regressions |
| Manual (post-APP-063 or mock) | New game → hover map during NAME step | Hint visible; no `travel to` in logs on click |

---

## Rollback / flags

- Pure UI + one orchestrator helper — no config flag.
- Rollback: revert six files; engine APP-008 gate remains safe without UI overlay.

---

## Open questions

1. **Double status on success** — Plan uses `finally`-only status push (not success + finally). Matches APP-065 chip pattern; QA should confirm single refresh is acceptable.
2. **`_load_session` status push** — Not in R2 AC; first turn after load refreshes gate. Add enriched status in `_load_session` only if QA plan requires immediate overlay on resume mid-creation.
3. **APP-036 overlap** — Enriched status may later carry `creation_step` for badge; same Option A payload — no conflict.

---

## Implementation order

1. `is_map_travel_blocked` + unit tests (orchestrator table).
2. `MapView` + `Sidebar` (testable without full App loop).
3. `app.py` enrichment, `_queue_turn_status`, click guard, exception-path test.
4. Full pytest suite; manual hover check during creation.
5. Ticket close: domain changelog + `release APP-037 --done`.
