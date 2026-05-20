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
| **Stats** | HP bar, Fortune, Gold, Phase badge — **from engine status, not LLM tags** |
| **Map** | AV-GRID clickable cells; visited highlight; click → travel action — **redesign** [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) |
| **NPC card** | Current speaker + voice animation when TTS active |
| **Sidebar** | Composes stats + map + NPC |
| **Character panel** | Left column; **Backpack** / **Spells** tabs — engine data from bridge — APP-062 |

### Controls

| Input | Action |
|-------|--------|
| Enter | Submit to orchestrator |
| Escape | Save + quit |
| Narration toggle | Turn GM voice (TTS) on/off for the session — see [APP-058](backlog/app-058-ui-toggle-narration-tts-on-off.md) |
| Map click | Travel to cell (orchestrator handles) |

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

---

## Task checklist

- [x] Narration panel + rich text
- [x] Input box + history
- [x] Stats panel (HP, Fortune, Gold, Phase)
- [x] Map view + click travel
- [x] NPC card + sidebar

**Open work:** [APP-035](backlog/app-035-stats-panel-reads-engine-status.md)–[APP-037](backlog/app-037-block-map-travel-during-creation.md), [APP-058](backlog/app-058-ui-toggle-narration-tts-on-off.md), [APP-060](backlog/app-060-auto-scroll-narration-on-input-and-response.md), [APP-062](backlog/app-062-left-character-panel-inventory-spells-tabs.md), [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) in [`tmp/backlog/README.md`](backlog/README.md). _(APP-038 superseded by APP-062.)_

- [x] **APP-065:** Always-clear chips; code-owned player map + blocklist; no narration scrape (spec: [Suggestion chips](#suggestion-chips)).

---

## Tests

- Manual: scroll, history, map click sends travel string to orchestrator.
- **APP-065:** `python -m pytest app/tests/test_ui_suggestions.py -q` — builder map, blocklist, inactive-creation guard, equipment non-confirm path.
- **APP-065 regression:** `python -m pytest app/tests/test_creation_flow.py app/tests/test_session_resume_failure.py -q` — narration `Awaiting:` asserts unchanged.
- Future: headless panel unit tests for `rich_text.py` wrap logic.

---

## File map

| Path | Role |
|------|------|
| `ui/app.py` | Main loop, thread-safe narration updates |
| `ui/theme.py` | Colors, fonts |
| `ui/rich_text.py` | Wrapped styled text |
| `ui/panels/*.py` | Panel widgets |
| `ui/suggestions.py` | Player chip maps + blocklist (APP-065) |
| `tests/test_ui_suggestions.py` | APP-065 unit tests for chip builder |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created from app/README architecture |
| 2026-05-20 | APP-065 draft: suggestion chip source-of-truth, blocklist, always-clear (PM) |
| 2026-05-20 | APP-065 r2: equipment non-confirm path, inactive-creation lookup, error-path refresh, pytest commands |
| 2026-05-20 | **APP-065 done:** `ui/suggestions.py` + `get_player_suggestions()`; unconditional turn refresh; narration scrape removed; 17 unit tests |
