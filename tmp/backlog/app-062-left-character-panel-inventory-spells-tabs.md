# APP-062: Left character panel — inventory & spells tabs

| Field | Value |
|-------|-------|
| **ID** | APP-062 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Add a **new left-side column** in the PyGame window with a **tabbed panel**: **Backpack** (player inventory) and **Spells** (known spell list). The player clicks tab headers at the top of the panel to switch views. Data comes from the engine via `GameBridge` — not from LLM narration.

## Current layout

```text
[ Narration + input (~70%) | Right sidebar: NPC, stats, map (~30%) ]
```

Stats panel currently shows up to **4 spell names** as a footnote ([`app/ui/panels/stats.py`](../../app/ui/panels/stats.py)) — insufficient for inventory or full spell detail.

## Target layout

```text
[ Character panel (tabs) | Narration + input | Right sidebar ]
```

| Tab | Label (UI) | Content |
|-----|------------|---------|
| Default | **Backpack** | Active delver pack from `list_inventory()` — item display names; indicate equipped slots if available in pack data |
| Alternate | **Spells** | Known spells from `list_known_spells()` — name, tier, MP, school (match bridge spell objects / `spell_lines`) |

Tab bar at **top** of the left panel; clicking **Spells** / **Backpack** swaps the body; active tab visually distinct (theme-consistent with existing panels).

## Acceptance criteria

### Layout & interaction

- [ ] New **left column** panel; window layout updated in [`app/ui/app.py`](../../app/ui/app.py) (narration + right sidebar shrink accordingly).
- [ ] Width configurable via `config.yaml` (e.g. `ui.character_panel_width_ratio` or fixed min/max px) — document in domain spec.
- [ ] **Tab bar** at top: `Backpack` | `Spells`; click switches active tab; only one tab body visible.
- [ ] Panel **resizes** correctly on window resize (`VIDEORESIZE`).
- [ ] Panel **scrolls** internally if item/spell list exceeds height (wheel when mouse over panel).

### Data (engine-backed)

- [ ] **Backpack tab** populated from `GameBridge.list_inventory()` for active living PC — refresh when `status` UI queue message arrives (after each turn) and on session load.
- [ ] **Spells tab** populated from `GameBridge.list_known_spells(character_id)` — same refresh cadence.
- [ ] Empty states: no roster / character creation → show short placeholder (“No delver yet” / “No spells known”); not crash.
- [ ] Non-casters: Spells tab shows empty state or “No spells known”.

### UX polish

- [ ] Remove or trim redundant **Spells** block in stats panel (avoid duplicate lists) — document in spec if stats keeps MP only.
- [ ] Styling matches [`app/ui/theme.py`](../../app/ui/theme.py) (BG_SIDEBAR, borders, fonts).

### Spec & tests

- [ ] [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) — layout diagram, tab behavior, config keys, changelog.
- [ ] [`app-economy-inventory-play-spec.md`](../app-economy-inventory-play-spec.md) — UI touchpoint for pack display (if behavior noted there).
- [ ] Manual test checklist: new game → creation → after finalize backpack shows kit items; caster sees spells on Spells tab; tab switch works mid-session.

## Expected files

- `app/ui/app.py`
- `app/ui/panels/character_panel.py` _(new — tabs + backpack/spells subviews)_
- `app/ui/panels/stats.py` _(optional: remove spell list duplication)_
- `app/ui/theme.py` _(optional: tab colors)_
- `app/config.yaml`
- `tmp/app-pygame-ui-spec.md`
- `tmp/app-economy-inventory-play-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update domain spec(s) + changelog.
3. Cancel or close superseded ticket [APP-038](app-038-inventory-and-stash-summary-strip.md).

## Notes

### Bridge contracts

- `list_inventory()` → `{ ok, pack[], summary, goldGp, character_id }` — [`app/gm/bridge.py`](../../app/gm/bridge.py)
- `list_known_spells(character_id)` → `{ ok, spells[], spell_lines[], spell_schools[] }`

UI thread must not call bridge directly from draw — refresh via main thread on `status` queue event (orchestrator already pushes status after turns). Session init / load should trigger one refresh.

### Out of scope (follow-ups)

- Click-to-equip / click-to-cast (APP-039 consumables, combat tools).
- Account **stash** tab (hub-only; separate ticket if needed).
- Drag-and-drop inventory.
- **Quests tab** — [APP-085](app-085-quest-system-key-npc-quests-ui.md) adds third tab to this panel (same tab component).

### Related tickets

| Ticket | Relationship |
|--------|--------------|
| [APP-038](app-038-inventory-and-stash-summary-strip.md) | **Superseded** by this panel |
| [APP-039](app-039-gm-tool-for-useitem-and-consumables.md) | Future interact from inventory |
| [APP-085](app-085-quest-system-key-npc-quests-ui.md) | Quests tab + quest lifecycle (extends this panel) |
| [APP-061](app-061-expand-magic-schools-and-spell-catalog.md) | More spells to display |
| [APP-035](app-035-stats-panel-reads-engine-status.md) | **Done** — stats already engine-backed; APP-062 adds left panel without stats rework |
| [APP-036](app-036-creation-step-badge-in-ui.md) | Creation step badge — schedule with UI batch |
| [APP-037](app-037-block-map-travel-during-creation.md) | Block map travel during creation — right sidebar |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-062 --task character-panel-tabs
python tmp/backlog/claim_ticket.py release APP-062 --done
```
