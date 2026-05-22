# Research Brief: APP-025-registry-hub-loop-test

**Date:** 2026-05-22
**Question:** What exists today for an automated **preparation → ingress → delve → extract** Registry hub loop test, and what is the smallest correct integration path via `GameBridge` / `app/tests/`?

**backlog_ticket:** APP-025
**ticket_path:** tmp/backlog/app-025-registry-hub-loop-integration-test.md
**domain_spec:** tmp/app-exploration-delve-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Exploration & delve** owns travel/site tools in orchestrator + map UI and links engine `site.py` / `world.py`. Hub phase transitions (`set_phase`, `enter_dungeon`, `exit_dungeon`) are wired through `GameBridge` extraction/site methods already documented in [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md). No new domain spec is required.

## Summary

There is **no** existing `app/tests/` module that covers the full hub extraction phase loop. Coverage is **fragmented** across engine tests (`test_site_resolve`, `test_world`, `test_site`) and app exploration **unit/integration** tests (`test_exploration_site_entry_gate`, `test_exploration_set_phase_delve_hint`) that mock LLM tool chains but stop at single-tool behavior.

A **bridge-direct** integration test is feasible today without LLM mocks: bootstrap an isolated workspace at **Breley Keep (`32-C`)** in **`preparation`**, call `enter_dungeon("32-C-UG-1" | "undercrypt")` (auto-walks **preparation→ingress→delve** via `advance_phase_for_dungeon_entry`), optionally `exit_dungeon()` (returns to **surface**, phase stays **`delve`**), then `set_phase("extract")`. Live probe confirmed all steps succeed with no roster required.

**APP-051** (open) targets a broader mock-LLM golden path (creation → undercrypt → one beat) under logging/QA spec; **APP-052** (open) is manual PyGame smoke only. **APP-025** should not wait on APP-051 — it can land first as a deterministic bridge test and later share a bootstrap helper if APP-051 adds one.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| App test scaffolding | `app/tests/conftest.py`, `helpers.py` | `isolated_workspace`, `bridge`, `orchestrator`, `mock_openrouter_client` |
| GameBridge hub APIs | `app/gm/bridge.py` | `session_start`, `world_travel`, `enter_dungeon`, `exit_dungeon`, `set_phase`, `compass_exits` |
| Phase FSM | `play/tomb_gm/services/extraction.py` | `PHASE_TRANSITIONS`, `set_phase`, `advance_phase_for_dungeon_entry` |
| Dungeon entry (app path) | `play/tomb_gm/services/exploration.py` | `ExplorationService.enter_site` → `mode=dungeon`; imports `breley-undercrypt.json` rooms |
| Site graph (CLI alt path) | `play/tomb_gm/services/site.py` | `enter_site` → `mode=site` + `site_node_id` — **not** the app `enter_dungeon` path |
| Surface travel | `play/tomb_gm/services/world.py` | `resolve_surface_address`, `WorldService.can_travel` |
| Orchestrator tool dispatch | `app/gm/orchestrator.py` | `enter_dungeon`, `exit_dungeon`, `world_travel`, `set_phase` |
| Tool schema | `app/gm/tools.py` | `enter_dungeon(site_address)`, `set_phase`, `exit_dungeon`, `world_travel` |
| Default hub | `play/tomb_gm/domain/session.py` | `DEFAULT_HUB_ADDRESS = "32-C"`, `DEFAULT_PHASE = "preparation"` |
| Canon site fixture | `build/data/sites/breley-undercrypt.json` | `primaryAddress: 32-C-UG-1`, entry node `chapel-stairs` |
| Golden-path patterns | `app/tests/test_creation_flow.py` | Full creation FSM (APP-057); ends at `Phase: preparation`, no delve |
| Exploration test helpers | `app/tests/test_exploration_site_entry_gate.py` | `_tool_call`, `_patch_llm_sequence`, `_surface_exploration_orchestrator` (reused by APP-022 tests) |
| Engine loop fragments | `play/tomb_gm/tests/test_site_resolve.py`, `test_world.py`, `test_site.py` | Phase advance, travel, site graph — not full app bridge loop |
| Economy slice (different ticket) | `play/tomb_gm/tests/test_extraction_slice.py` | buy→equip→loot→stash; no phase loop |

## Code-path traces

### Hub loop (recommended APP-025 test path — bridge-direct)

1. **Entry:** `app/tests/conftest.py:bridge` → `GameBridge(workspace=isolated_workspace).init()`
2. **Bootstrap session:** `bridge.campaign_new(...)` → `bridge.session_start(campaign_slug)` → party at `32-C`, `mode=surface`, `phase=preparation` (`play/tomb_gm/domain/session.py:start_session`)
3. **Preparation (assert):** `bridge.status()["party"]` → `phase=="preparation"`, `address=="32-C"`, `mode=="surface"`
4. **Ingress + delve (single call):** `bridge.enter_dungeon(site_address="32-C-UG-1")` (`app/gm/bridge.py:652`)
   - `resolve_site_address` (`play/tomb_gm/services/site_resolve.py`)
   - `ExplorationService.enter_site` → `mode=dungeon`, `site_id=32-C-UG-1`, entry room from authored graph (`exploration.py:376`)
   - `advance_phase_for_dungeon_entry` → `set_phase(ingress)` then `set_phase(delve)` when starting from `preparation` (`extraction.py:65–79`)
   - Logs `phase.set` events `{from: preparation, to: ingress}` and `{from: ingress, to: delve}`
5. **Delve (assert):** `status()["party"]` → `phase=="delve"`, `mode=="dungeon"`, `site_id=="32-C-UG-1"`
6. **Exit site (optional but realistic):** `bridge.exit_dungeon()` → `ExplorationService.exit_site` → `mode=surface`, `site_id=NULL`; **phase remains `delve`**
7. **Extract:** `bridge.set_phase("extract")` → `phase=extract` (legal transition `delve→extract` per `PHASE_TRANSITIONS`)
8. **Persistence:** SQLite `party_state` + `sessions.phase` updated; `events` table holds `phase.set` audit trail

**Live probe (2026-05-22):** all steps above returned `ok: True` on isolated workspace with no character roster.

### Alternate: orchestrator + mock LLM (APP-051 style, not required for minimal AC)

1. **Entry:** `conftest.orchestrator` + `mock_openrouter_client`
2. **Post-creation surface:** `_surface_exploration_orchestrator` pattern from `test_exploration_site_entry_gate.py` (`setup_new_game`, `creation.active=False`)
3. **Tool chain:** `_patch_llm_sequence` returning tool_calls for `enter_dungeon` → optional `exit_dungeon` → `set_phase(extract)`
4. **Exit:** `orchestrator.process_turn(...)` → real bridge calls via `orchestrator._execute_tool`

Heavier than bridge-direct; useful if ticket later requires tool-arg normalization or narration gates in the same test module.

### Surface travel (optional prep beat — APP-023)

1. **Entry:** `bridge.world_travel(to_address="kings road")` from `32-C`
2. **Resolver:** `resolve_surface_address` → `33-C` (`play/tomb_gm/services/world.py`)
3. **Assert:** `status()["party"]["address"]=="33-C"`, phase unchanged (`preparation`)
4. **Reference test:** `play/tomb_gm/tests/test_world.py:test_world_travel_friendly_kings_road_bridge` (uses `GameBridge` + isolated workspace)

Not in ticket AC; useful regression if PM wants “hub prep includes surface travel” in the same module.

### What **not** to use for this ticket

| Path | Why |
|------|-----|
| `bridge.site_enter` / CLI `handle_site_enter` | Sets `mode=site` + node graph — different from app `enter_dungeon` dungeon-room model |
| `set_phase("delve")` from `preparation` | Rejected by FSM; APP-022 tests document hint-only behavior |
| `world_travel("32-C-UG-1")` | Layered address → APP-023 `USE_ENTER_DUNGEON`; must use `enter_dungeon` |
| `registry_stamp_buy` | Engine CLI only (`extraction.py`); **not** exposed on `GameBridge` or LLM tools |

## Existing specs & docs

- **Ticket domain spec:** [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) — lists APP-025 as open work; tests section cites engine extraction slice + exploration gate tests, not hub loop
- **GameBridge:** [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) — `enter_dungeon`, `exit_dungeon`, `set_phase`, `world_travel`
- **Logging/QA:** [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) — fixture inventory; APP-051 golden path still open
- **Canon loop:** [`build/systems/world/extraction.md`](../../../build/systems/world/extraction.md) — five phases; preparation includes stamp/equip fiction; extract = leave site with salvage
- **Related tickets:** APP-021 (enter_dungeon arg, done), APP-024 (site-entry gate, done), APP-051/052 (golden path / manual smoke, open), APP-085 note (future Holt quest scenario, out of scope v1)

## Tests & commands

```bash
# Existing related suites (none cover full hub loop)
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py -q
python -m pytest play/tomb_gm/tests/test_world.py -q
python -m pytest play/tomb_gm/tests/test_site.py -q

# Proposed gate after implementation
python -m pytest app/tests/test_registry_hub_loop.py -q   # name TBD by Dev
python -m pytest app/tests -q
```

## Risks & unknowns

| Risk | Detail | Mitigation for PM/Dev |
|------|--------|------------------------|
| **Ingress not observable via `status()` mid-call** | `advance_phase_for_dungeon_entry` runs synchronously inside `enter_dungeon`; only final `phase=delve` visible on status | Assert `events` rows `phase.set` with `preparation→ingress→delve`, or document ingress as implicit sub-step |
| **Dual site models** | `mode=site` (CLI graph) vs `mode=dungeon` (ExplorationService rooms) | Pin test to `bridge.enter_dungeon` + `32-C-UG-1`; do not call `site_enter` |
| **Extract vs exit_dungeon** | `exit_dungeon` does **not** set `extract`; player/GM must `set_phase("extract")` while phase is still `delve` | Test must call both for full AC; spec should state this explicitly |
| **APP-051 overlap** | Both want undercrypt entry; APP-051 adds creation + beat + mock LLM | Keep APP-025 bridge-only; optional shared `bootstrap_hub_session(bridge)` helper in `helpers.py` if both land |
| **No stamp in bridge loop** | Registry stamp buy is canon preparation activity but not on GameBridge | Out of scope unless ticket AC expanded; phase=`preparation` at hub is sufficient |
| **Roster optional** | Probe succeeded without `character_create` | Dev may still add minimal roster if future gates require living delver |
| **APP-087 dependency** | Ticket notes Holt Q&A on surface for quest scenario | Optional post-APP-085 scenario; not blocking minimal loop test |

## Raw notes

- **Default hub:** `start_session` → `32-C` Breley Keep, `phase=preparation`, `mode=surface`
- **Undercrypt resolution:** queries `undercrypt`, `breley-undercrypt`, `32-C-UG-1` all resolve from `32-C` (`test_site_resolve.py`)
- **Exploration tests use `23-A-UG-1`** for entry gate mocks — different site than Registry hub fixture; APP-025 should prefer **`32-C-UG-1`**
- **`test_extraction_slice.py`** is economy inventory vertical slice at `32-C` but session phase seeded `delve` and never walks FSM
- **`test_creation_flow.py`** ends with `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` — creation golden path stops before delve
- **APP-030** combat integration (batch peer) follows similar “new `app/tests/test_*.py`” pattern
- **Batch board:** APP-025 in research alongside APP-030, APP-077
