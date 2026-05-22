# Drift Check: APP-023-friendly-travel-av-grid

**backlog_ticket:** APP-023  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) | no | § Friendly surface travel resolution (APP-023), checklist `[x]`, changelog **APP-023 done** (2026-05-22) match `world.py`, `beat.py`, `bridge.py`, tests |
| Run [`spec.md`](./spec.md) R1–R7 | no | Verified against `resolve_surface_address`, scoring helpers, bridge pre-resolve, beat error map |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Exploration domain row unchanged; no registry gap |

## Code ↔ domain spec (APP-023 scope)

| Requirement | Code | Match |
|-------------|------|-------|
| Exit-scoped candidates from `legal_exits(from)` only | `_candidate_pool` L73–107; `resolve_surface_address` L146 | yes |
| Pass 1 surface-only; pass 2 layered fallback | `surface_only=True` L166–173; layered L187–215 | yes |
| Apostrophe folding before slug/substring | `_fold_apostrophes` L9–13; L144 | yes |
| Scoring tiers 100/90/80/70/60 + compound `tradeRoute` gate | `_display_match_score` L16–31; `_score_surface_candidate` L34–54 (`display_score > 0`) | yes |
| Skip current cell unless exact address match | `_candidate_pool` L82–94 | yes |
| Outcomes: resolved / ambiguous / unknown / `USE_ENTER_DUNGEON` | `_pick_best` L110–129; `resolve_surface_address` L174–223 | yes |
| Unknown message lists legal surface exit hints | `_surface_exit_hints` L57–70 | yes |
| **`bridge.world_travel`** pre-resolve when not exact exit id | `bridge.py` L201–208; preserve `from`/`to` on failure; `resolved_from` on success L226–227 | yes |
| **`process_beat`** shared resolver + error map | `beat.py` L450–468; `UNKNOWN_ADDRESS` → `NO_DESTINATION`; other errors pass through | yes |
| **`enter_dungeon`** unchanged (site resolver) | No edits to `resolve_site_address` path | yes |
| Map click unchanged (canonical ids) | No `map_view.py` edits | yes |

## Minor gap (non-blocking)

| Item | Spec | Code | Notes |
|------|------|------|-------|
| LLM tool schema `world_travel.to_address` description | Wiring table: AV-GRID id **or** friendly surface name on ticket close | `tools.py` L102 still AV-GRID-only | Ticket Expected files marks `tools.py` optional; behavior unaffected — defer to hygiene pass or Stage 7 |

## Ticket AC ↔ verification

| Ticket AC | Result |
|-----------|--------|
| Map friendly place names to AV-GRID for surface travel via engine `world.py` | ✓ `resolve_surface_address`; wired in `bridge.world_travel` + `process_beat` |

## Domain spec test matrix ↔ tests

| Case | Test | Result |
|------|------|--------|
| King's Road (`32-C` → `33-C`) | `test_resolve_surface_address_kings_road`, `test_beat_travel_friendly_kings_road`, `test_world_travel_friendly_kings_road_bridge` | ✓ |
| Canonical passthrough | `test_resolve_surface_address_canonical_passthrough`, CLI `test_world_travel_surface` | ✓ |
| Exit scope (global duplicate not in exits) | `test_resolve_surface_address_exit_scope` | ✓ |
| Ambiguity (two exits tie) | `test_resolve_surface_address_ambiguous` | ✓ |
| UG child → `USE_ENTER_DUNGEON` | `test_resolve_surface_address_use_enter_dungeon` | ✓ |
| Beat `UNKNOWN_ADDRESS` → `NO_DESTINATION` | `test_beat_travel_unknown_maps_no_destination` | ✓ |
| Stay put (road name not current cell) | `test_resolve_surface_address_kings_road_not_current_cell` | ✓ |
| Invalid edge after resolve | `test_resolve_surface_address_then_can_travel` | ✓ |

## Tests run

```bash
python -m pytest play/tomb_gm/tests/test_world.py play/tomb_gm/tests/test_beat.py play/tomb_gm/tests/test_site_resolve.py -q
```

**Result:** 32 passed in 9.05s

| Module | APP-023 tests | Result |
|--------|---------------|--------|
| `play/tomb_gm/tests/test_world.py` | T1, T3–T6, passthrough, can_travel chain, T8 bridge | ✓ |
| `play/tomb_gm/tests/test_beat.py` | T2 friendly travel, T7 `NO_DESTINATION` map | ✓ |
| `play/tomb_gm/tests/test_site_resolve.py` | Scoring regression (`_slug` unchanged) | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [x] Domain spec checklist + changelog — APP-023 done row added
- [ ] `python tmp/backlog/claim_ticket.py release APP-023 --done` — **orchestrator** (QA drift: not run)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § Friendly surface travel resolution matched implementation before drift; ticket AC, checklist tick, and changelog were the lagging artifacts.
- **`tools.py` schema description** — optional per ticket; noted for follow-up if LLM tool docs should mention friendly names.
- **CLI `cmd_world.py`** — unchanged per plan (optional parity); bridge + beat paths covered.
- **Human playtest:** Friendly travel from Breley hub deferred to Stage 7 `human-test-plan.md`.
