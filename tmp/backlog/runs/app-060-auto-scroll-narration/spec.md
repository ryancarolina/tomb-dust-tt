# Spec: app-060-auto-scroll-narration

**Status:** draft
**backlog_ticket:** APP-060
**ticket_path:** tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-pygame-ui-spec.md

## Problem

The narration panel calls auto-scroll on every queued player/GM line, but **`scroll_to_bottom()` runs before layout rebuild**. `NarrationPanel.add_line` / `add_lines` append to `self.lines` and set `_dirty = True`; `_rebuild()` (which recomputes `_total_height` from wrapped text, markdown, and tables) runs only inside `draw()` when `_dirty` is true. `scroll_to_bottom()` sets `_scroll_offset` from the **previous** `_total_height`, so after `draw()` rebuilds with taller content the offset is too small — the viewport stays mid-history. Long GM replies and creation markdown tables (APP-059) make the gap obvious.

Secondary gap: the **`error`** queue handler adds a line but does not request bottom scroll (ticket AC requires it).

`_smooth_scroll_to_bottom()` in `app/ui/app.py` is a misnomer — it is an instant `scroll_to_bottom()` with no animation. `_target_scroll` on `App` is unused dead state; do not expand scope to real smooth scroll unless PM revises.

## Goals

- After **player submit**, narration pins to the bottom so the player's line is visible.
- After **GM response** (`narration`, `narration_text`) and **errors** (`error`), narration shows the **full** new content including wrapped paragraphs and markdown tables.
- Scroll offset is computed **after** content height is known (layout-correct).
- Manual wheel scroll up for history keeps working; **new** queued player/GM/error content returns the view to the bottom.
- Behavior documented in domain spec § [Narration scroll behavior](../../../app-pygame-ui-spec.md#narration-scroll-behavior-app-060).

## Non-goals

- Animated smooth scroll (rename or leave `_smooth_scroll_to_bottom` as thin wrapper; no `_target_scroll` implementation).
- Session-load auto-scroll on resume (`_load_session` appends lines with `_dirty = True` but no scroll — optional follow-up if playtest cares).
- Window **resize** re-pin when user was at bottom (edge case: `resize()` sets `_dirty` only).
- Changing wheel momentum physics (`MOUSEWHEEL` → `_scroll_velocity` → `narration.scroll()`).
- TTS / multi-chunk narration coalescing beyond what tail-follow already handles (APP-090 may emit multiple events; flag must survive batched queue drains in one frame).

## Requirements

### R1: Layout-correct bottom pin (primary fix)

**Root cause:** `add_line(s)` → `_dirty=True` → `scroll_to_bottom(stale _total_height)` → `draw()` → `_rebuild(new _total_height)` → blit with stale `_scroll_offset`.

**Required behavior:** bottom pin must apply **after** `_total_height` reflects all pending lines.

**Preferred implementation — deferred tail-follow in `draw()`:**

| Step | Location | Action |
|------|----------|--------|
| 1 | `NarrationPanel` | Add `_follow_tail: bool = False` (or `_stick_to_bottom`; pick one name, use consistently). |
| 2 | `NarrationPanel` | Add `request_follow_tail()` (or `pin_to_bottom()`) that sets `_follow_tail = True` — does **not** call `scroll_to_bottom()` immediately. |
| 3 | `NarrationPanel.draw()` | After `if self._dirty: self._rebuild()`, if `_follow_tail`: call `scroll_to_bottom()`, then set `_follow_tail = False`. |
| 4 | `app/ui/app.py` | Replace direct `scroll_to_bottom()` in `_smooth_scroll_to_bottom()` with `narration.request_follow_tail()`. |

**Acceptable alternative — rebuild-before-scroll API:**

Add `scroll_to_bottom_after_rebuild()` on `NarrationPanel`: if `_dirty`, call `_rebuild()` first, then set `_scroll_offset` via existing `scroll_to_bottom()` math. Wire `_smooth_scroll_to_bottom()` to that method instead of bare `scroll_to_bottom()`.

**PM choice:** prefer **`_follow_tail` in `draw()`** so a single rebuild per frame remains authoritative and multiple queue messages in one `_process_ui_queue` pass coalesce to one tail pin after the final rebuild.

**Preserve:** `scroll_to_bottom()` clamp formula and `+ 40` bottom padding (matches `scroll()` clamp in `narration.py:68–73`); do not change without documenting in domain spec.

**Acceptance criteria**

- [ ] After adding lines that exceed viewport height, visible tail includes the latest line/table rows without manual wheel scroll.
- [ ] Unit test proves stale path fails and fixed path passes (see R4).
- [ ] At most one intentional `_rebuild()` per dirty frame on the tail-follow path (no double rebuild in queue + draw unless using rebuild-before-scroll alternative explicitly).

### R2: Queue paths that must follow tail

Wire **`request_follow_tail()`** (or fixed scroll API) from `_process_ui_queue` for every player-visible append that ticket AC covers:

| `msg_type` | Handler today | Required after fix |
|------------|---------------|-------------------|
| `player` | `add_line(..., "player")` + scroll (stale) | add + **follow tail** |
| `narration_text` | `add_line(..., "narrator")` + scroll (stale) | add + **follow tail** |
| `narration` | `add_lines(data)` + scroll (stale) | add + **follow tail** |
| `error` | `add_line(f"[Error: {data}]", "narrator")` — **no scroll** | add + **follow tail** |

**Do not** follow tail on: `clear_narration` (offset reset in `clear()` is correct), `processing`, status/map/suggestions/speaker events.

**Player submit flow (integration trace):**

1. Enter / chip → `_submit(text)` queues `("player", text)`.
2. Same or next frame: `_process_ui_queue` → player line + follow tail.
3. Worker `_process_turn` → queues `("narration_text", narration)` on success or `("error", …)` on failure.
4. Next queue drain → GM/error line + follow tail.
5. `draw()` rebuilds full history; tail pin uses fresh `_total_height`.

**Acceptance criteria**

- [ ] Manual repro: `new game` → creation table step → submit line → player line + table tail visible without wheel.
- [ ] Turn error path: forced orchestrator error shows `[Error: …]` at bottom without manual scroll.
- [ ] Batch startup `narration` lines still end at bottom after first `draw()` (welcome copy).

### R3: Manual scroll policy

**v1 policy — always follow on new queued content:** when `player`, `narration`, `narration_text`, or `error` appends lines, request tail follow **regardless** of current `_scroll_offset`. If the user scrolled up to read history, the next submit or GM reply jumps back to the bottom.

Rationale: matches primary ticket AC (“on **new** player/GM content, view returns to bottom”) and player expectation after sending input. Near-bottom-only auto-scroll is explicitly deferred (ticket optional enhancement).

**Wheel scroll unchanged:**

- `MOUSEWHEEL` over narration rect → `_scroll_velocity` → `_update_scroll` → `narration.scroll(dy)`.
- User can scroll up between turns; follow-tail on next queue event resets to bottom.

**Acceptance criteria**

- [ ] Wheel scroll up reveals older lines; scrollbar thumb moves.
- [ ] After scrolling up, submitting new input returns view to bottom (player line visible).
- [ ] Domain spec documents always-follow policy.

### R4: Unit tests (`app/tests/test_narration_scroll.py`)

New module — **required**, not optional. Headless pattern: `pygame.font.init()` / minimal display init as in `app/tests/test_ui_map_creation_gate.py`; construct `NarrationPanel` with fixed `rect` height.

**Minimum cases:**

| Test | Assert |
|------|--------|
| Stale path regression | Add tall content (multi-line GM text or table block), call broken sequence `scroll_to_bottom()` **before** rebuild → `_scroll_offset` **<** bottom position for current content. |
| Fixed path — rebuild-before-scroll | Same setup, call `scroll_to_bottom_after_rebuild()` (if implemented) → `_scroll_offset >= _total_height - rect.height` (within `+ 40` padding). |
| Fixed path — follow tail | Same setup, `request_follow_tail()` then `draw(mock_surface)` → offset at bottom after rebuild. |
| Player voice line | `add_line("hello", "player")` + follow → tail visible. |
| Error-style line | `add_line("[Error: …]", "narrator")` + follow → tail visible. |

Implementer may use one fixed API consistently; tests must cover the shipped approach.

**Acceptance criteria**

- [ ] `python -m pytest app/tests/test_narration_scroll.py -q` passes.
- [ ] No regression: `python -m pytest app/tests/test_ui_map_creation_gate.py -q`.

## Test plan

```bash
# Unit (required)
python -m pytest app/tests/test_narration_scroll.py -q

# Regression
python -m pytest app/tests/test_ui_map_creation_gate.py -q

# Broader app suite (no narration scroll coverage elsewhere)
python -m pytest app/tests -q
```

**Manual (Stage 7 human-test-plan):**

```bash
cd app && python main.py
```

- Creation step with stats/skills **table** → submit any line → player + GM table tail visible without wheel.
- Long multi-paragraph GM reply after exploration action → full reply visible.
- Provoke turn error → `[Error: …]` visible at bottom.

## Human playtest hints (for Stage 7)

- **Creation table:** advance to `ROLL_STATS` or skills table; submit name/choice; confirm no wheel needed to read table footer.
- **Long reply:** after world intro, ask a question that yields several paragraphs; confirm tail visible.
- **History read:** wheel up, read old lines, submit new command — view jumps to bottom with new exchange.
- **Error:** disconnect API or trigger known failure path; error line visible without scroll.

## Affected paths

Must match ticket **Expected files**:

| Path | Role |
|------|------|
| `app/ui/panels/narration.py` | `_follow_tail` + `request_follow_tail()`; apply in `draw()` after `_rebuild()`; optional `scroll_to_bottom_after_rebuild()` |
| `app/ui/app.py` | `_smooth_scroll_to_bottom()` → follow-tail API; add follow on `error` handler |
| `app/tests/test_narration_scroll.py` | Unit tests for rebuild + scroll offset |
| `tmp/app-pygame-ui-spec.md` | § Narration scroll behavior + changelog on close |

**Batch note:** APP-036 also touches `app/ui/app.py` — merge scroll wiring carefully; sequential Stage 7a per batch board.

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft (APP-060) |
