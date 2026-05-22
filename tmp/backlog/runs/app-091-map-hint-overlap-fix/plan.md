# Implementation Plan: APP-091-map-hint-overlap-fix

**Status:** draft  
**backlog_ticket:** APP-091  
**ticket_path:** tmp/backlog/app-091-map-travel-block-hint-overlap-fix.md  
**domain_spec:** tmp/app-pygame-ui-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

**Layout-only fix** in `MapView`: move the creation travel-block hover hint from the footer label row (`grid_y + grid_h + 16`) **into** the existing semi-transparent grid overlay, centered with word-wrap. No changes to APP-037 gate behavior (orchestrator, enriched status, sidebar cache, click guard, default hint string).

**Root cause:** `_draw_surface` blits `displayName` at `info_y = grid_y + grid_h + 16`, then calls `_draw_travel_block_overlay(..., hint_x=x, hint_y=grid_y + grid_h + 16)` — identical Y.

**Preferred API:** refactor `_draw_travel_block_overlay` so surface path omits external hint coordinates; dungeon path keeps optional absolute hint position via keyword arg to avoid regression.

**Out of scope:** APP-063 map UX, orchestrator/sidebar/app.py edits, hint copy changes, sidebar height formula, new `theme.py` tokens.

---

## Code-path traces (current → planned)

### Flow A — Surface map draw (creation repro at `32-C`)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `map_view.py:draw` | L107–115: mode branch → `_draw_surface` | unchanged |
| 2 | `map_view.py:_draw_surface` | L117–120: `x`, `y` from `PANEL_PADDING` | unchanged |
| 3 | same | L123–125: title **MAP** | unchanged |
| 4 | same | L128–131: current cell col/row from `_addresses` | unchanged |
| 5 | same | L134–141: `cell_size`, `grid_x`, `grid_y`, `grid_w`, `grid_h` | unchanged |
| 6 | same | L143–207: compass + 3×3 cells | unchanged |
| 7 | same | L209–222: footer — `info_y = grid_y + grid_h + 16`; blit `displayName`; scene line below | **unchanged draw order** — footer always drawn before overlay |
| 8 | same | L224–226: `grid_rect = Rect(grid_x, grid_y, grid_w, grid_h)`; `_draw_travel_block_overlay(screen, grid_rect, x, grid_y + grid_h + 16)` | **`_draw_travel_block_overlay(screen, grid_rect)`** — no footer-row hint coords |
| 9 | `map_view.py:_draw_travel_block_overlay` | L285–288: alpha fill on `overlay_rect` | unchanged fill |
| 10 | same | L289–291: if `_hovering`, single-line hint at `(hint_x, hint_y)` | if `_hovering`, **wrap + center inside `overlay_rect`** |

**Collision coordinates (pre-fix):**

```text
overlay_rect.bottom = grid_y + grid_h
info_y              = grid_y + grid_h + 16   ← displayName Y
hint_y (bug)        = grid_y + grid_h + 16   ← same as info_y
```

**Post-fix invariant:**

```text
hint_rect.top    >= overlay_rect.top + HINT_PAD
hint_rect.bottom <= overlay_rect.bottom - HINT_PAD
hint_rect.bottom <  info_y                     ← strictly above footer row
```

---

### Flow B — Hover signal (unchanged)

| Step | File:symbol | L | Role |
|------|-------------|---|------|
| 1 | `app.py` event loop | ~L339 | `MOUSEMOTION` → `sidebar.handle_hover(pos)` |
| 2 | `sidebar.py:handle_hover` | L60–62 | delegate to `map.handle_hover` when in map rect |
| 3 | `map_view.py:handle_hover` | L99–100 | `_hovering = self.rect.collidepoint(pos)` — full panel |

Hint only renders when `travel_blocked and _hovering`; gate unchanged.

---

### Flow C — Status → blocked flag (unchanged)

| Step | File:symbol | L | Role |
|------|-------------|---|------|
| 1 | `app.py:_enrich_status_for_ui` | L346–349 | `map_travel_blocked` + hint |
| 2 | `sidebar.py:update_from_status` | L46–52 | `map.set_travel_blocked(...)` |
| 3 | `sidebar.py:_do_layout` | L33, L71–73 | re-apply cached block on resize |

No APP-091 edits.

---

### Flow D — Dungeon path (no regression)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `map_view.py:_draw_dungeon` | L269–276 | `content_rect` overlay; `_draw_travel_block_overlay(screen, content_rect, x, y + 4)` |
| 2 | overlay helper | hint at address line below content | **`hint_outside=(x, y + 4)`** kwarg preserves absolute blit |

Dungeon hint sits after `[address]` line — not on surface footer row. Surface fix must not alter this branch.

---

## Exact changes

### 1. `app/ui/panels/map_view.py`

#### 1a. Module-level layout constants (top of file, after imports)

```python
_HINT_PAD = 6          # horizontal inset inside overlay_rect
_HINT_LINE_GAP = 2     # vertical gap between wrapped lines
```

No `theme.py` changes — reuse `TEXT_MUTED` for hint color (unchanged).

#### 1b. New helpers on `MapView`

**`_wrap_hint_lines(self, text: str, max_width: int) -> list[pygame.Surface]`**

- Uses `self._font_small` (already created in `_ensure_fonts`).
- Simple word-wrap by space tokens (same algorithm as `rich_text.render_wrapped_line` but **without** `StyledSpan` — do **not** import narration rich_text to avoid cross-panel coupling).
- Pseudocode:

```python
def _wrap_hint_lines(self, text: str, max_width: int) -> list[pygame.Surface]:
    self._ensure_fonts()
    words = text.split()
    lines: list[pygame.Surface] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if self._font_small.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(self._font_small.render(current, True, TEXT_MUTED))
            current = word
    if current:
        lines.append(self._font_small.render(current, True, TEXT_MUTED))
    return lines
```

**`_layout_hint_in_rect(self, overlay_rect: pygame.Rect, lines: list[pygame.Surface]) -> pygame.Rect`**

- Computes centered blit positions **without** drawing (shared by draw + test).
- `max_width = overlay_rect.width - 2 * _HINT_PAD`
- `total_h = sum(s.get_height() for s in lines) + _HINT_LINE_GAP * max(0, len(lines) - 1)`
- `start_y = overlay_rect.top + max(_HINT_PAD, (overlay_rect.height - total_h) // 2)`
- For each line: `x = overlay_rect.left + (overlay_rect.width - line.get_width()) // 2`
- Return union `pygame.Rect` covering all line bounds (empty rect if `lines` empty).

**`_travel_block_hint_rect(self, overlay_rect: pygame.Rect) -> pygame.Rect | None`**

- Returns `None` unless `self.travel_blocked and self._hovering`.
- `max_w = max(1, overlay_rect.width - 2 * _HINT_PAD)`
- `lines = self._wrap_hint_lines(self.travel_blocked_hint, max_w)`
- Return `_layout_hint_in_rect(overlay_rect, lines)`.

**`_surface_grid_metrics(self) -> tuple[pygame.Rect, int]`** *(test helper — mirrors `_draw_surface` grid math)*

- Duplicate the layout block from `_draw_surface` L119–141 (title → `grid_x/grid_y/grid_w/grid_h`) **without blitting**.
- Return `(pygame.Rect(grid_x, grid_y, grid_w, grid_h), grid_y + grid_h + 16)`.
- Keeps test DRY and locked to production layout formula.

#### 1c. Refactor `_draw_travel_block_overlay`

**Before (L278–291):**

```python
def _draw_travel_block_overlay(self, screen, overlay_rect, hint_x, hint_y):
    ... fill ...
    if self.travel_blocked and self._hovering:
        hint_surf = self._font_small.render(...)
        screen.blit(hint_surf, (hint_x, hint_y))
```

**After:**

```python
def _draw_travel_block_overlay(
    self,
    screen: pygame.Surface,
    overlay_rect: pygame.Rect,
    *,
    hint_outside: tuple[int, int] | None = None,
) -> None:
    overlay = pygame.Surface((overlay_rect.width, overlay_rect.height), pygame.SRCALPHA)
    muted = TEXT_MUTED
    overlay.fill((muted[0], muted[1], muted[2], 102))
    screen.blit(overlay, overlay_rect.topleft)

    if not (self.travel_blocked and self._hovering):
        return

    self._ensure_fonts()

    if hint_outside is not None:
        # Dungeon legacy: single line at absolute screen coords
        hint_surf = self._font_small.render(self.travel_blocked_hint, True, TEXT_MUTED)
        screen.blit(hint_surf, hint_outside)
        return

    # Surface path: wrap + center inside overlay_rect
    max_w = max(1, overlay_rect.width - 2 * _HINT_PAD)
    lines = self._wrap_hint_lines(self.travel_blocked_hint, max_w)
    layout_rect = self._layout_hint_in_rect(overlay_rect, lines)
    y = layout_rect.top if not lines else layout_rect.top  # iterate from layout
    # Blit each line at positions derived from _layout_hint_in_rect
    # (impl: either return list of (surf, pos) from layout helper or blit in loop mirroring layout math)
```

**Implementation note:** Prefer extending `_layout_hint_in_rect` to return `list[tuple[pygame.Surface, tuple[int, int]]]` so draw and rect helper share one code path:

```python
def _layout_hint_in_rect(...) -> tuple[pygame.Rect, list[tuple[pygame.Surface, tuple[int, int]]]]:
    ...
    return union_rect, placements

def _travel_block_hint_rect(...):
    _, placements = self._layout_hint_placements(overlay_rect, lines)
    return union_rect from placements

def _draw_travel_block_overlay(...):
    ...
    _, placements = self._layout_hint_placements(overlay_rect, lines)
    for surf, pos in placements:
        screen.blit(surf, pos)
```

#### 1d. Call-site updates

**`_draw_surface` L224–226 — change to:**

```python
if self.travel_blocked:
    grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
    self._draw_travel_block_overlay(screen, grid_rect)
```

Remove `x` and `grid_y + grid_h + 16` arguments entirely.

**`_draw_dungeon` L276 — change to:**

```python
self._draw_travel_block_overlay(screen, content_rect, hint_outside=(x, y + 4))
```

Preserves dungeon hint below address line.

---

### 2. `app/tests/test_ui_map_creation_gate.py`

#### New test: `test_map_view_hint_blit_inside_overlay_not_footer_row`

**Purpose (R4):** Assert hint layout rect is inside grid overlay and strictly above footer `info_y`. Fails on pre-fix code (hint Y == `info_y`); passes after impl.

**Setup:**

```python
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
try:
    from pathlib import Path
    from ui.panels.map_view import MapView

    build_root = Path(__file__).resolve().parents[2] / "build"
    # Narrow sidebar column (~30% of 800px window) — APP-062 wrap stress
    mv = MapView(pygame.Rect(0, 0, 240, 320), content_root=build_root)
    mv.update_position("32-C")
    mv.set_travel_blocked(True)
    mv._hovering = True
    mv._ensure_fonts()

    grid_rect, info_y = mv._surface_grid_metrics()
    hint_rect = mv._travel_block_hint_rect(grid_rect)

    assert hint_rect is not None
    assert grid_rect.contains(hint_rect)
    assert hint_rect.top >= grid_rect.top
    assert hint_rect.bottom <= grid_rect.bottom
    assert hint_rect.bottom < info_y  # not on displayName / scene footer row

    # Wrap on narrow column: long default hint should be multi-line inside overlay
    max_w = max(1, grid_rect.width - 12)  # 2 * _HINT_PAD
    wrapped = mv._wrap_hint_lines(mv.travel_blocked_hint, max_w)
    assert len(wrapped) >= 2
finally:
    pygame.quit()
```

**Optional secondary assertion (same test):** `hint_rect.centery` within `[grid_rect.top, grid_rect.bottom]` — confirms vertical centering, not pinned to footer.

**Existing tests:** All 10 current tests must pass unchanged — no weakening of APP-037 assertions.

---

### 3. `tmp/app-pygame-ui-spec.md`

**Impl on close only (R5):**

1. § Hint placement (APP-091) — PM draft already matches planned behavior; verify no drift after impl.
2. Changelog L361: replace **APP-091 draft** with **done** entry dated release day.
3. Ticket: `release APP-091 --done`.

No spec prose edits during impl unless behavior diverges from draft.

---

## Layout math reference (surface path)

For test/debug alignment with `_draw_surface`:

| Variable | Formula |
|----------|---------|
| `x` | `rect.left + PANEL_PADDING` (12) |
| `y` after title | `rect.top + PANEL_PADDING + title_h + 4` |
| `available_w` | `rect.width - PANEL_PADDING * 2` |
| `available_h` | `rect.height - (y - rect.top) - PANEL_PADDING - 60` |
| `cell_size` | `min(available_w // 3, available_h // 3, 60)` |
| `grid_w`, `grid_h` | `cell_size * 3` |
| `grid_x` | `x + (available_w - grid_w) // 2` |
| `grid_y` | `y + 14` |
| `info_y` | `grid_y + grid_h + 16` |
| `overlay_rect` | `Rect(grid_x, grid_y, grid_w, grid_h)` |

**Narrow sidebar example** (`rect.width=240`):

- `available_w = 216` → `cell_size = 60` → `grid_w = 180`
- Hint max line width ≈ `180 - 12 = 168px` at 11px Consolas → **"Finish Registry intake first"** wraps to 2+ lines.

---

## Files (must ⊆ ticket Expected files)

| Path | Change |
|------|--------|
| `app/ui/panels/map_view.py` | Hint wrap/center inside overlay; refactor `_draw_travel_block_overlay`; test helpers `_surface_grid_metrics`, `_travel_block_hint_rect` |
| `app/tests/test_ui_map_creation_gate.py` | `test_map_view_hint_blit_inside_overlay_not_footer_row` |
| `tmp/app-pygame-ui-spec.md` | Changelog finalize on close only |

**Not edited:** `app/ui/app.py`, `sidebar.py`, `orchestrator.py`, `theme.py`, `rich_text.py`.

---

## Tests

```bash
# Primary — includes new placement test
python -m pytest app/tests/test_ui_map_creation_gate.py -q

# APP-037 regression
python -m pytest app/tests/test_creation_flow.py -q
```

**Fail-pre / pass-post contract:**

| State | `test_map_view_hint_blit_inside_overlay_not_footer_row` |
|-------|--------------------------------------------------------|
| Pre-fix | **FAIL** — no `_travel_block_hint_rect`; or if testing blit Y directly, `hint_y == info_y` |
| Post-fix | **PASS** — `grid_rect.contains(hint_rect)` and `hint_rect.bottom < info_y` |

**Manual repro:**

```bash
cd app && python main.py
# new game → hover sidebar map at 32-C during creation
# Expect: hint inside grey grid; "Breley Keep" + scene line legible below
```

---

## TurnTruth / narration gate

No `app/gm/` narration changes — **N/A**.

---

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Muted-on-muted contrast inside overlay | Human playtest per run `human-test-plan.md`; no color token change in scope |
| Dungeon path accidental break | Preserve `hint_outside=` branch; single-line blit unchanged |
| `_surface_grid_metrics` drift from `_draw_surface` | Extract shared private `_compute_surface_grid()` used by both draw + metrics |
| Wrap helper duplication vs `rich_text` | Accept small duplicate — hint is plain unstyled text |

**Recommended impl refinement:** If `_surface_grid_metrics` duplicates too much logic, extract `_compute_surface_grid(self) -> tuple[int,int,int,int,int]` returning `(grid_x, grid_y, grid_w, grid_h, info_y)` and call from `_draw_surface` + test helper.

---

## Implementation order

1. Add `_wrap_hint_lines` + layout helpers + `_travel_block_hint_rect` + `_surface_grid_metrics` (or shared `_compute_surface_grid`).
2. Refactor `_draw_travel_block_overlay` (inside vs `hint_outside`).
3. Update `_draw_surface` call (drop footer hint coords); update `_draw_dungeon` call (`hint_outside=`).
4. Add placement unit test; run full `test_ui_map_creation_gate.py`.
5. Manual repro at `32-C`; finalize spec changelog on ticket close.
