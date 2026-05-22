# QA PASS: implementation — round 1

**Task:** app-023-friendly-travel-av-grid  
**backlog_ticket:** APP-023  
**ticket_path:** [tmp/backlog/app-023-friendly-travel-name-to-av-grid.md](../../app-023-friendly-travel-name-to-av-grid.md)  
**Round:** 1  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) § Friendly surface travel resolution (APP-023)

## Verdict

**PASS** — `resolve_surface_address` matches domain spec (exit-scoped two-pass resolution, apostrophe folding, compound `tradeRoute` gate). `bridge.world_travel` and `process_beat` share the resolver with correct error mapping. Plan tests T1–T8 green; site scoring regression unchanged.

## Automated tests

```text
python -m pytest play/tomb_gm/tests/test_world.py play/tomb_gm/tests/test_beat.py play/tomb_gm/tests/test_site_resolve.py -v
32 passed in 9.01s
```

| Module | APP-023 tests | Result |
|--------|---------------|--------|
| `play/tomb_gm/tests/test_world.py` | T1, T3–T6, passthrough, can_travel chain, T8 bridge | ✓ 10 new + 9 regression |
| `play/tomb_gm/tests/test_beat.py` | T2 friendly travel, T7 `NO_DESTINATION` map | ✓ 2 new + 3 regression |
| `play/tomb_gm/tests/test_site_resolve.py` | Scoring regression (unchanged `_slug`) | ✓ 9 pass |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Map friendly place names to AV-GRID for surface travel via engine `world.py` | `resolve_surface_address` in `play/tomb_gm/services/world.py`; wired in `app/gm/bridge.py` + `play/tomb_gm/services/beat.py` | ✓ |

## Spec R1–R7 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Exit-scoped two-pass resolver | `_candidate_pool` surface-only pass 1, layered pass 2; `legal_exits(from)` scope only | ✓ |
| **R2** | Apostrophe fold + compound-gated exit `tradeRoute`; exclude current cell | `_fold_apostrophes`, `_score_surface_candidate` (route tier only when display tier > 0); skip `from_address` unless exact match | ✓ |
| **R3** | `AMBIGUOUS_ADDRESS` / `UNKNOWN_ADDRESS` + surface exit hints | `_pick_best` ambiguity branch; `_surface_exit_hints` in unknown message | ✓ |
| **R4** | Layered fallback → `USE_ENTER_DUNGEON` | Pass 2 single match returns `USE_ENTER_DUNGEON` with enter_dungeon message | ✓ |
| **R5** | `bridge.world_travel` pre-resolve | `bridge.py` L201–208: resolve when not exact exit id; preserve `from`/`to` on failure; `resolved_from` on success | ✓ |
| **R6** | `process_beat` shared resolver + error map | `beat.py` L450–468: `resolve_surface_address`; `UNKNOWN_ADDRESS` → `NO_DESTINATION`; other errors pass through | ✓ |
| **R7** | Canonical passthrough | Resolver L156–164; bridge skips resolve when query ∈ `legal_exits` | ✓ |

## Domain spec test matrix → tests

| Case | Test / evidence | Result |
|------|-----------------|--------|
| King's Road (`32-C` → `33-C`) | T1, T2, T8 | ✓ |
| Canonical passthrough | `test_resolve_surface_address_canonical_passthrough`, `test_world_travel_surface` (CLI) | ✓ |
| Exit scope (global duplicate not in exits) | T3 | ✓ |
| Ambiguity (two exits tie) | T4 | ✓ |
| UG child → `USE_ENTER_DUNGEON` | T5 | ✓ |
| Beat `UNKNOWN_ADDRESS` → `NO_DESTINATION` | T7 | ✓ |
| Stay put (not current cell for road name) | T6 | ✓ |
| Invalid edge after resolve | T1 + `test_resolve_surface_address_then_can_travel` (`can_travel` chain) | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `play/tomb_gm/services/world.py` | `resolve_surface_address`, scoring helpers, hints | ✓ |
| `play/tomb_gm/services/beat.py` | `_extract_travel_destination`; resolver in travel branch | ✓ |
| `app/gm/bridge.py` | Pre-resolve hook in `world_travel` | ✓ |
| `play/tomb_gm/tests/test_world.py` | T1, T3–T6, T8 + chain test | ✓ |
| `play/tomb_gm/tests/test_beat.py` | T2, T7 | ✓ |
| `app/gm/tools.py` | No change (optional on close) | ✓ deferred |
| `build/data/av-grid/av-grid.json` | No change | ✓ per plan |
| `play/tomb_gm/cli/cmd_world.py` | No change | ✓ per plan |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **`tools.py` description** | Plan §6 optional — still AV-GRID-only in schema; update at ticket close if desired. |
| **CLI friendly travel** | `cmd_world.py` unchanged per plan; bridge + beat paths covered. |
| **Domain spec / ticket close** | Behavior section matches impl; checklist ticks + impl-done changelog deferred to Stage 6 `release --done`. |
| **Human playtest** | Stage 7 `human-test-plan.md` not run in QA impl gate. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-023 --done` (optional `tools.py` hygiene, domain changelog, ticket AC ticks).  
**Stage 7:** Manual PyGame — `world_travel("kings road")` from Breley hub; unknown friendly name shows exit hints, no fake arrival.
