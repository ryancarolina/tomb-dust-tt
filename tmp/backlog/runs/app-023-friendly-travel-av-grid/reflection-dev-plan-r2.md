# Reflection: Dev — APP-023 plan (round 2)

**Agent:** Dev  
**Round:** 2  
**Deliverables:** `plan.md` (r2), `spec.md`, `tmp/app-exploration-delve-spec.md`, `reflection-dev-plan-r2.md`

## QA findings addressed

### PLAN-001 (blocker) — King's Road wrong winner

- **Root cause:** Exit `32-D` ("Heartland mile post") has `tradeRoute: kings-road` but no display-name match for `kings road`. Ungated tier **80** beat `33-C` tier **70**.
- **Fix chosen:** **Compound `tradeRoute` gate** (QA option 1) — score **80** only when the same candidate also scores > 0 on display/address tiers (60–100). Route metadata is a boost, not a standalone match.
- **Verification:** Ran `WorldService.legal_exits("32-C")` against live JSON — surface pass-1 candidates `{31-C, 32-B, 32-D, 33-C}`. Only `33-C` scores > 0 after gate. T1/T6/human playtest target restored without `av-grid.json` edit.

### PLAN-002 (major) — bridge test gap

- **Fix:** Added **T8** `test_world_travel_friendly_kings_road_bridge` in `play/tomb_gm/tests/test_world.py` (Expected files). Uses `GameBridge` + `isolated_workspace` (root `conftest.py` adds `app/` to path). Asserts `world_travel("kings road")` → `to == "33-C"` and party row updated.
- **Not done:** No `app/tests/` file — outside ticket Expected files; T8 covers R5 hook adequately.

## Policy rationale

Rejected alternatives:

| Option | Why not |
|--------|---------|
| Tie-break “road name” heuristic | Query-shape special case; fragile for non-road queries |
| Re-rank tradeRoute below slug globally | Breaks future cells where display + route both match and route should boost |
| JSON data fix on `32-D` | Ticket non-goal; 155-cell grid shouldn't need one-off edits for MVP resolver |

Compound gate matches design intent: players say place **names**; `tradeRoute` disambiguates when display text also references the route.

## Files updated

| File | Change |
|------|--------|
| `plan.md` | Flow C scoring helpers split; full `32-C` candidate table; T8 bridge test; R2/R5 map |
| `spec.md` | R2 compound gate; SPEC-001 proof; T8 row; changelog |
| `tmp/app-exploration-delve-spec.md` | Scoring table row 80 gated; proof table with all surface exits; changelog |

## Self-critique

- **Layered pass 2:** Compound gate applies same scoring table — layered candidates rarely have `tradeRoute`; undercrypt T5 unchanged (display 70 only).
- **T8 fixture bootstrap:** Plan references existing `_bootstrap_session` / bridge lifecycle patterns but does not paste full test code — Dev must mirror `test_setup_new_game_lifecycle` or `_bootstrap_session` at impl time.
- **Impl not started:** Scoring proof is plan-level trace only; no `resolve_surface_address` in repo yet.

## Handoff

**Ready for:** QA plan gate re-review — focus on full exit table, compound gate pseudocode, T8 feasibility.

**Escalate if:** Product wants route-only cells (mile posts) reachable by route enum alone — would need explicit tier reorder or data model, not compound gate.
