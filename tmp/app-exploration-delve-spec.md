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

---

## Blocker: content validation (blocks `tomb_gm check`)

`check` currently fails on invalid site edge type `"passage"`:

- `build/data/sites/boydon-undercroft.json` — 1 edge
- `build/data/sites/shadowfen-vaults.json` — 4 edges

Canonical types in `validate_content.py`: `door`, `archway`, `stairs`, `secret`, `hatch`, `collapse`.

**Decision:** Remap `passage` → `archway`, or add `passage` to `SITE_EDGE_TYPES`.

**Done when:** `validate_content.py` and `tomb_gm check` pass.

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
- [ ] Fix site `passage` edges (content — see Blocker above)
- [ ] Tool schema documents `enter_dungeon(site_address)` as primary arg
- [ ] On failed `set_phase(delve)`, orchestrator hints `enter_dungeon` + `compass_exits`
- [ ] Map friendly place names → AV-GRID for surface travel (engine `world.py`)
- [ ] Block site-entry fiction unless last tool was successful `enter_dungeon` / `site enter`
- [ ] Registry hub loop: preparation → ingress → delve → extract in tests

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
