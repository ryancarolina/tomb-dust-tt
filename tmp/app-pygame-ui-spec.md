# Spec — PyGame UI

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress (baseline shipped)  
**Owns:** `app/ui/**`

---

## Spec

### Layout

- Split: **character panel (left, tabbed)**, narration (center), sidebar (right) — stats, map, NPC card, input.
- Character panel: **Backpack** | **Spells** tabs — [APP-062](backlog/app-062-left-character-panel-inventory-spells-tabs.md).
- Configurable widths via `config.yaml` (`narration_width_ratio`, character panel ratio).

### Panels

| Panel | Behavior |
|-------|----------|
| **Narration** | Scrollable rich text; per-voice colors; wheel scroll; **auto-scroll to bottom** on new player/GM lines — [APP-060](backlog/app-060-auto-scroll-narration-on-input-and-response.md) |
| **Input** | Enter to send; Up/Down history; suggestion chips — see [Suggestion chips](#suggestion-chips) |
| **Stats** | HP bar, Fortune, Gold, Phase badge, **Registry intake step badge** (APP-036 when `creation.active`) — **from enriched engine status via UI queue**, not LLM narration tags (APP-035) |
| **Map** | AV-GRID 3×3 grid; visited highlight; click → travel when allowed — **travel blocked during creation** [APP-037](backlog/app-037-block-map-travel-during-creation.md); **redesign** [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) |
| **NPC card** | Current speaker + voice animation when TTS active |
| **Sidebar** | Composes stats + map + NPC |
| **Character panel** | Left column; **Backpack** / **Spells** tabs — engine data from bridge — APP-062 |

### Controls

| Input | Action |
|-------|--------|
| Enter | Submit to orchestrator |
| Escape | Save + quit |
| Narration toggle | Turn GM voice (TTS) on/off for the session — see [APP-058](backlog/app-058-ui-toggle-narration-tts-on-off.md) |
| Map click | Travel to cell when map travel not blocked (orchestrator handles); no-op during Registry intake |

### Narration scroll behavior (APP-060)

**Ticket:** [APP-060](backlog/app-060-auto-scroll-narration-on-input-and-response.md)

The narration panel is scrollable rich text (wheel + scrollbar). **New player/GM/error lines must pin the viewport to the bottom** after layout height is known — not before.

#### Root cause (pre-fix)

`add_line` / `add_lines` set `_dirty = True` and defer `_rebuild()` until `draw()`. Calling `scroll_to_bottom()` immediately after append uses **stale** `_total_height`, so long wrapped text and markdown tables leave the latest content below the visible area.

#### Tail-follow policy (v1)

| Rule | Detail |
|------|--------|
| **When** | After queued append of player input, GM narration, or error text |
| **Policy** | **Always** follow tail on those events — even if the user had scrolled up to read history; the next submit or GM reply returns to the bottom |
| **Not on** | `clear_narration`, status/map/suggestions/speaker/processing events |
| **Wheel** | Unchanged — `MOUSEWHEEL` over narration applies momentum via `narration.scroll()`; manual history reading works between turns |

Near-bottom-only auto-scroll (only pin when user was already within N px of bottom) is **deferred** — not v1.

#### Layout-correct pin (required implementation)

Bottom offset must be computed **after** `_total_height` reflects all pending lines.

**Preferred:** `_follow_tail` flag on `NarrationPanel`:

1. Queue handlers call `request_follow_tail()` (via `App._smooth_scroll_to_bottom()`) — does not scroll immediately.
2. `draw()`: if `_dirty`, `_rebuild()`; if `_follow_tail`, `scroll_to_bottom()` then clear flag.

**Alternative:** `scroll_to_bottom_after_rebuild()` — rebuild if dirty, then set `_scroll_offset` using existing clamp (`max(0, _total_height - rect.height + 40)`).

Multiple queue messages drained in one frame coalesce to **one** tail pin after the final rebuild.

#### Queue paths

| `msg_type` | Append | Follow tail |
|------------|--------|-------------|
| `player` | Player line (`voice: player`) | Yes |
| `narration_text` | Single GM string | Yes |
| `narration` | Batch GM lines | Yes |
| `error` | `[Error: …]` narrator line | Yes |
| `clear_narration` | `clear()` — offset → 0 | No (reset only) |

Frame order in `App.run`: `_process_ui_queue()` → wheel momentum `_update_scroll()` → panel `draw()`.

#### Out of scope (APP-060)

- Animated smooth scroll (`_target_scroll` unused).
- Auto pin on session load (`_load_session` sets `_dirty` only).
- Re-pin on window resize alone.

#### Implementation files (APP-060)

| Path | Role |
|------|------|
| `app/ui/panels/narration.py` | `_follow_tail`, `request_follow_tail()`, apply in `draw()` after `_rebuild()`; optional `scroll_to_bottom_after_rebuild()` |
| `app/ui/app.py` | `_smooth_scroll_to_bottom()` delegates to follow-tail API; `error` handler requests tail |
| `app/tests/test_narration_scroll.py` | Unit tests: stale vs fixed scroll offset after tall content |

#### Tests (APP-060)

```bash
python -m pytest app/tests/test_narration_scroll.py -q
python -m pytest app/tests/test_ui_map_creation_gate.py -q   # regression
```

Manual: creation table step + submit → player line and table tail visible without wheel; long GM reply; error line at bottom.

### Map travel during creation (APP-037)

**Ticket:** [APP-037](backlog/app-037-block-map-travel-during-creation.md) · **Engine mirror:** [APP-008](backlog/app-008-hard-gate-exploration-during-creation.md) (`creation.active` hard-gate in orchestrator).

During Registry intake the map **still displays** (hub cell, fog, labels from `party.address`) but **travel actions are disabled** — greyed overlay, no `travel to …` submit, hover hint.

#### Travel-blocked signal

| Rule | Detail |
|------|--------|
| **Source** | `Orchestrator.is_map_travel_blocked()` — **not** narration, not `StatsPanel` alone. |
| **Block when** | `creation.active` **or** (`status.awaiting == "CHARACTER_CREATION"` and empty `roster`). |
| **Do not block** | `creation.active == false` and post-finalize play (`PLAYER_ACTIONS`, non-empty roster) — even if `awaiting` is stale. |
| **UI refresh** | On each `("status", …)` push from `app/ui/app.py` (init + every turn success **or** exception), enrich `get_status()` with `map_travel_blocked` (and optional `map_travel_blocked_hint`) via `Orchestrator.is_map_travel_blocked()` before `Sidebar.update_from_status`. Exception path: queue enriched status in `_process_turn` `finally` alongside `_queue_turn_suggestions` (APP-065 parity) — not only the success-path push. |

Same dual-condition policy as [APP-065](backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md) inactive-creation guard.

#### Layers (defense in depth)

1. **`app/ui/app.py`** — skip `_submit(f"travel to {addr}")` when blocked (even if `handle_click` returns an address after APP-063).
2. **`MapView`** — `set_travel_blocked`; `handle_click` → `None` when blocked; muted overlay on draw; hover shows hint.
3. **Engine (APP-008)** — exploration tools rejected while `creation.active`; UI does not replace this gate.

#### Player copy

- Default hover hint: **"Finish Registry intake first"** (ticket allows equivalent wording in UI only if tests lock the default string).

#### Re-enable

After creation finalize (`creation.active == false`, live delver on surface): next status refresh clears blocked state; map clicks may submit travel again (subject to APP-063 hit-testing).

#### Layout (APP-062)

Map lives in right sidebar (`stats` + `map` split). Travel block is `MapView` state only — `Sidebar._do_layout` height formula unchanged; resize must not drop blocked flag.

#### Implementation files (APP-037)

| Path | Role |
|------|------|
| `app/gm/orchestrator.py` | `is_map_travel_blocked()` — reads `creation.active` and `bridge.status()`; not narration |
| `app/ui/app.py` | Enrich `("status", …)` with `map_travel_blocked` / hint (init, success path, and `_process_turn` `finally`); guard map click → `_submit` when blocked |
| `app/ui/panels/sidebar.py` | Forward blocked flag from status to `MapView`; optional short-circuit in `handle_map_click` |
| `app/ui/panels/map_view.py` | `set_travel_blocked`, muted overlay, hover hint, gated `handle_click` |
| `app/tests/test_ui_map_creation_gate.py` | Unit tests for `is_map_travel_blocked`, MapView gated click, enriched status payload |

### Suggestion chips

**Ticket:** [APP-065](backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md) · **Batch:** prefer [APP-073](backlog/app-073-strip-llm-embedded-status-tags-in-creation.md) impl first (narration cleanup); chips do not scrape narration regardless.

Chips are quick-send buttons above the input row (`input_box.py`). Each chip’s **display label is the submitted text** (v1: no separate submit payload).

#### Source of truth (never narration)

| Rule | Detail |
|------|--------|
| **Builder** | `Orchestrator.get_player_suggestions()` → list of player phrases (max 4). |
| **Module** | Curated maps + blocklist in `app/ui/suggestions.py` (or equivalent under `app/ui/**`). |
| **Forbidden** | Regex on GM narration for `Awaiting:` (legacy `_extract_suggestions` removed from turn path). |
| **Not used** | `play/tomb_gm/suggest.py` `prompts` (GM/operator hints). |

**Lookup order:** (1) if `creation.active` → `PLAYER_SUGGESTIONS_BY_CREATION_STEP[creation.step]`; (2) else `PLAYER_SUGGESTIONS_BY_AWAITING[status.awaiting]`; (3) else `[]`. When `creation.active` is false, **never** read `creation.step` — post-finalize chips come from engine `awaiting` only (typically `PLAYER_ACTIONS` → `[]`), even if `awaiting` is still `CHARACTER_CREATION` or `creation.step` is stale (e.g. `WORLD_INTRO` after finalize). Map keys use **`creation.step`** (`NAME`, `EQUIPMENT_GOLD`, …), not `CREATION_STATUS_LABELS` footer tokens (`EQUIPMENT_GOLD_CONFIRMATION`, …).

#### Always refresh (stale clear)

After every `process_turn` (success or exception), the UI queue **always** sends `("suggestions", list)` — including `[]`. Empty list clears prior chips. No `if suggestions:` skip. On turn failure, refresh still runs so prior step chips do not persist beside the error line.

Startup (`_init_orchestrator`) may seed once; first turn overwrites via the builder.

#### Curated player map (v1)

| Context | Chips |
|---------|-------|
| `creation.active` and `creation.step == EQUIPMENT_GOLD` | `Yes, confirm`, `I need different gear` — confirm matches `is_equipment_confirm`; objection works via **non-confirm** (`not is_equipment_confirm`) and re-presents kit — does **not** require `EQUIPMENT_OBJECTION_RE` match |
| `awaiting == SETUP` | `new game`; add `load game` when save exists |
| `awaiting == SESSION_ENDED` | `new game` |
| `awaiting == CHARACTER_CREATION` and not `creation.active` | `[]` |
| All other creation steps (when active) | `[]` (free-text or code tables) |
| `PLAYER_ACTIONS`, `COMBAT_TURN`, `ROSTER_SETUP`, etc. | `[]` (map travel / combat typed in input) |

Post–world-intro exploration: no chips in v1 (`WORLD_INTRO` → `[]`); map click handles travel.

#### Blocklist

Filter before display; block if `is_blocked_chip_token(text)`:

- `UPPER_SNAKE_CASE` internal labels (regex `^[A-Z][A-Z0-9_]{2,}$`).
- Suffixes `*_INPUT`, `*_CONFIRMATION`.
- Engine enums: `SETUP`, `SESSION_ENDED`, `CHARACTER_CREATION`, `ROSTER_SETUP`, `PLAYER_ACTIONS`, `COMBAT_TURN`, `DYING`, `DOWNED`, `BLOCKED`, `HUMAN_GATE`, `RECEPTION_CHOICE`.
- All values from `CREATION_STATUS_LABELS` in `app/gm/creation.py`.

**Allowed examples:** `load game`, `new game`, `Yes, confirm`, `I need different gear`.

#### Widget contract

- `InputBox.set_suggestions` truncates to 4; click submits that string to orchestrator.
- Chips must never show or submit raw `Awaiting:` tokens from narration footers or LLM status lines.

#### Stats panel (APP-035)

- `StatsPanel.update_from_status(status)` in `app/ui/panels/stats.py` — HP, MP, Fortune, gold, phase badge, address, conditions, known spells.
- Data source: `GameBridge.status()` pushed as `("status", …)` on each turn from `app/ui/app.py` — **never** parsed from narration `[Phase: …]` / `[Location: …]` footers.
- Spell names in stats are a short footnote (≤4); full list moves to APP-062 Spells tab when shipped.

### Creation step badge (APP-036)

**Ticket:** [APP-036](backlog/app-036-creation-step-badge-in-ui.md) · **Step truth:** [`app-character-creation-spec.md`](app-character-creation-spec.md) § Awaiting contract · **Enrich template:** [Map travel during creation (APP-037)](#map-travel-during-creation-app-037).

During Registry intake (`creation.active`), show a **Registry step badge** at the **top of the stats panel** (above character name and phase badge). Duplicate signal for sidebar clarity — narration `Awaiting:` footer remains code-owned (APP-007); badge is **not** a second source of truth and **never** scraped from narration.

#### Badge signal

| Rule | Detail |
|------|--------|
| **Source** | `Orchestrator.get_creation_step_badge()` — reads `creation.active` and `creation.step`; **not** narration, not `status.awaiting` alone |
| **Show when** | `creation.active == True` |
| **Hide when** | `creation.active == False` (post-finalize, live roster) — even if engine `awaiting == CHARACTER_CREATION` or stale `creation.step` |
| **UI refresh** | On each enriched `("status", …)` push from `app/ui/app.py` (init + every turn success **or** exception) via `_enrich_status_for_ui` — same cadence as APP-037 map gate and APP-065 chips |
| **Session load** | After resume/`import_creation_state`, next status push carries badge fields so label matches restored step without waiting for a player turn |

#### Enriched status keys

`_enrich_status_for_ui` adds (alongside APP-037 `map_travel_blocked` keys):

| Key | When active | When inactive |
|-----|-------------|---------------|
| `creation_step` | FSM key (`NAME`, `SKILLS`, …) | `None` |
| `creation_step_display` | Human label from `CREATION_STEP_DISPLAY[step]` | `None` |

**Display labels** are keyed by **`creation.step`** in `CREATION_STEP_DISPLAY` (`app/gm/creation.py`) — **not** `CREATION_STATUS_LABELS` footer tokens (`SKILLS_INPUT`, `EQUIPMENT_GOLD_CONFIRMATION`, …). APP-065 blocklist still applies: never show those tokens as badge text.

| Step | Badge display label |
|------|---------------------|
| `NAME` | Name |
| `RACE` | Race |
| `ROLL_STATS` | Roll Stats |
| `CLASS` | Class |
| `SKILLS` | Skills |
| `SPELL_SCHOOLS` | Spell Schools |
| `SPELLS` | Spells |
| `EQUIPMENT_GOLD` | Equipment & Gold |
| `FINALIZE` | Finalize |
| `WORLD_INTRO` | Reception |

Unknown step: title-case fallback from step slug.

#### Render (StatsPanel)

- Draw only when `creation_step_display` is non-empty.
- Copy: static prefix **`Registry:`** + display label (e.g. `Registry: Skills`).
- Small-font rounded badge (reuse phase pill pattern); distinct color from phase badge.
- Phase badge below character name unchanged during intake.

#### Layout (APP-062)

Badge is draw state on `StatsPanel` inside right sidebar stats half — `Sidebar._do_layout` height formula unchanged; resize must not drop badge state (mirror APP-037 blocked-flag preserve test).

#### Implementation files (APP-036)

| Path | Role |
|------|------|
| `app/gm/creation.py` | `CREATION_STEP_DISPLAY` — step-keyed human labels |
| `app/gm/orchestrator.py` | `get_creation_step_badge()` |
| `app/ui/app.py` | Extend `_enrich_status_for_ui`; `_queue_turn_status` in init + turn `finally` |
| `app/ui/panels/stats.py` | Read enriched keys; draw Registry badge at panel top |
| `app/ui/panels/sidebar.py` | Cache creation badge keys; re-apply on `_do_layout` resize |
| `app/tests/test_ui_creation_badge.py` | Helper, enrich payload, panel state, sidebar resize, exception-path refresh |
| `app/tests/test_ui_map_creation_gate.py` | Enrich regression — mock `get_creation_step_badge.return_value = None` |

---

## Task checklist

- [x] Narration panel + rich text
- [x] Input box + history
- [x] Stats panel (HP, Fortune, Gold, Phase) — engine-backed via `update_from_status` (APP-035)
- [x] Map view + click travel
- [x] NPC card + sidebar

- [x] **APP-036:** Registry step badge via `_enrich_status_for_ui`; `CREATION_STEP_DISPLAY` keyed by `creation.step`; `get_creation_step_badge()`; StatsPanel top placement; sidebar resize cache; not footer tokens (spec: [Creation step badge](#creation-step-badge-app-036)).

**Open work:** [APP-058](backlog/app-058-ui-toggle-narration-tts-on-off.md), [APP-062](backlog/app-062-left-character-panel-inventory-spells-tabs.md), [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) in [`tmp/backlog/README.md`](backlog/README.md). _(APP-038 superseded by APP-062.)_

- [x] **APP-060:** Tail-follow scroll after `_rebuild()`; error path scroll; `test_narration_scroll.py` (spec: [Narration scroll behavior](#narration-scroll-behavior-app-060)).

- [x] **APP-037:** Map travel blocked during Registry intake; orchestrator `is_map_travel_blocked()`; overlay + hint; enriched status refresh (spec: [Map travel during creation](#map-travel-during-creation-app-037)).
- [x] **APP-065:** Always-clear chips; code-owned player map + blocklist; no narration scrape (spec: [Suggestion chips](#suggestion-chips)).

---

## Tests

- Manual: scroll, history, map click sends travel string to orchestrator when travel not blocked.
- **APP-037:** `python -m pytest app/tests/test_ui_map_creation_gate.py -q` — `is_map_travel_blocked`, MapView gated click, status payload (when added).
- **APP-037 regression:** `python -m pytest app/tests/test_creation_flow.py -q` — post-finalize travel not blocked.
- **APP-065:** `python -m pytest app/tests/test_ui_suggestions.py -q` — builder map, blocklist, inactive-creation guard, equipment non-confirm path.
- **APP-065 regression:** `python -m pytest app/tests/test_creation_flow.py app/tests/test_session_resume_failure.py -q` — narration `Awaiting:` asserts unchanged.
- **APP-036:** `python -m pytest app/tests/test_ui_creation_badge.py -q` — `get_creation_step_badge`, enrich payload, StatsPanel badge show/hide, display labels ≠ footer tokens.
- **APP-036 regression:** `python -m pytest app/tests/test_creation_flow.py app/tests/test_creation_restore.py -q` — badge hidden post-finalize; resume restores step label.
- Future: headless panel unit tests for `rich_text.py` wrap logic.

---

## File map

| Path | Role |
|------|------|
| `ui/app.py` | Main loop, thread-safe narration updates; enriched status push on turn success/exception (APP-037) |
| `ui/theme.py` | Colors, fonts |
| `ui/rich_text.py` | Wrapped styled text |
| `ui/panels/sidebar.py` | NPC + stats + map column; resize cache for map block (APP-037) and creation badge (APP-036) |
| `ui/panels/stats.py` | Engine-backed HP, phase, location (APP-035); Registry step badge (APP-036) |
| `gm/creation.py` | `CREATION_STEP_DISPLAY` — badge labels keyed by `creation.step` (APP-036) |
| `gm/orchestrator.py` | `get_creation_step_badge()` (APP-036) |
| `ui/panels/map_view.py` | AV-GRID map; travel block overlay + hint (APP-037) |
| `ui/suggestions.py` | Player chip maps + blocklist (APP-065) |
| `tests/test_ui_map_creation_gate.py` | APP-037 unit tests for travel block during creation |
| `tests/test_ui_suggestions.py` | APP-065 unit tests for chip builder |
| `tests/test_ui_creation_badge.py` | APP-036 unit tests for creation step badge |
| `tests/test_narration_scroll.py` | APP-060 unit tests for narration tail-follow scroll |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created from app/README architecture |
| 2026-05-20 | APP-065 draft: suggestion chip source-of-truth, blocklist, always-clear (PM) |
| 2026-05-20 | APP-065 r2: equipment non-confirm path, inactive-creation lookup, error-path refresh, pytest commands |
| 2026-05-20 | **APP-065 done:** `ui/suggestions.py` + `get_player_suggestions()`; unconditional turn refresh; narration scrape removed; 17 unit tests |
| 2026-05-22 | **APP-035 done:** stats panel reads `GameBridge.status()` via UI queue; no narration tag parsing for HP/phase/location |
| 2026-05-22 | **APP-037 draft:** map travel blocked during `creation.active` (+ desync guard); display preserved; hint "Finish Registry intake first"; orchestrator `is_map_travel_blocked` (PM) |
| 2026-05-22 | **APP-037 r2:** ticket Expected files + domain § Implementation files aligned to orchestrator; R2 `finally` status refresh (mirror APP-065) |
| 2026-05-22 | **APP-037 done:** `is_map_travel_blocked()`; enriched status with `map_travel_blocked` / hint; MapView overlay + gated click; sidebar resize cache; `_queue_turn_status` in `finally`; 10 unit tests |
| 2026-05-22 | **APP-036 draft:** Registry step badge via `_enrich_status_for_ui`; `CREATION_STEP_DISPLAY` keyed by `creation.step`; `get_creation_step_badge()`; StatsPanel top placement; not footer tokens (PM) |
| 2026-05-22 | **APP-060 draft:** § Narration scroll behavior — tail-follow after `_rebuild`, queue paths (player/narration/error), always-follow policy, `test_narration_scroll.py` (PM) |
| 2026-05-22 | **APP-060 done:** `_follow_tail` + `request_follow_tail()` in `draw()` after `_rebuild()`; `_smooth_scroll_to_bottom()` defers pin; error handler follows tail; 6 unit tests |
| 2026-05-22 | **APP-036 done:** `CREATION_STEP_DISPLAY` + `format_creation_step_display`; `get_creation_step_badge()`; enriched `creation_step` / `creation_step_display`; Registry badge at stats panel top; sidebar resize cache; 9 unit tests |
