# Implementation Plan: APP-060-auto-scroll-narration

**Status:** draft  
**backlog_ticket:** APP-060  
**ticket_path:** tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md  
**domain_spec:** tmp/app-pygame-ui-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Fix layout-stale auto-scroll by **deferring bottom pin until `_total_height` is current**. Root cause: queue handlers call `scroll_to_bottom()` immediately after `add_line(s)` while `_rebuild()` only runs in `draw()` when `_dirty`.

**Shipped fix (PM choice):** `_follow_tail` flag on `NarrationPanel`:

1. Queue paths call `request_follow_tail()` (via thin `App._smooth_scroll_to_bottom()` wrapper) — **no immediate** `scroll_to_bottom()`.
2. `draw()`: `if _dirty: _rebuild()` → **`if _follow_tail: scroll_to_bottom(); _follow_tail = False`**.
3. One rebuild per dirty frame; multiple queue appends in one `_process_ui_queue` pass coalesce to a single tail pin.

**Policy (R3):** always follow tail on `player`, `narration`, `narration_text`, and **`error`** — even if user scrolled up. Wheel momentum unchanged.

**Error path (AC gap):** wire tail follow on `msg_type == "error"` (init failure, turn exception, orchestrator errors).

**Out of scope:** animated scroll (`_target_scroll` dead state), session-load pin, resize re-pin, rename `_smooth_scroll_to_bottom`.

**Batch note:** APP-036 also touches `app/ui/app.py` — implement APP-060 in isolation; merge scroll wiring without disturbing creation-step badge work (sequential Stage 7a per batch board).

---

## Code-path traces (current → planned)

### Flow A — Frame lifecycle (primary fix)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `app.py:run` L87–92 | `_process_ui_queue()` → `_update_scroll()` → `narration.draw()` | unchanged order |
| 2 | `app.py:_process_ui_queue` L163–171 | `add_*` → `_smooth_scroll_to_bottom()` → `scroll_to_bottom()` on **stale** height | `add_*` → `_smooth_scroll_to_bottom()` → `request_follow_tail()` only |
| 3 | `narration.py:draw` L161–163 | `if _dirty: _rebuild()` — no offset fix | after rebuild block: `if _follow_tail: scroll_to_bottom(); _follow_tail = False` |
| 4 | `narration.py:scroll_to_bottom` L72–73 | `_scroll_offset = max(0, _total_height - rect.height + 40)` | unchanged formula (+40 padding) |

**Planned `NarrationPanel.draw()` tail block:**

```python
def draw(self, screen: pygame.Surface):
    if self._dirty:
        self._rebuild()
    if self._follow_tail:
        self.scroll_to_bottom()
        self._follow_tail = False
    # ... blit + scrollbar (unchanged)
```

### Flow B — Player submit → GM response

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `app.py:_submit` L253–271 | queues `("player", text)` | unchanged |
| 2 | `_process_ui_queue` `player` | add + stale scroll | add + `request_follow_tail()` |
| 3 | `app.py:_process_turn` | success → `("narration_text", …)` | unchanged |
| 4 | `_process_ui_queue` `narration_text` | add + stale scroll | add + `request_follow_tail()` |
| 5 | `draw()` | rebuild with full GM block; offset wrong | tail pin uses fresh `_total_height` |

### Flow C — Batch startup narration

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `app.py:_init_orchestrator` L132–148 | multiple `("narration", [...])` in one drain | unchanged enqueue |
| 2 | `_process_ui_queue` | each batch: stale scroll | each batch: `request_follow_tail()` (flag stays True) |
| 3 | First `draw()` | welcome often fits viewport | single coalesced tail pin after final rebuild |

### Flow D — Error path (required AC)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `app.py:_init_orchestrator` L151–152 | `("error", f"Init failed: {exc}")` | unchanged |
| 2 | `app.py:_process_turn` except | `("error", str(exc))` | unchanged |
| 3 | `_process_ui_queue` `error` L202–204 | `add_line(f"[Error: {data}]", "narrator")` + `_set_turn_idle(...)` — **no scroll** | **add** `_smooth_scroll_to_bottom()` **after** add_line (before or after `_set_turn_idle` — order irrelevant) |
| 4 | `draw()` | error line may sit below viewport | tail pin shows `[Error: …]` |

**Error handler (planned):**

```python
elif msg_type == "error":
    self.narration.add_line(f"[Error: {data}]", "narrator")
    self._smooth_scroll_to_bottom()  # → request_follow_tail()
    self._set_turn_idle("Error — try again")
```

All error sources (`Init failed`, turn exception, future error enqueues) share this handler — one wiring point.

### Flow E — Manual wheel scroll (regression guard)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `app.py:run` MOUSEWHEEL L65–67 | sets `_scroll_velocity` | unchanged |
| 2 | `app.py:_update_scroll` L212–217 | `narration.scroll(dy)` | unchanged |
| 3 | Next player/GM/error queue event | stale scroll today | `request_follow_tail()` → view returns to bottom (always-follow policy) |

### Flow F — Explicit non-paths

| `msg_type` | Follow tail? |
|------------|--------------|
| `clear_narration` | No — `clear()` resets offset to 0 |
| `processing`, `status`, `map_update`, `speaker`, `suggestions`, `ready`, `turn_idle`, `load_session`, `speaking` | No |

**Defensive:** `NarrationPanel.clear()` should set `_follow_tail = False` so a pending flag cannot scroll after clear in the same frame.

---

## Task breakdown

### 1. `NarrationPanel` tail-follow — `app/ui/panels/narration.py`

#### 1.1 State

In `__init__`:

```python
self._follow_tail = False
```

#### 1.2 Public API

```python
def request_follow_tail(self) -> None:
    """Pin viewport to bottom after next layout rebuild in draw()."""
    self._follow_tail = True
```

Do **not** call `scroll_to_bottom()` here.

#### 1.3 Apply in `draw()` after `_rebuild`

Insert tail block immediately after the existing `if self._dirty: self._rebuild()` (before blit). Ensures `_total_height` reflects all lines appended since last rebuild.

#### 1.4 `clear()` reset

Add `self._follow_tail = False` in `clear()` alongside offset reset.

#### 1.5 Optional test helper (same module, no new export required)

Tests may compute expected bottom as:

```python
expected_bottom = max(0, panel._total_height - panel.rect.height + 40)
assert panel._scroll_offset >= expected_bottom - 1  # or ==
```

No `scroll_to_bottom_after_rebuild()` unless impl wants both — **ship `_follow_tail` only** per spec preference.

---

### 2. App queue wiring — `app/ui/app.py`

#### 2.1 `_smooth_scroll_to_bottom()` L225–226

Replace body:

```python
def _smooth_scroll_to_bottom(self):
    self.narration.request_follow_tail()
```

Keep name (spec: thin wrapper; no animation).

#### 2.2 Error handler L202–204

After `add_line`, call `self._smooth_scroll_to_bottom()`.

#### 2.3 Existing scroll callers (unchanged call sites)

Verify still call `_smooth_scroll_to_bottom()` after append:

- `narration` L163–165
- `narration_text` L166–168
- `player` L169–171

No new call sites on non-scroll events.

#### 2.4 Do not touch

- `_target_scroll` (unused)
- `_load_session` (no auto pin — out of scope)
- Wheel / `_update_scroll` physics

---

### 3. Unit tests — `app/tests/test_narration_scroll.py` (new)

Headless pattern from `test_ui_map_creation_gate.py`:

```python
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
try:
    ...
finally:
    pygame.quit()
```

**Panel setup:** `NarrationPanel(pygame.Rect(0, 0, 400, 120))` — viewport shorter than tall content.

**Tall content fixture:** multi-line GM string with markdown table (mirrors APP-059 creation tables), e.g. header + separator + several rows — enough wrapped surfaces that `_total_height >> rect.height`.

| Test | Steps | Assert |
|------|-------|--------|
| `test_stale_scroll_before_rebuild_fails` | add tall content; call `scroll_to_bottom()` **without** rebuild/draw | `_scroll_offset < bottom` (proves regression) |
| `test_request_follow_tail_after_draw_pins_bottom` | add tall content; `request_follow_tail()`; `draw(dummy_surface)` | `_scroll_offset == max(0, _total_height - rect.height + 40)` |
| `test_player_line_follows_tail` | `add_line("hello", "player")` + follow + draw | tail visible (offset at bottom) |
| `test_error_line_follows_tail` | `add_line("[Error: boom]", "narrator")` + follow + draw | tail visible |
| `test_multiple_follow_requests_coalesce` | add line; `request_follow_tail()` ×3; draw once | single bottom pin; flag cleared (`_follow_tail is False`) |
| `test_clear_clears_follow_flag` | `request_follow_tail()`; `clear()` | `_follow_tail is False`; offset 0 |

**Optional App-level test (non-blocking):** construct `App` with dummy pygame, stub queue put `("error", "msg")`, run `_process_ui_queue()`, assert `narration._follow_tail is True` before draw — only if quick; panel tests satisfy R4.

**Dummy surface for draw:** `pygame.Surface((400, 120))`.

---

### 4. Domain spec sync — `tmp/app-pygame-ui-spec.md`

PM draft § Narration scroll behavior already documents behavior (L38–105). On ticket close:

- Mark open-work / checklist item APP-060 `[x]`.
- Append changelog row: `2026-05-22 | APP-060: tail-follow after _rebuild; error path scroll (impl)`.

No rewrite unless impl diverges from PM draft.

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/ui/panels/narration.py` | `_follow_tail`, `request_follow_tail()`, apply in `draw()` after `_rebuild()`; reset flag in `clear()` |
| `app/ui/app.py` | `_smooth_scroll_to_bottom()` → `request_follow_tail()`; **error** handler adds tail follow |
| `app/tests/test_narration_scroll.py` | **New** — stale vs fixed, player/error, coalesce |
| `tmp/app-pygame-ui-spec.md` | Changelog + checklist on close |

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `python -m pytest app/tests/test_narration_scroll.py -q` | All new tests green |
| 2 | `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | Regression green |
| 3 | `python -m pytest app/tests -q` | Broader suite green |
| 4 | Manual: `cd app && python main.py` | Creation table + submit → no wheel; error visible at bottom |

---

## Rollback / flags

- Revert `narration.py` flag + `draw()` block, `app.py` wrapper + error line, delete test module.
- No feature flags. Behavior is immediate.

---

## Open questions

| # | Question | Default if unresolved |
|---|----------|----------------------|
| 1 | Also reset `_follow_tail` in `resize()`? | No — out of scope; resize only sets `_dirty` |
| 2 | Rename `_smooth_scroll_to_bottom`? | Keep name (spec non-goal) |
| 3 | App-level error queue integration test? | Panel + manual error repro sufficient |

---

## Acceptance criteria mapping

| Ticket AC / Spec R | Plan task |
|--------------------|-----------|
| Player submit pins player line | §2.3 player path + §3 player test |
| GM response full content (`narration`, `narration_text`) | §1 draw tail pin + §3 tall-content test |
| Layout-correct scroll after height known | §1 `_follow_tail` in `draw()` after `_rebuild` |
| Tables / multi-paragraph without wheel | §3 table fixture + manual creation step |
| **Error** line at bottom | §2.2 error handler + §3 error test |
| Manual scroll up; new content returns bottom | §2 always-follow via existing queue calls |
| Domain spec § Narration scroll behavior | §4 PM draft exists; checklist on close |
| R4 unit module required | §3 `test_narration_scroll.py` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial Dev plan from spec + qa-spec-pass |
