# APP-063: Map UX redesign — useful navigation

| Field | Value |
|-------|-------|
| **ID** | APP-063 |
| **Type** | decision |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

The sidebar **map is confusing and barely helps navigation**. Players see a 3×3 AV-GRID with fog, terrain colors, and compass letters, but **cannot reliably use it to move** — `MapView.handle_click()` **always returns `None`** ([`app/ui/panels/map_view.py`](../../app/ui/panels/map_view.py)), while [`app/ui/app.py`](../../app/ui/app.py) and [`app/README.md`](../../app/README.md) claim click-to-travel works. The map does not show **legal exits**, **place names on cells**, **delve ingress**, or **hover detail** from engine `compass_exits`. This ticket requires **design work first** (documented in domain specs), then implementation aligned with exploration/travel rules.

## Problem (observed)

| Issue | Detail |
|-------|--------|
| **Clicks do nothing** | `handle_click` stubbed — no cell hit-testing or address return |
| **Fog hides options** | Adjacent cells unknown until visited — player can't see where they *can* go |
| **No exit semantics** | Map ignores `compass_exits` (terrain, danger, population, below/sites) |
| **Weak labeling** | Only current cell `displayName` below grid; grid cells are anonymous color squares |
| **Compass vs grid** | N/S/E/W labels without explaining row/column movement or blocked edges |
| **Dungeon mode** | Room + exit text list; exits not clickable; no graph/spatial context |
| **Docs lie** | README: “Clickable AV-GRID map — click cells to travel” |

## Acceptance criteria

### Phase A — Design (required before code)

- [ ] **Map design** section added to [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md): player goals, surface vs dungeon modes, what is shown/hidden, interaction model.
- [ ] **Travel integration** notes in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md): map click → `world_travel` / `enter_dungeon` / blocked when illegal (mirror engine `can_travel`).
- [ ] Decisions recorded (examples — pick/adjust in spec):
  - Show **adjacent legal exits** even if unvisited? (recommended: yes, from `compass_exits`)
  - Cell label: `displayName` short form vs AV-GRID id on hover
  - Click adjacent cell → `travel to {address}` or call bridge directly after validation
  - Danger/terrain **legend** (compact key)
  - Delve ingress: icon/list for `below` sites from compass data
  - Creation / combat: map disabled or read-only ([APP-037](app-037-block-map-travel-during-creation.md))

### Phase B — Implementation

- [ ] **`handle_click` / `handle_hover`** — hit-test grid cells; return target AV-GRID address or `None`; hover shows tooltip (name, terrain, danger, exit direction).
- [ ] **Engine-backed exits** — map refreshes from `compass_exits` (or status payload including compass) each turn; only **legal** adjacent cells clickable (or click shows “can't travel there”).
- [ ] **Cell labels** — at minimum show short name or symbol on visited/current/adjacent-exit cells.
- [ ] **Surface travel** — click submits valid move (via existing `_submit(f"travel to {addr}")` or direct `world_travel` with user feedback on failure).
- [ ] **Dungeon mode** — clickable exit list or room graph stub that sends `move_room` / direction intent (scope in design §).
- [ ] **Blocked states** — no travel clicks during character creation; combat behavior per design.
- [ ] README + spec match shipped behavior.

### Phase C — Verification

- [ ] Manual: at Registry hub (`32-C`), map shows named neighbors and at least one clickable exit; travel updates position.
- [ ] Manual: illegal cell not clickable or shows clear failure (no silent no-op).
- [ ] Optional: `app/tests/test_map_view.py` — hit-test math, compass → cell list parsing (no pygame display if feasible).

## Expected files

- `app/ui/panels/map_view.py`
- `app/ui/panels/sidebar.py`
- `app/ui/app.py`
- `app/gm/bridge.py` / `app/gm/orchestrator.py` _(if compass data pushed to UI status)_
- `app/README.md`
- `tmp/app-pygame-ui-spec.md`
- `tmp/app-exploration-delve-spec.md`
- `app/tests/test_map_view.py` _(optional)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update both domain specs (UI layout + exploration map/travel UX) with changelog.
3. Record design decisions in ticket **Notes** or spec § Map design.

## Notes

### Suggested design direction (starting point — not canon until spec updated)

**Surface (3×3 local view kept, made informative):**

- Center = you; ring = **compass_exits** directions with cell data.
- Unvisited but **reachable** cells: outlined + label (not full fog).
- Unreachable / off-grid: fog or dim.
- Gold border = current; icons for town/fortress; red/orange border = danger tier (keep existing colors + legend).
- Click neighbor → travel if `can_travel`; shift+click or tooltip for full AV-GRID id (optional).

**Dungeon:**

- Show current room name + **clickable exits** that send structured move commands.
- Optional phase 2: simple room graph from site state (larger ticket if needed — document deferral).

### Data sources

- AV-GRID: `build/data/av-grid/av-grid.json` (already loaded in `MapView._load_grid`)
- Live exits: `GameBridge.compass_exits()` / orchestrator status `exploration.compass`
- Travel validation: `world.can_travel(from, to)` via bridge

### Related tickets

| Ticket | Relationship |
|--------|--------------|
| APP-023 | Friendly name resolution for travel strings |
| APP-021 / APP-022 | enter_dungeon / delve hints — map should surface ingress |
| APP-037 | Block map during creation |
| APP-025 | Hub loop test may include map travel |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-063 --task map-ux-redesign
python tmp/backlog/claim_ticket.py release APP-063 --done
```
