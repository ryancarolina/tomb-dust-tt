# Research Brief: APP-060-auto-scroll-narration

**Date:** 2026-05-22
**Question:** Why does narration fail to auto-scroll after player submit and GM response despite `_smooth_scroll_to_bottom()` calls? What is the correct fix point (rebuild-before-scroll vs deferred tail-follow)?

**backlog_ticket:** APP-060
**ticket_path:** tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md), which owns `app/ui/**` and already references APP-060 in the Narration panel row and open-work list. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **PyGame UI** maps to that spec. All Expected files (`app/ui/panels/narration.py`, `app/ui/app.py`, optional `app/tests/test_narration_scroll.py`) fall under that owner. PM will add a dedicated **Narration scroll behavior** section per ticket AC — no new domain spec file required.

## Summary

The UI **does** call auto-scroll on every narration queue event (`narration`, `narration_text`, `player`), but scroll runs **before layout rebuild**. `NarrationPanel.add_line` / `add_lines` only append to `self.lines` and set `_dirty = True`; `_rebuild()` (which recomputes `_total_height` from wrapped text, markdown, and tables) runs exclusively inside `draw()` when `_dirty` is true. `scroll_to_bottom()` sets `_scroll_offset` from the **previous** `_total_height`, so after `draw()` rebuilds with taller content the offset is too small — the viewport stays mid-history. The bug is most visible on long GM replies and creation markdown tables (APP-059), where the height delta between stale and fresh layout is large. `_smooth_scroll_to_bottom()` is a misnomer: it is an instant `scroll_to_bottom()` with no animation; `_target_scroll` on `App` is unused dead state. Secondary gaps: `error` queue handler adds a line but does not scroll; `_load_session` restores lines with `_dirty = True` but never requests bottom scroll.

**Recommended fix:** defer bottom pinning until `_total_height` is current — either `scroll_to_bottom_after_rebuild()` (rebuild-if-dirty then set offset) or a `_follow_tail` / `_stick_to_bottom` flag cleared in `draw()` after `_rebuild()`. Wire `_process_ui_queue` (and error path) through the fixed API. Document scroll policy (always follow on new content vs only when user was near bottom) in domain spec § Narration scroll behavior.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Narration model + layout | `app/ui/panels/narration.py` | Deferred `_rebuild()`; `scroll_to_bottom()` uses `_total_height` |
| Rich layout (wrap, tables) | `app/ui/rich_text.py` | Tables add many surfaces → large height jumps |
| Main loop + queue drain | `app/ui/app.py` | Frame order: queue → wheel momentum → `draw()` |
| Scroll trigger | `app/ui/app.py` | `_process_ui_queue` L163–171; `_smooth_scroll_to_bottom` L225–226 |
| Player submit | `app/ui/app.py` | `_submit` queues `player`; worker queues `narration_text` |
| Wheel scroll | `app/ui/app.py` | `MOUSEWHEEL` → `_scroll_velocity`; `_update_scroll` → `narration.scroll()` |
| Session restore | `app/ui/app.py` | `_load_session` appends lines, sets `_dirty`, no scroll |
| Domain spec (intent) | `tmp/app-pygame-ui-spec.md` | Narration row claims auto-scroll; open work APP-060 |
| Tests today | — | No `NarrationPanel` / scroll unit tests; `test_ui_map_creation_gate.py` shows pygame init pattern |

## Code-path traces

### Frame lifecycle (root cause)

1. Entry: `App.run` main loop (`app/ui/app.py:54–97`).
2. `_process_ui_queue()` drains thread-safe queue (orchestrator / worker threads → main thread).
3. On `narration` / `narration_text` / `player`: `add_lines` or `add_line` → `_dirty = True` → `_smooth_scroll_to_bottom()` → `narration.scroll_to_bottom()`.
4. `scroll_to_bottom()` (`narration.py:72–73`): `_scroll_offset = max(0, _total_height - rect.height + 40)` using **pre-add** `_total_height`.
5. `_update_scroll(dt)` applies wheel momentum only (`app.py:212–217`); does not correct auto-scroll.
6. `narration.draw()` (`narration.py:161–163`): if `_dirty`, `_rebuild()` recomputes `_rendered` and `_total_height` from all `self.lines` — **does not adjust `_scroll_offset`**.
7. Blit uses stale `_scroll_offset` → latest lines/tables below visible area.

```text
add_line(s) → _dirty=True → scroll_to_bottom(stale height) → … → draw() → _rebuild(new height) → blit(old offset)
```

### Player submit → GM response

1. Entry: Enter / chip click → `_submit(text)` (`app.py:253–271`).
2. Queues `("processing", …)` then `("player", text)` — no scroll on processing.
3. Same or next frame: `_process_ui_queue` handles `player` → `add_line(..., "player")` + scroll (stale).
4. Worker `_process_turn` (`app.py:273–336`) → `orchestrator.process_turn(text)`.
5. On success: `("narration_text", narration)` — single string, often multi-paragraph + tables.
6. `_process_ui_queue` handles `narration_text` → `add_line(..., "narrator")` + scroll (stale again).
7. `draw()` rebuilds full history; offset still reflects height **before** GM block → user must wheel-scroll.

### Startup narration (lower severity)

1. Entry: `_init_orchestrator` thread pushes multiple `("narration", [...])` batches (`app.py:132–148`).
2. All processed in one `_process_ui_queue` pass before first `draw()`; each batch calls scroll with `_total_height == 0` until first rebuild.
3. Welcome copy often fits viewport → bug less obvious at boot; same mechanism.

### Error path (AC gap)

1. Entry: `_process_ui_queue` `msg_type == "error"` (`app.py:202–204`).
2. `add_line(f"[Error: {data}]", "narrator")` — **no** `_smooth_scroll_to_bottom()`.
3. AC requires scroll after error; implementer should add scroll via fixed API.

### Manual wheel scroll (regression guard)

1. Entry: `MOUSEWHEEL` when cursor over narration rect (`app.py:65–67`).
2. Sets `_scroll_velocity`; `_update_scroll` calls `narration.scroll(dy)` which clamps using `_total_height`.
3. AC: manual scroll up for history must keep working; new content should return view to bottom (policy choice: always vs near-bottom-only — document in spec).

### Session load (related, out of ticket AC)

1. Entry: `_load_session` (`app.py:454–478`).
2. Appends saved `narration_lines` directly to `self.narration.lines`, sets `_dirty = True`.
3. No scroll request — resume may open mid-log. Optional follow-up ticket if playtest cares.

## Existing specs & docs

- Ticket: [`tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md`](../../app-060-auto-scroll-narration-on-input-and-response.md) — root cause and suggested fixes already drafted.
- Domain spec: [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) — Narration panel row lists auto-scroll (APP-060); Tests section says "Manual: scroll, history"; no § Narration scroll behavior yet.
- Related: [APP-059](backlog/app-059-standardize-creation-table-outputs.md) — taller tables increase visible failure; [APP-090](backlog/app-090-combat-phased-narration-and-death-beat.md) — multi-emit may depend on scroll coalesce.
- Batch note: APP-036 and APP-060 both touch `app/ui/app.py` — sequential Stage 7a per batch board.

## Tests & commands

```bash
# Manual repro (primary)
cd app && python main.py
# new game → advance creation until a stats/skills table appears
# submit a line; confirm player line + table tail require wheel scroll

# Regression after fix
python -m pytest app/tests/test_ui_map_creation_gate.py -q   # pygame panel pattern
python -m pytest app/tests/test_narration_scroll.py -q       # optional new module per ticket

# Full app tests (no narration scroll coverage today)
python -m pytest app/tests -q
```

**Suggested unit test (no display):** construct `NarrationPanel` with fixed `rect`, `pygame.font` init (see `test_ui_map_creation_gate.py`), add lines exceeding `rect.height`, call broken path (`scroll_to_bottom` before rebuild) vs fixed path, assert `_scroll_offset >= _total_height - rect.height` (within padding `+ 40`).

## Risks & unknowns

- **APP-036 overlap:** if creation-step badge lands first in `app/ui/app.py`, merge scroll fix carefully in same file.
- **Near-bottom policy:** ticket AC allows implementer choice (always scroll vs only if user was at bottom); PM spec should pick one and define threshold.
- **`+ 40` padding:** magic constant in `scroll_to_bottom` / `scroll` clamp — preserve or document; may relate to status line above input.
- **Resize:** `resize()` sets `_dirty = True` only; no auto re-pin — window resize during long log may leave view mid-panel until next add (edge case).
- **TTS / multi-chunk narration:** APP-090 may emit multiple narration events per turn; tail-follow flag should handle batched queue drains in one frame.
- **`_target_scroll`:** unused; remove or implement real smooth scroll — out of scope unless PM expands.

## Raw notes

- `_rebuild()` is O(all lines) every dirty draw — pre-existing; scroll fix should not add extra rebuilds per frame beyond one intentional rebuild-before-scroll.
- `clear_narration` resets offset to 0 in `clear()` — correct for new game.
- Queue message types that scroll today: `narration`, `narration_text`, `player` only.
- Grep: no `_follow_tail`, `_stick_to_bottom`, or `scroll_to_bottom_after_rebuild` in repo yet.
- Domain spec file map lists `ui/panels/*.py` but not scroll-specific behavior — PM adds § Narration scroll behavior + changelog on close.
