# Implementation Plan: APP-036-creation-step-badge

**Status:** draft  
**backlog_ticket:** APP-036  
**ticket_path:** tmp/backlog/app-036-creation-step-badge-in-ui.md  
**domain_spec:** tmp/app-pygame-ui-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add a **Registry intake step badge** in the right-sidebar stats panel, sourced from orchestrator FSM truth (`creation.active` + `creation.step`) — never narration scrape or coarse engine `awaiting` alone ([APP-065](../../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md), [APP-066](../../../app-066-sync-engine-awaiting-with-creation-step.md)).

Follow the **APP-037 enrichment template** already shipped:

1. **`creation.py`** — new `CREATION_STEP_DISPLAY` map (player-facing labels, separate from `CREATION_STATUS_LABELS` footer tokens).
2. **`orchestrator.py`** — `get_creation_step_badge()` helper (mirror `is_map_travel_blocked()` placement ~L348).
3. **`app.py`** — extend existing `_enrich_status_for_ui` with `creation_step` / `creation_step_display`; no new queue message type; refresh cadence unchanged (init + `_queue_turn_status` in turn `finally`).
4. **`stats.py`** — read enriched keys; draw `Registry: {label}` pill at **top** of stats region when set.
5. **`test_ui_creation_badge.py`** — helper, enrich, panel state, exception path, resize preserve.

**Label policy:** Badge shows `CREATION_STEP_DISPLAY[step]` (e.g. `Skills`), **not** `CREATION_STATUS_LABELS` values (`SKILLS_INPUT`). Narration `Awaiting:` footer remains unchanged (APP-007 / APP-073).

**Resize hazard:** `Sidebar._do_layout` recreates `StatsPanel` on every `resize()` (same as pre-APP-037 `MapView`). Badge draw state must survive resize — cache last badge fields on `Sidebar` and re-apply after layout (mirror APP-037 map-block cache). Minimal `sidebar.py` change is required despite spec “optional” wording; without it, window resize mid-intake drops the badge until next status push.

**Out of scope:** Domain spec prose (PM draft complete); changelog on ticket close only. Left character panel (APP-062). Engine `awaiting` sync (APP-066).

---

## Code-path traces (current → planned)

### Flow A — `CREATION_STEP_DISPLAY` + fallback (`creation.py`)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `creation.py:CREATION_STATUS_LABELS` | L85–96: footer tokens | unchanged |
| 2 | same (new) | — | **`CREATION_STEP_DISPLAY`** dict immediately after labels (spec R1 table) |
| 3 | same (new) | — | **`format_creation_step_display(step: str) -> str`** — map lookup or `_` → space + `.title()` fallback |
| 4 | `CREATION_STEPS` | L20–31 | unchanged — R1 test asserts every step has display label |

**Display map (locked by spec):**

| Step | Badge label |
|------|-------------|
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

**Invariant:** no value in `CREATION_STEP_DISPLAY.values()` may appear in `CREATION_STATUS_LABELS.values()`.

---

### Flow B — `get_creation_step_badge()` (orchestrator)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:is_map_travel_blocked` | L348–355 | unchanged |
| 2 | same (new) | — | **`get_creation_step_badge() -> dict \| None`** adjacent to map helper |
| 3 | new method | — | `if not self.creation.active: return None` |
| 4 | same | — | `step = self.creation.step`; `display = format_creation_step_display(step)` |
| 5 | same | — | `return {"step": step, "display_label": display}` |
| 6 | `export_creation_state` | L446–449 | unchanged — badge uses live `CreationState`, not export dict |

**Truth table (R2):**

| `creation.active` | `creation.step` | `awaiting` | `roster` | Badge |
|---------------------|-----------------|------------|----------|-------|
| True | `SKILLS` | any | any | `{"step": "SKILLS", "display_label": "Skills"}` |
| True | `WORLD_INTRO` | any | any | `{"step": "WORLD_INTRO", "display_label": "Reception"}` |
| False | `WORLD_INTRO` (stale) | `CHARACTER_CREATION` | `[]` | **`None`** (hide; differs from map desync guard) |
| False | any | `PLAYER_ACTIONS` | non-empty | **`None`** (post-finalize) |

**Forbidden:** derive step from `bridge.status()["awaiting"]` or narration `Awaiting:` line.

---

### Flow C — Status enrichment (extend APP-037)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `app.py:_enrich_status_for_ui` | L341–349: map keys only | **Add** creation badge keys after map block |
| 2 | `app.py:_init_orchestrator` | L127–128: enrich → put status | unchanged path — picks up new keys automatically |
| 3 | `app.py:_queue_turn_status` | L351–358 | unchanged — calls enrich |
| 4 | `app.py:_process_turn` finally | L320–322 (approx) | unchanged — already queues status on success + exception |
| 5 | `app.py:_process_ui_queue` | L174–176: sidebar update | unchanged — stats receives enriched dict via sidebar delegate |
| 6 | `app.py:_load_session` | restore + sync | **No new hook required** — QA note: first turn `finally` or init refresh carries badge; optional follow-up: queue enriched status immediately after load if playtest shows gap |

**Planned enrich extension (pseudocode):**

```python
def _enrich_status_for_ui(self, status: dict) -> dict:
    if not self._orchestrator:
        return status
    out = dict(status)
    # existing map_travel_blocked block (APP-037) ...
    badge = self._orchestrator.get_creation_step_badge()
    if badge:
        out["creation_step"] = badge["step"]
        out["creation_step_display"] = badge["display_label"]
    else:
        out["creation_step"] = None
        out["creation_step_display"] = None
    return out
```

**Refresh cadence:** identical to APP-037 / APP-065 — init push + every turn `finally` (including exception path covered by `test_process_turn_exception_queues_enriched_status` pattern).

---

### Flow D — StatsPanel render + Sidebar resize survival

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `stats.py:__init__` | L14–31 | Add `self.creation_step_display: str \| None = None` |
| 2 | `stats.py:update_from_status` | L39–77 | Read `creation_step_display`; set/clear field (ignore `creation_step` for draw — display string is sufficient) |
| 3 | `stats.py:draw` | L87–101: name then phase | **Insert** Registry badge **before** character name when `creation_step_display` truthy |
| 4 | badge draw | — | Copy: `Registry: {label}`; `FONT_SIZE_SMALL`; rounded rect; bg **`COLOR_CLERK`** from `theme.py` L25; text dark `(20, 20, 20)` like phase pill |
| 5 | phase coexistence | L95–101 | unchanged below name — both visible during intake |
| 6 | `sidebar.py:update_from_status` | L33–44 | **Cache** `_creation_step_display` / `_creation_step` from status; delegate to stats |
| 7 | `sidebar.py:_do_layout` | L20–31 | After new `StatsPanel(...)`, **re-apply** cached badge via `stats.update_from_status({...})` or small `set_creation_badge(display)` helper on stats |
| 8 | `sidebar.py:resize` | L60–62 | unchanged formula |

**Draw order (top → bottom):**

```text
[Registry: Skills]   ← only when creation_step_display set
Character name (— during intake)
Phase badge (PREPARATION)
HP / Fortune / …
```

When inactive: omit badge row entirely (no reserved blank space).

---

### Flow E — Step advance + finalize hide

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `process_turn` → `_creation_turn` | `CreationState.advance()` updates `creation.step` |
| 2 | turn `finally` | `_queue_turn_status` → enriched `creation_step_display` updates |
| 3 | `_auto_finalize` | `creation.active = False` |
| 4 | next status push | `get_creation_step_badge()` → `None`; stats clears badge |
| 5 | narration footer | may still show `RECEPTION_CHOICE` via `format_creation_status` — badge hidden per R2 desync guard |

---

## Task breakdown

### 1. Display map — `app/gm/creation.py`

1. Add `CREATION_STEP_DISPLAY` per spec R1 table (all 10 `CREATION_STEPS` keys).
2. Add `format_creation_step_display(step: str) -> str`:
   - `return CREATION_STEP_DISPLAY.get(step) or step.replace("_", " ").title()`
3. Export for orchestrator import (add to existing orchestrator imports block if convenient).

---

### 2. Orchestrator helper — `app/gm/orchestrator.py`

1. Import `format_creation_step_display` from `gm.creation`.
2. Implement `get_creation_step_badge()` per spec R2 (active guard first).
3. Place immediately after `is_map_travel_blocked()` (~L356).

---

### 3. Enrich status — `app/ui/app.py`

1. Extend `_enrich_status_for_ui` with creation keys (preserve existing map keys).
2. No changes to `_queue_turn_status`, `_init_orchestrator`, or `_process_turn` wiring — already correct from APP-037.

---

### 4. StatsPanel + Sidebar resize — `app/ui/panels/stats.py`, `app/ui/panels/sidebar.py`

1. **stats.py:** state field, `update_from_status` reader, draw Registry pill at top.
2. **sidebar.py:** cache badge fields on `update_from_status`; re-apply after `StatsPanel` recreation in `_do_layout`.

---

### 5. Tests — `app/tests/test_ui_creation_badge.py` (new)

| Test | Covers |
|------|--------|
| `test_creation_step_display_covers_all_steps` | Every `CREATION_STEPS` key in map; no display value ∈ `CREATION_STATUS_LABELS.values()` |
| `test_format_creation_step_display_fallback` | Unknown slug → title-case |
| `test_get_creation_step_badge_active` | `creation.active=True`, step `SKILLS` → `{"step": "SKILLS", "display_label": "Skills"}` |
| `test_get_creation_step_badge_inactive` | `creation.active=False` → `None` (even with stale step + `CHARACTER_CREATION` awaiting) |
| `test_enrich_status_for_ui_creation_fields` | Mock orch: active badge → keys set; inactive → both `None` |
| `test_stats_panel_shows_badge_from_status` | Headless: `update_from_status({"creation_step_display": "Race"})` → internal field set |
| `test_stats_panel_clears_badge_when_none` | `creation_step_display=None` clears field |
| `test_sidebar_resize_preserves_creation_badge` | Status with badge → `resize()` → stats still has display (APP-037 mirror) |
| `test_process_turn_exception_queues_creation_badge` | Extend APP-037 exception test: mock `get_creation_step_badge` → assert enriched status includes creation keys |

Use `orchestrator` / `app_config` fixtures from `conftest.py`; pygame dummy driver for App/Stats/Sidebar tests.

**Regression fix (small, recommended):** Update `test_enrich_status_for_ui_payload` in `test_ui_map_creation_gate.py` to set `mock_orch.get_creation_step_badge.return_value = None` — otherwise `MagicMock()` is truthy and pollutes enriched payload after APP-036 lands.

---

### 6. Domain spec — `tmp/app-pygame-ui-spec.md`

PM draft complete (§ Creation step badge). **Impl:** append changelog row on **`release APP-036 --done`** only; mark checklist item done.

---

## Files (must ⊆ ticket Expected files)

| Path | Change |
|------|--------|
| `app/gm/creation.py` | `CREATION_STEP_DISPLAY`, `format_creation_step_display` |
| `app/gm/orchestrator.py` | `get_creation_step_badge()` |
| `app/ui/app.py` | Extend `_enrich_status_for_ui` |
| `app/ui/panels/stats.py` | Badge state + draw at top |
| `app/ui/panels/sidebar.py` | Cache + re-apply badge on resize (minimal) |
| `app/tests/test_ui_creation_badge.py` | New test module |
| `tmp/app-pygame-ui-spec.md` | Changelog on close only |

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| Focused | `python -m pytest app/tests/test_ui_creation_badge.py -q` | All new tests green |
| Map enrich regression | `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | Green after mock fix |
| Creation FSM | `python -m pytest app/tests/test_creation_flow.py -q` | Badge hidden post-finalize |
| Resume | `python -m pytest app/tests/test_creation_restore.py -q` | Restored step → correct label on status push |
| Chips parity | `python -m pytest app/tests/test_ui_suggestions.py -q` | No regressions |
| Manual | New game → sidebar `Registry: Name` → advance steps → finalize → badge gone | Badge never shows `NAME_INPUT` / footer tokens |

---

## Rollback / flags

- Pure UI signal + display map + one orchestrator helper — no config flag.
- Rollback: revert seven files; narration footer and FSM unchanged.

---

## Open questions

1. **`_load_session` immediate badge** — Spec R3 satisfied by next status push (init after new game, turn `finally` after resume). If resume playtest shows blank badge until first input, add enriched status queue in `_load_session` after `_sync_creation_from_status` (same pattern as APP-037 open question #2).
2. **Sidebar scope creep** — Ticket Expected files omit `sidebar.py`; resize cache is required for R4/R5 AC. Treat as necessary wiring (≤10 lines), not optional.
3. **`test_ui_map_creation_gate.py` touch** — Not in Expected files; one-line mock fix prevents false failure — impl should include.

---

## Implementation order

1. `CREATION_STEP_DISPLAY` + `format_creation_step_display` + map coverage unit test.
2. `get_creation_step_badge()` + orchestrator unit tests.
3. Extend `_enrich_status_for_ui` + enrich tests (fix map gate mock).
4. `StatsPanel` draw + `Sidebar` resize cache.
5. Exception-path + resize integration tests.
6. Full pytest regression suite; manual intake walkthrough.
7. Ticket close: domain changelog + `release APP-036 --done`.
