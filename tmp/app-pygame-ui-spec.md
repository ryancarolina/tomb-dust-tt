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
| **Stats** | HP bar, Fortune, Gold, Phase badge — **from engine `status()` via UI queue**, not LLM narration tags (APP-035) |
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

---

## Task checklist

- [x] Narration panel + rich text
- [x] Input box + history
- [x] Stats panel (HP, Fortune, Gold, Phase) — engine-backed via `update_from_status` (APP-035)
- [x] Map view + click travel
- [x] NPC card + sidebar

**Open work:** [APP-036](backlog/app-036-creation-step-badge-in-ui.md), [APP-058](backlog/app-058-ui-toggle-narration-tts-on-off.md), [APP-060](backlog/app-060-auto-scroll-narration-on-input-and-response.md), [APP-062](backlog/app-062-left-character-panel-inventory-spells-tabs.md), [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) in [`tmp/backlog/README.md`](backlog/README.md). _(APP-038 superseded by APP-062.)_

- [x] **APP-037:** Map travel blocked during Registry intake; orchestrator `is_map_travel_blocked()`; overlay + hint; enriched status refresh (spec: [Map travel during creation](#map-travel-during-creation-app-037)).
- [x] **APP-065:** Always-clear chips; code-owned player map + blocklist; no narration scrape (spec: [Suggestion chips](#suggestion-chips)).

---

## Tests

- Manual: scroll, history, map click sends travel string to orchestrator when travel not blocked.
- **APP-037:** `python -m pytest app/tests/test_ui_map_creation_gate.py -q` — `is_map_travel_blocked`, MapView gated click, status payload (when added).
- **APP-037 regression:** `python -m pytest app/tests/test_creation_flow.py -q` — post-finalize travel not blocked.
- **APP-065:** `python -m pytest app/tests/test_ui_suggestions.py -q` — builder map, blocklist, inactive-creation guard, equipment non-confirm path.
- **APP-065 regression:** `python -m pytest app/tests/test_creation_flow.py app/tests/test_session_resume_failure.py -q` — narration `Awaiting:` asserts unchanged.
- Future: headless panel unit tests for `rich_text.py` wrap logic.

---

## File map

| Path | Role |
|------|------|
| `ui/app.py` | Main loop, thread-safe narration updates; enriched status push on turn success/exception (APP-037) |
| `ui/theme.py` | Colors, fonts |
| `ui/rich_text.py` | Wrapped styled text |
| `ui/panels/*.py` | Panel widgets |
| `ui/panels/stats.py` | Engine-backed HP, phase, location (APP-035) |
| `ui/panels/map_view.py` | AV-GRID map; travel block overlay + hint (APP-037) |
| `ui/suggestions.py` | Player chip maps + blocklist (APP-065) |
| `tests/test_ui_map_creation_gate.py` | APP-037 unit tests for travel block during creation |
| `tests/test_ui_suggestions.py` | APP-065 unit tests for chip builder |

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
