# Research Brief: APP-023-friendly-travel-av-grid

**Date:** 2026-05-22
**Question:** How does surface travel resolve destinations today, what canon data exists for friendly names, and where should APP-023 add AV-GRID resolution without inventing fake arrivals?

**backlog_ticket:** APP-023
**ticket_path:** tmp/backlog/app-023-friendly-travel-name-to-av-grid.md
**domain_spec:** tmp/app-exploration-delve-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Exploration & delve** already owns travel/site tools (`play/tomb_gm/services/world.py`, orchestrator + map UI). No new domain spec file is required; PM adds an APP-023 section and changelog to the existing owner.

## Summary

Surface travel today accepts **only canonical AV-GRID ids**. `WorldService.can_travel` validates graph edges; it does not parse prose or display names. `GameBridge.world_travel` and the CLI `world travel --to` pass `to_address` straight through — unknown strings return `UNKNOWN_ADDRESS`. `process_beat` travel lines use regex `AV_ADDRESS_RE` only; vague phrases like “kings road” yield `NO_DESTINATION` with a prompt to name an address (spec Problem log).

Dungeon/site entry already solved friendly resolution: `play/tomb_gm/services/site_resolve.py` scores queries against `displayName` (and site JSON), scoped to **current cell children** then global layered cells, with `AMBIGUOUS_SITE` / `UNKNOWN_SITE` errors. **`enter_dungeon`** in `app/gm/bridge.py` calls this resolver before `enter_site`. **No equivalent exists for surface travel.**

Canon data: every grid cell has `displayName` in `build/data/av-grid/av-grid.json` (schema field, no `aliases` array). Procedural coast cells reuse names heavily (**155** case-insensitive duplicate `displayName` values across **1560** surface cells). Resolution **must** prefer **`WorldService.legal_exits(from_address)`** candidates (and likely **surface-only** `layerStack == []` for road/place travel) before any global scan — otherwise “Silversea cove” would be unusable.

Recommended shape: add `resolve_surface_address` (or shared helper) in **`play/tomb_gm/services/world.py`**, reuse scoring patterns from `site_resolve.py`, wire **`bridge.world_travel`** (and **`beat.py`** for `process_beat` parity — see risks). Optional secondary match on `tradeRoute` enum (e.g. `kings-road` on 32-C) after displayName. JSON alias index is **not** required for MVP if scoring + exit scoping is strict.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Travel validation | `play/tomb_gm/services/world.py` | `legal_exits`, `can_travel`, `unknown_address_error`; **no name resolution** |
| Site name resolution (pattern) | `play/tomb_gm/services/site_resolve.py` | `_match_score`, slug normalize, child-first scope, ambiguity |
| Beat travel parse | `play/tomb_gm/services/beat.py` | `AV_ADDRESS_RE`, `_find_address`, `_intent_travel`, `NO_DESTINATION` |
| App bridge | `app/gm/bridge.py` | `world_travel` L184–208; `enter_dungeon` uses `resolve_site_address` L628–666 |
| LLM tools | `app/gm/tools.py` | `world_travel.to_address` described as AV-GRID only |
| Orchestrator dispatch | `app/gm/orchestrator.py` | `world_travel` → `bridge.world_travel(**args)` |
| Map UI | `app/ui/app.py` | Click submits `travel to {addr}` — already canonical ids |
| Compass / exits payload | `play/tomb_gm/services/exploration.py` | `compass_exits` includes neighbor `displayName` |
| Content load | `play/tomb_gm/services/content.py` | `get_cell`, `cell_payload` expose `displayName` |
| Canon grid | `build/data/av-grid/av-grid.json`, `schema.json` | `displayName` required on cells; `tradeRoute` enum includes `kings-road` |
| CLI parity | `play/tomb_gm/cli/cmd_world.py` | `handle_travel` — same strict address check |
| Tests | `play/tomb_gm/tests/test_world.py`, `test_beat.py`, `test_site_resolve.py` | Address-only travel tests; site resolve tests are the template |

## Code-path traces

### world_travel (LLM tool / bridge)

1. Entry: `app/gm/orchestrator.py` — `_execute_tool` → `bridge.world_travel(**args)` (`to_address` from tool schema).
2. `app/gm/bridge.py:world_travel` — loads `party_state.address`, builds `WorldService` + `ContentService`.
3. `world.can_travel(from_addr, to_address)` — `get_cell` must exist; `to_address` must be in `legal_exits(from)` unless same cell.
4. On success: UPDATE `party_state` address, `log_event` `world_travel`, return `cell` payload with `displayName`.
5. On failure: `ok: false`, `error` ∈ `UNKNOWN_ADDRESS`, `INVALID_TRAVEL`, `UNKNOWN_FROM_ADDRESS` — **no resolution attempt**.

### process_beat travel (vague name failure path)

1. Entry: `bridge.process_beat` → `play/tomb_gm/services/beat.py:process_beat`.
2. Per line: `_intent_travel` if verbs/direction+road detected.
3. `dest = _find_address(text, content)` — **only** `\d{1,2}-[A-Z](…)` matches in uppercased text.
4. `travel_hint` without dest: picks `legal_exits[0]` (compass default) — not name-based.
5. If no `dest`: mechanical result `error: NO_DESTINATION`, message asks for AV-GRID (e.g. 33-C).
6. **No bridge hook** — stays in engine `beat.py` unless shared resolver called from both.

### enter_dungeon (existing friendly resolution — reference)

1. `bridge.enter_dungeon` normalizes `site_address` / `site_id` query.
2. `resolve_site_address(content, query, current_surface_address=…)` — child `childAddresses` first, then layered cells globally.
3. Returns `site_address` or structured error; bridge then `enter_site` + phase advance.

### Map click (already canonical)

1. `app/ui/app.py` — map click → `_submit(f"travel to {map_addr}")` with grid id from `MapView`.
2. Orchestrator may call `world_travel` or `process_beat` depending on LLM; ids already valid when map is used.

### Legal exits from Breley (fixture)

From `32-C` today: `['31-C', '32-B', '32-C-UG-1', '32-C-UG-2', '32-D', '33-C']` with `33-C` → **"King's Road (east bend)"**. Query `kings road` should match `33-C` among exits, not global `"King's Road ford"` at `40-C`.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) — Surface play bullet: “friendly names should resolve to AV-GRID (engine)”; Problem: `process_beat` → `NO_DESTINATION` for “kings road”; Tests: `32-C` → `33-C`, vague travel helpful prompt.
- Bridge: [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) — `world_travel` listed; no friendly-name behavior yet.
- Related: [APP-063](../../../app-063-map-ux-redesign-useful-navigation.md) depends on APP-023 for travel strings.
- Canon grid README: `build/data/av-grid/README.md` — `displayName` clerk-facing title.
- AGENTS.md: JSON wins; grid edits need validate + build-index.

## Tests & commands

```bash
# Engine travel (address-only today)
python -m pytest play/tomb_gm/tests/test_world.py -q
python -m pytest play/tomb_gm/tests/test_beat.py -q

# Template for scoring / ambiguity
python -m pytest play/tomb_gm/tests/test_site_resolve.py -q

# Spec regression (exploration)
python -m pytest app/tests/test_exploration_site_entry_gate.py -q

# After grid changes only
python build/tools/av_grid.py validate
python build/tools/av_grid.py build-index
```

Suggested new cases (PM/Dev): from `32-C`, `world_travel(to_address="kings road")` → `33-C`; `process_beat` line “travel to kings road” → same; ambiguous duplicate displayName among exits → `AMBIGUOUS_*`; unknown → `NO_DESTINATION` / `UNKNOWN_ADDRESS` with exit list hint, **no** `ok: true` travel.

## Risks & unknowns

- **Duplicate `displayName` (155 groups)** — global name lookup will mis-resolve; exit-scoped candidate set is mandatory (PM must spec).
- **Child addresses in `legal_exits`** — includes `32-C-UG-*`; “undercrypt” could match UG via beat travel vs `enter_dungeon` — clarify surface vs delve intent in spec.
- **Ticket Expected files omit `beat.py`** — spec Problem explicitly cites `process_beat`; implementation needs resolver call in `beat.py` or expanded ticket paths.
- **`tradeRoute` vs `displayName`** — 32-C has `tradeRoute: kings-road` but displayName “Breley Keep”; “kings road” should not move party to 32-C when already there.
- **Tool / prompt drift** — `tools.py` still says AV-GRID only; update description + exploration spec changelog on close.
- **CLI `cmd_world.py` not in Expected files** — dev-team may want parity for `tomb_gm world travel`.
- **No `aliases` in JSON** — adding alias arrays is optional; increases validate/build-index scope; MVP can slug-match `displayName` + `tradeRoute` within exits.
- **Did not run live PyGame** — trace-only; human playtest in Stage 7.

## Raw notes

- `site_resolve._match_score`: exact address 100, exact name 90, slug substring 70, name substring 60.
- `beat.py` `travel_hint` + no dest → first legal exit (east from 32-C is `33-C` if sorted? `legal_exits` is **sorted** — first is `31-C`, not 33-C) — direction+road hint behavior is separate from APP-023.
- `grep` `alias` under `build/data/av-grid` — **no matches**.
- King's Road cells: `33-C` “King's Road (east bend)”, `40-C` “King's Road ford”.
- `build/tools/av_grid.py:resolve_surface` — parses surface root from id; **not** friendly-name lookup (name collision with proposed API).
- Orchestrator does not pre-resolve `to_address` before bridge (unlike `enter_dungeon` normalization in bridge only).
