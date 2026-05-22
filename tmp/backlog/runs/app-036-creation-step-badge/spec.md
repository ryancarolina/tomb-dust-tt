# Spec: app-036-creation-step-badge

**Status:** draft
**backlog_ticket:** APP-036
**ticket_path:** tmp/backlog/app-036-creation-step-badge-in-ui.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-pygame-ui-spec.md

## Problem

During Registry intake (`creation.active`), the only persistent indicator of the current desk step is the code-owned `Awaiting:` footer in the narration panel (`format_creation_status()`). The right sidebar shows HP, phase, and map but **no creation-step signal**.

`Orchestrator.get_status()` returns `bridge.status()` only — no `creation.active` or `creation.step`. `export_creation_state()` holds granular FSM truth but is **not** merged into the per-turn `("status", …)` UI queue today (same gap APP-037 fixed for map travel via `_enrich_status_for_ui`).

Engine `awaiting == CHARACTER_CREATION` is **coarse** for the entire intake period ([APP-066](../../../app-066-sync-engine-awaiting-with-creation-step.md)). The badge must read **`CreationState.step`**, not engine `awaiting` and **never** narration scrape ([APP-065](../../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md)).

## Goals

- Show a **creation step badge** in the right sidebar while `creation.active` is true.
- Display **human-readable** copy keyed by `creation.step` — **not** raw `CREATION_STATUS_LABELS` footer tokens (`SKILLS_INPUT`, `EQUIPMENT_GOLD_CONFIRMATION`, …).
- Source badge data from orchestrator via **`_enrich_status_for_ui`** (APP-037 pattern) on every status push (init + post-turn success/exception).
- Hide badge when `creation.active` is false (post-finalize, live roster).
- Document behavior in `tmp/app-pygame-ui-spec.md`.

## Non-goals

- Replacing or removing the narration `Awaiting:` footer (APP-007 / APP-073 — duplicate signal for sidebar clarity).
- Driving badge from engine `awaiting` alone or parsing GM narration.
- Showing blocklisted internal tokens on screen (APP-065 chip policy alignment).
- Left character panel / Backpack tab work — APP-062 (badge must survive future three-column layout).
- Syncing engine `awaiting` to granular step — APP-066.

## Requirements

### R1: Step display map (code-owned, step-keyed)

Add `CREATION_STEP_DISPLAY: dict[str, str]` in `app/gm/creation.py`, keyed by **`creation.step`** (same keys as `CREATION_STEPS` / `PLAYER_SUGGESTIONS_BY_CREATION_STEP`), **separate** from `CREATION_STATUS_LABELS` (footer/drift tokens).

| Step | Display label (badge text) |
|------|------------------------------|
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

Unknown step fallback: title-case from step slug (`ROLL_STATS` → `Roll Stats` via `_` → space + `.title()`).

**Acceptance criteria**

- [ ] Map lives in `creation.py` next to `CREATION_STATUS_LABELS`; values are **never** `CREATION_STATUS_LABELS` values.
- [ ] Unit test asserts every `CREATION_STEPS` entry has a display label and no display label equals a footer token from `CREATION_STATUS_LABELS.values()`.

### R2: Orchestrator badge helper

Introduce a single orchestrator accessor used by UI enrichment (mirror `is_map_travel_blocked()`):

```python
def get_creation_step_badge(self) -> dict | None:
    if not self.creation.active:
        return None
    step = self.creation.step
    from gm.creation import CREATION_STEP_DISPLAY  # or module-level import
    display = CREATION_STEP_DISPLAY.get(step) or _step_display_fallback(step)
    return {"step": step, "display_label": display}
```

| Rule | Detail |
|------|--------|
| **Show when** | `self.creation.active == True` |
| **Hide when** | `self.creation.active == False` — even if stale `creation.step` or engine `awaiting == CHARACTER_CREATION` |
| **Step truth** | `self.creation.step` — not `bridge.status()["awaiting"]` |
| **Label truth** | `CREATION_STEP_DISPLAY[step]` — not `CREATION_STATUS_LABELS[step]` |

**Acceptance criteria**

- [ ] Helper lives on `Orchestrator` in `app/gm/orchestrator.py`.
- [ ] Active creation at `SKILLS` → `{"step": "SKILLS", "display_label": "Skills"}`.
- [ ] Post-finalize (`creation.active == False`) → `None`, regardless of engine `awaiting`.
- [ ] Desync guard: inactive creation + empty roster + `CHARACTER_CREATION` awaiting → `None` (badge hidden; differs from map gate scope).

### R3: Enrich status payload (`_enrich_status_for_ui`)

Extend `app/ui/app.py` `_enrich_status_for_ui` (alongside existing `map_travel_blocked` keys from APP-037):

```python
badge = self._orchestrator.get_creation_step_badge()
if badge:
    out["creation_step"] = badge["step"]
    out["creation_step_display"] = badge["display_label"]
else:
    out["creation_step"] = None
    out["creation_step_display"] = None
```

| Rule | Detail |
|------|--------|
| **Refresh paths** | `_init_orchestrator` status push; `_queue_turn_status` in `_process_turn` `finally` (success + exception — APP-065/037 parity) |
| **Forbidden** | Regex on narration `Awaiting:`; inferring step from `status["awaiting"]` alone |
| **Session load** | After `_load_session` / `import_creation_state`, next status push carries enriched fields so badge matches restored step without waiting for a player turn |

**Acceptance criteria**

- [ ] Enriched keys present on every `("status", …)` enqueue when orchestrator is set.
- [ ] Step advances (NAME → RACE → …) update `creation_step_display` on next status push without reading narration.
- [ ] `_process_turn` exception path still queues enriched status (mirror APP-037 `test_process_turn_exception_queues_enriched_status`).

### R4: StatsPanel render (placement)

Render badge in **`StatsPanel`** at the **top of the stats region** — above character name and phase badge.

| Element | Detail |
|---------|--------|
| **Visibility** | Draw only when `creation_step_display` is non-empty string |
| **Copy** | Static prefix **`Registry:`** + display label (e.g. `Registry: Skills`) |
| **Style** | Reuse small-font badge pattern from phase pill (`FONT_SIZE_SMALL`, rounded rect); distinct color from `PHASE_COLORS` — e.g. clerk green `(80, 140, 80)` or `theme.COLOR_CLERK` if defined |
| **Phase coexistence** | Phase badge (`PREPARATION`, etc.) remains below character name during intake; creation badge is the primary intake signal at top |
| **Clear** | When `creation_step_display` is `None`, do not draw badge; panel height/layout unchanged (badge row omitted, not reserved) |

`Sidebar.update_from_status` delegates to `StatsPanel.update_from_status(status)` **and** caches `creation_step` / `creation_step_display` on the sidebar (mirror APP-037 `_map_travel_blocked`). After `_do_layout` recreates `StatsPanel`, re-apply cached badge fields so resize does not drop intake signal until the next status push.

**Acceptance criteria**

- [ ] Badge visible during mocked status push with `creation_step_display="Race"`.
- [ ] Badge hidden when `creation_step_display` is `None`.
- [ ] Sidebar resize (`_do_layout`) does not drop badge state — retest like `test_sidebar_resize_preserves_blocked` (APP-037).

### R5: APP-062 layout compatibility

Badge lives in right-sidebar **stats** sub-panel (`Sidebar._do_layout` stats half). No narration-header strip in v1. When APP-062 adds the left character panel, badge position unchanged (stats region top).

**Acceptance criteria**

- [ ] `Sidebar._do_layout` height formula unchanged; badge is draw-only state on `StatsPanel`.
- [ ] Domain spec notes compatibility with three-column shell.

### R6: Domain spec sync

Update `tmp/app-pygame-ui-spec.md` § Creation step badge (APP-036) with signal table, display map reference, enrichment cadence, placement, tests (PM delivers with this file).

**Acceptance criteria**

- [ ] Cross-reference APP-066 (step vs awaiting), APP-065 (no narration scrape), APP-037 (enrich pattern).
- [ ] Changelog entry on ticket close (impl stage).

## File map (implementation)

| Path | Change |
|------|--------|
| `app/gm/creation.py` | `CREATION_STEP_DISPLAY` map + optional `_step_display_fallback` |
| `app/gm/orchestrator.py` | `get_creation_step_badge()` |
| `app/ui/app.py` | Extend `_enrich_status_for_ui` with `creation_step` / `creation_step_display` |
| `app/ui/panels/stats.py` | Read enriched keys; draw Registry badge at top when set |
| `app/ui/panels/sidebar.py` | Cache badge fields on `update_from_status`; re-apply after `StatsPanel` recreation in `_do_layout` (APP-037 mirror) |
| `app/tests/test_ui_map_creation_gate.py` | Set `mock_orch.get_creation_step_badge.return_value = None` in `test_enrich_status_for_ui_payload` so unconfigured `MagicMock` does not pollute enriched payload |
| `tmp/app-pygame-ui-spec.md` | Behavior + tests + changelog on close |
| `app/tests/test_ui_creation_badge.py` | New — helper, enrich payload, StatsPanel state, sidebar resize preserve |

## Tests & commands

```bash
python -m pytest app/tests/test_ui_creation_badge.py -q
python -m pytest app/tests/test_ui_map_creation_gate.py -q   # enrich helper regression
python -m pytest app/tests/test_creation_flow.py -q          # badge hides post-finalize
python -m pytest app/tests/test_creation_restore.py -q       # resume restores step → badge
python -m pytest app/tests/test_ui_suggestions.py -q         # parallel creation.active guard
```

**Suggested test cases (`test_ui_creation_badge.py`):**

| Test | Assert |
|------|--------|
| `test_get_creation_step_badge_active` | Mock orchestrator at `SKILLS` → display `"Skills"`, step `"SKILLS"` |
| `test_get_creation_step_badge_inactive` | `creation.active == False` → `None` |
| `test_creation_step_display_not_footer_token` | No display label in `CREATION_STATUS_LABELS.values()` |
| `test_enrich_status_for_ui_creation_fields` | `_enrich_status_for_ui` adds/clears keys |
| `test_stats_panel_shows_badge_from_status` | `update_from_status` sets internal flag; optional headless draw skip |
| `test_stats_panel_clears_badge_when_none` | `creation_step_display=None` clears badge |
| `test_process_turn_exception_queues_creation_badge` | Exception `finally` still enriches (extend APP-037 test pattern) |
| `test_sidebar_resize_preserves_creation_badge` | Status with badge → `Sidebar.resize()` → stats still has display (APP-037 mirror) |

Manual: new game → sidebar shows `Registry: Name` → advance through race/class → label updates each step → after finalize badge gone while phase/map update.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-035 | Stats panel reads engine status via queue — badge same path |
| APP-037 | `_enrich_status_for_ui` / `_queue_turn_status` template |
| APP-065 | Same `creation.active` guard; never show footer tokens as UI copy |
| APP-066 | Granular step vs coarse engine `awaiting` |
| APP-062 | Layout — badge stable in stats region |
| APP-007 / APP-073 | Narration footer remains; badge is sibling signal |

## Human playtest hints (for Stage 7)

- Start new game: badge reads `Registry: Name` before first name entry; narration footer may show `Awaiting: NAME_INPUT` — badge must **not** show `NAME_INPUT`.
- Complete race step: badge updates to `Registry: Race` without relying on chip scrape.
- Finish full intake: after finalize, badge disappears; stats show live delver name/HP; map travel unblocked (APP-037).
- Save mid-creation (e.g. at Skills), restart app, resume: badge matches restored step immediately on load.

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft — enrich pattern, step-keyed display map, StatsPanel placement |
| 2026-05-22 | PM r2 — ticket Expected files + file map: `sidebar.py` resize cache (TICKET-001); `test_ui_map_creation_gate.py` mock fix (PLAN-002) |
