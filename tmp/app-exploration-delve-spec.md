# Spec — App Exploration & Delve Play

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** exploration path in orchestrator, map travel UX, site/delve tools

**Engine/canon (not a separate tmp spec):** site JSON fixes in `build/data/sites/` per [`build/docs/engine-integration.md`](../build/docs/engine-integration.md)

---

## Spec

### Surface play

- Player describes actions or clicks map → `world_travel(to_address)` or `process_beat`.
- `compass_exits` / `world_exits` for directions; friendly names should resolve to AV-GRID (engine).
- Wilderness: `wilderness_encounter` when travel flags demand it.

### Delve play

- Enter site via **`enter_dungeon(site_address)`** — not `set_phase(delve)` alone.
- In site mode: `site_move`, `search_site`, `interact_feature`, `move_room`, `exit_dungeon`.
- Phase/clock transitions via bridge extraction services.
- **Never** narrate entering a site without successful `enter_dungeon` / `site_enter`.

### UI

- Map click sends travel intent; blocked during creation/combat as appropriate.
- **Map UX redesign** (design + implementation): [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) — compass-backed exits, labels, working clicks, dungeon exits.

---

## Site edge types (canon)

Canonical types in `validate_content.py` (`SITE_EDGE_TYPES`): `door`, `archway`, `stairs`, `secret`, `hatch`, `collapse`.

**Canon decision (2026-05-20, APP-001):** Legacy JSON types `passage` and `gap` are remapped to **`archway`** in site data — not added as new enum values. Optional edge metadata (e.g. `hazard`) is preserved on the edge object.

---

## Problem (from logs)

- `enter_dungeon(site_id=…)` — wrong param (bridge accepts alias)
- `set_phase(delve)` rejected from `preparation`
- `process_beat` travel → `NO_DESTINATION` for vague names (“kings road”)
- GM narrated entering crypt without tool commit

---

## Task checklist

- [x] `world_travel`, `process_beat`, `enter_dungeon` tools exposed
- [x] Map click → travel string to orchestrator
- [x] `enter_dungeon` accepts `site_address` and `site_id` alias in bridge

**Open work:** [APP-021](backlog/app-021-enterdungeon-primary-tool-arg.md)–[APP-025](backlog/app-025-registry-hub-loop-integration-test.md), [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Tests

- Travel `32-C` → `33-C` via tool; status address updates.
- Enter Breley Undercrypt from `32-C`; mode becomes site.
- Vague travel → `NO_DESTINATION` with helpful prompt, not fake arrival.

```bash
python -m pytest play/tomb_gm/tests/test_extraction_slice.py -q
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
```

---

## File map

| File | Role |
|------|------|
| `gm/orchestrator.py` | Exploration `_llm_loop` |
| `gm/tools.py` | `world_travel`, `enter_dungeon`, `site_*`, `process_beat` |
| `gm/system_prompt.py` | Delve entry rules |
| `ui/panels/map_view.py` | Click travel |
| `gm/bridge.py` | World/site/exploration methods |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged delve-travel + site-edge validation content |
| 2026-05-20 | APP-001: remapped `passage`/`gap` → `archway` in boydon-undercroft + shadowfen-vaults; unblocks validate_content / tomb_gm check |
