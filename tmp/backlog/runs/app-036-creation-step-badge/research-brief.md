# Research Brief: APP-036-creation-step-badge

**Date:** 2026-05-22
**Question:** How should the PyGame UI show the current creation FSM step during Registry intake, sourced from orchestrator/engine state (not narration), and where should it live in the sidebar layout?

**backlog_ticket:** APP-036
**ticket_path:** tmp/backlog/app-036-creation-step-badge-in-ui.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md), which owns `app/ui/**` per [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **PyGame UI**. Creation step badge placement, refresh cadence, and display rules are UI concerns. FSM step truth and `CREATION_STATUS_LABELS` live in [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) / `app/gm/creation.py` — the UI reads orchestrator state, it does not own the FSM. No new domain spec file required.

## Summary

During `creation.active`, players only see the current desk step via the code-owned `Awaiting:` footer in the narration panel (`format_creation_status()`). There is **no persistent sidebar indicator** of which creation step is active.

**Same signal gap as APP-037 (now fixed for map):** `Orchestrator.get_status()` returns `bridge.status()` only — fields like `awaiting`, `roster`, `party`; **no** `creation.active` or `creation.step`. `export_creation_state()` returns `{active, step, …}` when `creation.active` else `None`; it is persisted to `session_state.json` on save but **not** merged into the per-turn `("status", …)` UI queue payload today. APP-037 solved this for map travel by enriching status in `_enrich_status_for_ui()` with orchestrator-derived flags (`map_travel_blocked`). APP-036 should follow the same enrichment pattern for creation step display.

**Label vocabulary tension (PM decision):** Ticket AC examples use step keys (`RACE`, `SKILLS`). `CREATION_STATUS_LABELS` maps steps to **footer tokens** (`RACE_INPUT`, `SKILLS_INPUT`, …) used in `Awaiting:` lines and drift checks. APP-065 explicitly **blocks** those tokens from suggestion chips as internal enums. The badge should **not** show raw `CREATION_STATUS_LABELS` values on screen — use step-derived **human-readable** text (e.g. title-case step name or a new display map) while sourcing **step truth** from `CreationState.step` / `export_creation_state()`, not from narration scrape.

**Visibility:** Show badge only when `creation.active` is true (ticket AC). Hide after finalize when `creation.active` is false and roster is live. Do **not** drive the badge from engine `awaiting == CHARACTER_CREATION` alone — engine awaiting is coarse for the entire intake period ([APP-066](../../../app-066-sync-engine-awaiting-with-creation-step.md)); character-creation spec already notes APP-036 must use `CreationState.step`, not engine `awaiting`.

**Placement:** Right sidebar `StatsPanel` already renders a phase badge below character name (`stats.py` L95–101). Ticket suggests above stats or narration header; **stats panel top** (above or replacing emphasis on phase during intake) fits APP-062 future three-column layout without new columns. APP-062 left character panel is **not shipped** — current layout is narration (~70%) + right sidebar (~30%).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Creation FSM + labels | `app/gm/creation.py` | `CREATION_STEPS`, `CREATION_STATUS_LABELS`, `CreationState`, `format_creation_status()`, `to_dict()` |
| Orchestrator exposure | `app/gm/orchestrator.py` | `creation.active`, `export_creation_state()`, `get_status()`, `_expected_creation_awaiting_label()` |
| UI status enrich (template) | `app/ui/app.py` | `_enrich_status_for_ui`, `_queue_turn_status`, init + turn `finally` refresh |
| Stats / sidebar | `app/ui/panels/stats.py`, `app/ui/panels/sidebar.py` | `update_from_status`; phase badge pattern; sidebar forwards enriched keys to map |
| Chip policy (no narration scrape) | `app/ui/suggestions.py`, `orchestrator.get_player_suggestions()` | Keys off `creation.step` when `creation.active`; ignores step when inactive |
| Map gate precedent (APP-037) | `orchestrator.is_map_travel_blocked()`, `test_ui_map_creation_gate.py` | Orchestrator helper + enrich + sidebar forward |
| Persistence | `app/ui/app.py` `_save_session` / `_load_session` | `creation_state` on disk; load triggers status refresh after sync |
| Theme / badge styling | `app/ui/theme.py` | `PHASE_COLORS`, `FONT_SIZE_SMALL`, `PANEL_PADDING` — reuse for intake badge |
| Cross-spec contract | `tmp/app-character-creation-spec.md` § Awaiting contract | Step truth = `CreationState.step`; footer labels = `CREATION_STATUS_LABELS` |

## Code-path traces

### Creation step truth (orchestrator)

1. Entry: `Orchestrator.__init__` → `self.creation = CreationState()` (`orchestrator.py` L341).
2. Active intake: `process_turn` → `if self.creation.active: return self._creation_turn(...)` — FSM advances via `_handle_creation_response` / `CreationState.advance()` (`creation.py` L236–253).
3. Export: `export_creation_state()` returns `self.creation.to_dict()` when `self.creation.active` else `None` (`orchestrator.py` L446–449). Dict includes `active`, `step`, `name`, `race`, table flags, etc. (`creation.py` L258+).
4. Footer (narration only today): `_compose_creation_narration` → `format_creation_status(self.creation)` → `"Awaiting: {CREATION_STATUS_LABELS[step]}"` (`creation.py` L654–657).
5. Post-finalize: `_auto_finalize` sets `creation.active = False`; `export_creation_state()` returns `None` — badge should hide.

### Engine status vs creation step (APP-066)

1. `get_status()` → `self.bridge.status()` only (`orchestrator.py` L345–346).
2. Engine `awaiting` stays `CHARACTER_CREATION` for entire empty-roster intake (`play/tomb_gm/cli/cmd_core.py` — coarse layer).
3. Granular step is **app-owned**: `CreationState.step` + `CREATION_STATUS_LABELS` for footers/drift (`_expected_creation_awaiting_label()` at L455–459).
4. **Badge must read `creation.step`**, not `status["awaiting"]`.

### UI refresh path (APP-035 / APP-037 pattern)

1. Init: `_init_orchestrator` → `_enrich_status_for_ui(get_status())` → `("status", status)` (`app.py` L127–128).
2. Each turn: `_process_turn` `finally` → `_queue_turn_status(turn_id)` → enrich → `("status", status)` (`app.py` L321–322, L351–358).
3. Main thread: `_process_ui_queue` → `sidebar.update_from_status(data)` (`app.py` L174–176).
4. **Today `_enrich_status_for_ui` only adds** `map_travel_blocked` / hint — no `creation_state` or step label.
5. Stats panel reads `roster`, `party` only — no creation fields (`stats.py` L39–77).

### APP-065 chip policy (parallel consumer of creation state)

1. `_queue_turn_suggestions` → `get_player_suggestions()` every turn (`app.py` L360–366).
2. `build_player_suggestions(creation_step=..., creation_active=...)` (`suggestions.py` L72–101):
   - If `creation_active` → lookup `PLAYER_SUGGESTIONS_BY_CREATION_STEP[creation_step]` (keys = FSM steps, not footer labels).
   - If `not creation_active` → **never** read `creation_step`; `CHARACTER_CREATION` awaiting → `[]`.
3. Blocklist rejects `CREATION_STATUS_LABELS.values()` and `UPPER_SNAKE_CASE` tokens (`suggestions.py` L37–57).
4. **Badge policy aligns:** orchestrator/session state, not narration; never display blocklisted internal tokens as the badge text.

### APP-037 map gate pattern (implementation template)

1. Orchestrator: `is_map_travel_blocked()` reads `self.creation.active` + `bridge.status()` dual condition (`orchestrator.py` L348–355).
2. Enrich: `_enrich_status_for_ui` attaches `map_travel_blocked`, hint (`app.py` L341–349).
3. Forward: `Sidebar.update_from_status` → `MapView.set_travel_blocked` (`sidebar.py` L33–41).
4. Tests: `test_ui_map_creation_gate.py` — enrich payload, sidebar forward, resize preserves state.
5. **APP-036 analog:** enrich with `creation_state` (or `{active, step, display_label}`); `StatsPanel` or `Sidebar` renders badge; hide when `active` false.

### Session load / resume

1. `_load_session` → `import_creation_state(data.get("creation_state"))` → `_sync_creation_from_status()` (`app.py` L473–475).
2. Status push after load should carry enriched creation flags so badge matches restored step without waiting for next player turn.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) — lists APP-036 in open work; stats panel engine-backed (APP-035 done); no creation badge section yet.
- Creation FSM: [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) — § Awaiting contract, full `CREATION_STATUS_LABELS` table; explicitly references APP-036 for step badge source.
- Related done tickets: APP-035 (stats from engine), APP-037 (enrich status pattern), APP-065 (no narration scrape), APP-066 (granular vs coarse awaiting), APP-007/073 (code-owned footer — duplicate signal, not badge source).
- Layout follow-on: [APP-062](../../../app-062-left-character-panel-inventory-spells-tabs.md) (open) — three-column shell; badge on right sidebar should remain stable.
- [`AGENTS.md`](../../../AGENTS.md) — app changes require ticket + domain spec changelog on close.

## Tests & commands

```bash
# Creation FSM + finalize (badge should hide after turn 8)
python -m pytest app/tests/test_creation_flow.py -q

# Chip policy / creation.active guard (parallel pattern)
python -m pytest app/tests/test_ui_suggestions.py -q

# Status enrich precedent (extend or mirror)
python -m pytest app/tests/test_ui_map_creation_gate.py -q

# Persistence / restore step truth
python -m pytest app/tests/test_creation_restore.py app/tests/test_engine_status_on_save.py -q
```

**Suggested new tests (impl):** `app/tests/test_ui_creation_badge.py` — enrich payload includes `creation_state` when active; `StatsPanel`/`Sidebar` shows step label when `active`; hidden when `export_creation_state()` is `None`; step updates across mocked status pushes (NAME → RACE → …); no assertion on narration text.

## Risks & unknowns

- **Display label map missing** — repo has `CREATION_STATUS_LABELS` (footer tokens) and `CREATION_STEPS` (enum keys) but no `CREATION_STEP_DISPLAY` for friendly UI copy. PM must pick: title-case step (`Roll Stats`, `Spell Schools`) vs prefixed copy (`Registry: Skills`) vs new dict in `creation.py`.
- **Ticket wording vs APP-065** — AC says "human label from `CREATION_STATUS_LABELS`"; those values are internal footer enums. Showing `SKILLS_INPUT` on a badge would violate chip-policy spirit. Recommend step-based display with optional mapping keyed by `creation.step`.
- **`creation.active` not in `bridge.status()`** — badge must not infer step from narration `Awaiting:` or engine `awaiting` alone; requires enrich from orchestrator (same lesson as APP-037 research).
- **Empty roster during intake** — stats panel shows `character_name = "—"`; phase badge may still show `PREPARATION` from `party.phase`. Creation badge and phase badge may coexist — clarify visual hierarchy (intake badge above phase, or muted phase during intake).
- **Desync edge** — `creation.active == false` + stale `creation.step == WORLD_INTRO` + empty roster: map gate blocks (APP-037 desync guard); ticket AC says hide badge when not `creation.active` — badge hidden even if engine still `CHARACTER_CREATION`. Intentional difference from map gate scope.
- **APP-062 layout shift** — left panel will shrink narration width; stats panel height formula (`sidebar._do_layout`) unchanged for map block — badge draw must survive sidebar resize (retest like `test_sidebar_resize_preserves_blocked`).
- **WORLD_INTRO / post-finalize** — `creation.active` false before reception narration completes; badge hidden per AC even if footer shows `RECEPTION_CHOICE`.
- **No headless stats draw tests today** — APP-035 shipped with manual playtest; badge may need pygame dummy driver tests like map gate.

## Raw notes

### `CREATION_STATUS_LABELS` (footer tokens — not recommended as badge text)

| Step | Footer label |
|------|----------------|
| NAME | NAME_INPUT |
| RACE | RACE_INPUT |
| ROLL_STATS | STATS_REVIEW |
| CLASS | CLASS_INPUT |
| SKILLS | SKILLS_INPUT |
| SPELL_SCHOOLS | SPELL_SCHOOLS_INPUT |
| SPELLS | SPELLS_INPUT |
| EQUIPMENT_GOLD | EQUIPMENT_GOLD_CONFIRMATION |
| FINALIZE | FINALIZE |
| WORLD_INTRO | RECEPTION_CHOICE |

### Recommended enrich shape (implementation hint — not spec)

```python
# app/ui/app.py _enrich_status_for_ui
cs = self._orchestrator.export_creation_state()
if cs:
    out["creation_state"] = cs
    out["creation_step_display"] = format_step_for_badge(cs["step"])  # PM-owned copy
else:
    out["creation_state"] = None
```

Optional orchestrator helper: `get_creation_ui_badge() -> dict | None` mirroring `is_map_travel_blocked()` / `get_player_suggestions()` — keeps label derivation in one place.

### Placement sketch (current layout)

```text
[ Narration + input (~70%) | Sidebar: NPC | Stats (+ creation badge?) | Map ]
```

Phase badge in stats today: colored pill with `phase.upper()`. Creation badge could sit **above** phase row with distinct color (e.g. clerk green from `COLOR_CLERK`) and static prefix "Intake" or "Registry".

### Acceptance mapping

| Ticket AC | Research recommendation |
|-----------|-------------------------|
| Visible badge while `creation.active` | Enrich status with `export_creation_state()`; render in `stats.py` or `sidebar.py` |
| Human step label | Derive from `creation.step`; do not scrape narration; avoid raw `CREATION_STATUS_LABELS` values on screen |
| Hidden after finalize | When `export_creation_state()` is `None` / `active` false, clear badge |
| Engine/orchestrator source | `_enrich_status_for_ui` + orchestrator fields; never `Awaiting:` parse |
| APP-062 layout | Right sidebar stats region; avoid narration header unless PM prefers |
| APP-065 alignment | Same refresh cadence as status queue; same `creation.active` guard as chips |

### Batch

`batch-board-APP-032-APP-036-APP-060.md` — APP-036 in_progress with APP-060 (auto-scroll) in same batch.
