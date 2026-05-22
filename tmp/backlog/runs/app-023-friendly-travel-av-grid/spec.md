# Spec: APP-023-friendly-travel-av-grid

**Status:** draft  
**backlog_ticket:** APP-023  
**ticket_path:** [tmp/backlog/app-023-friendly-travel-name-to-av-grid.md](../../app-023-friendly-travel-name-to-av-grid.md)  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-exploration-delve-spec.md`

## Problem

Surface travel only accepts canonical AV-GRID ids. Friendly prose (“kings road”, “King's Road east bend”) fails at `bridge.world_travel` (`UNKNOWN_ADDRESS`) and `process_beat` travel (`NO_DESTINATION`) even when the destination is a **legal compass exit** with a matching `displayName`. **`enter_dungeon`** already resolves friendly site names via `resolve_site_address`; surface travel has no equivalent.

**Evidence:** Research brief traces; domain spec problem log; fixture `32-C` legal exit `33-C` → “King's Road (east bend)”.

## Goals

- Map friendly surface place names to AV-GRID ids **within legal exits from the current cell**.
- Share one engine resolver across **`world_travel`** and **`process_beat`** travel.
- Fail closed on ambiguity — never invent arrivals.

## Non-goals

| Deferred | Note |
|----------|------|
| JSON `aliases` array in `av-grid.json` | MVP uses `displayName` + `tradeRoute` scoring + apostrophe folding; no grid schema change |
| Global name index | 155 duplicate `displayName` groups forbid it |
| Map UX labels / click behavior | [APP-063](../../app-063-map-ux-redesign-useful-navigation.md) — depends on APP-023 strings |
| Site entry resolution | Existing `resolve_site_address` + `enter_dungeon` |
| `travel_hint` compass default (first sorted exit) | Separate beat behavior; not APP-023 |
| `build/tools/av_grid.py:resolve_surface` | Grid **tool** that parses surface root from a layered id — **not** the engine API **`resolve_surface_address`** (R1) |

## Requirements

Full behavior, scoring table, error shapes, and test matrix: **domain spec § [Friendly surface travel resolution (APP-023)](../../../app-exploration-delve-spec.md#friendly-surface-travel-resolution-app-023)**.

### Requirement summary

| ID | Summary | Locus |
|----|---------|-------|
| **R1** | `resolve_surface_address(content, query, from_address)` — exit-scoped; pass 1 surface candidates, pass 2 layered fallback | `play/tomb_gm/services/world.py` |
| **R2** | Scoring aligned with `site_resolve` + apostrophe folding + exit `tradeRoute` (80, **compound-gated**); no match on current cell for road names | `world.py` |
| **R3** | `AMBIGUOUS_ADDRESS` when tied best scores; `UNKNOWN_ADDRESS` with exit hint list | `world.py` |
| **R4** | Pass 2 layered fallback → `USE_ENTER_DUNGEON` when surface pass scores 0 but layered exit matches | `world.py` |
| **R5** | `bridge.world_travel` resolves before `can_travel` | `app/gm/bridge.py` |
| **R6** | `process_beat` travel calls same resolver when `_find_address` misses; map `UNKNOWN_ADDRESS` → `NO_DESTINATION` | `play/tomb_gm/services/beat.py` |
| **R7** | Canonical id passthrough unchanged | Both paths |

**Naming:** Engine API is **`resolve_surface_address`** in `world.py` — not `build/tools/av_grid.py:resolve_surface` (surface-root parser for grid tooling).

**Scoring proof (SPEC-001 / PLAN-001):** At `32-C`, query `kings road` → exit **`33-C`** ("King's Road (east bend)"), not route-only neighbor **`32-D`** ("Heartland mile post", `tradeRoute: kings-road`). **Compound gate:** `tradeRoute` tier 80 applies only when the same candidate also scores > 0 on display/address tiers. `32-D` display tier 0 → route suppressed; `33-C` slug substring **70** wins. Full exit table in domain spec § Matching proof table.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Map friendly place names to AV-GRID for surface travel via engine `world.py` | R1–R4; King's Road case; exit scope |
| Spec sync on close | Domain spec § APP-023 + changelog; optional `tools.py` description |

## Test plan

```bash
python -m pytest play/tomb_gm/tests/test_world.py -q
python -m pytest play/tomb_gm/tests/test_beat.py -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py -q
```

Primary cases (detail in domain spec):

| ID | Case | Pass |
|----|------|------|
| **T1** | `32-C` + `kings road` → `33-C` via resolver / `world_travel` | `ok: true`, address `33-C` |
| **T8** | `GameBridge.world_travel(to_address="kings road")` from `32-C` | `ok`; party at `33-C` |
| **T2** | `process_beat` line “travel to kings road” from `32-C` | Same destination; party moves |
| **T3** | Duplicate global name not in `legal_exits` | `UNKNOWN_ADDRESS`; no travel |
| **T4** | Two exits tie on score | `AMBIGUOUS_ADDRESS` + `options` |
| **T5** | Query matches UG child name only (`undercrypt`) from `32-C` | **`USE_ENTER_DUNGEON`** (layered fallback → `32-C-UG-1`); no UG `world_travel` |
| **T6** | At `32-C`, `kings road` does not resolve to `32-C` | Exit `33-C` |
| **T7** | Beat travel line; resolver `UNKNOWN_ADDRESS` | Beat `error: NO_DESTINATION` (message preserved) |

## Affected paths

| File | Change |
|------|--------|
| `play/tomb_gm/services/world.py` | **R1–R4** `resolve_surface_address` |
| `app/gm/bridge.py` | **R5** pre-resolve in `world_travel` |
| `play/tomb_gm/services/beat.py` | **R6** travel branch + error map |
| `play/tomb_gm/tests/test_world.py` | Resolver + bridge integration (T1, T3–T6, **T8**) |
| `play/tomb_gm/tests/test_beat.py` | Friendly travel beat line (T2) + error map (T7) |
| `app/gm/tools.py` | Tool description on close (optional same PR) |
| `tmp/app-exploration-delve-spec.md` | § APP-023 (PM draft) |

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Breley hub (`32-C`):** After creation, type **“travel to kings road”** or use LLM phrasing that calls `world_travel` with friendly name — party should land **`33-C`**, narration/map address updates.
- **Undercrypt:** Say **“travel to the undercrypt”** via beat/travel — should **not** surface-travel into UG; expect hint toward **`enter_dungeon`** / **`compass_exits`**.
- **Map click:** Still sends canonical ids — regression unchanged.
- **Ambiguity:** If two exits share a name on a test cell, expect failure message listing options, not silent wrong move.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — code traces, duplicate-name risk, King's Road fixture
- **Domain truth:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) — § Friendly surface travel resolution (APP-023)
- **Pattern:** `play/tomb_gm/services/site_resolve.py` — scoring/slug/ambiguity (site scope differs)
- **Bridge:** [tmp/app-gamebridge-spec.md](../../../app-gamebridge-spec.md) — `world_travel` row (update on close)
- **Downstream:** [APP-063](../../app-063-map-ux-redesign-useful-navigation.md) friendly labels depend on this resolver

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft — exit-scoped surface resolver, beat parity, UG vs enter_dungeon, T1–T6 |
| 2026-05-22 | PM r2 — apostrophe folding + scoring proof; layered fallback; beat error map; ticket Expected files; T5/T7 pinned; `resolve_surface` naming note |
| 2026-05-22 | Dev plan r2 — compound `tradeRoute` gate (PLAN-001); full `32-C` exit table; T8 bridge test (PLAN-002) |
