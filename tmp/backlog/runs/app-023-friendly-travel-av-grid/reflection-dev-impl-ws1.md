# Dev implementation reflection — APP-023 (WS1)

**backlog_ticket:** APP-023  
**Date:** 2026-05-22

## What shipped

1. **`resolve_surface_address`** in `play/tomb_gm/services/world.py` — exit-scoped two-pass resolver (surface pass 1, layered pass 2) with apostrophe folding, compound-gated `tradeRoute` scoring (80 only when display tier > 0), and structured errors (`AMBIGUOUS_ADDRESS`, `UNKNOWN_ADDRESS`, `USE_ENTER_DUNGEON`).

2. **Scoring helpers** — `_fold_apostrophes`, `_display_match_score` (100/90/70/60), `_score_surface_candidate`, `_surface_exit_hints`, shared `_candidate_pool` / `_pick_best`.

3. **`bridge.world_travel`** — pre-resolve when `to_address` is not an exact member of `legal_exits`; fail closed on resolver errors; optional `resolved_from` on success.

4. **`process_beat` travel branch** — `_extract_travel_destination` strips travel verbs; calls resolver when `_find_address` misses and intent is `travel` (not `travel_hint`); maps `UNKNOWN_ADDRESS` → `NO_DESTINATION`.

5. **Tests** — T1, T3–T6, T8 in `test_world.py`; T2, T7 in `test_beat.py`; `test_site_resolve.py` regression green.

## Deviations / notes

- No `app/gm/tools.py` description update — optional on close per plan.
- No domain spec changelog — close-time artifact, not impl Expected files.
- `_pick_best` returns a small internal dict for ambiguity vs success — keeps beat/bridge error mapping simple.
- T8 uses `_bootstrap_session` + `GameBridge` directly (no `bridge.init()` — DB already migrated via `run_tomb_gm("init")`).

## Verification

```text
python -m pytest play/tomb_gm/tests/test_world.py play/tomb_gm/tests/test_beat.py play/tomb_gm/tests/test_site_resolve.py -q
32 passed in 9.59s
```

## Risks / follow-ups

- `_extract_travel_destination` may miss edge phrasings (e.g. trailing "travel") — plan notes follow-up if playtest fails.
- CLI `cmd_world.py` still canonical-only — parity deferred.
- Compound gate depends on live JSON display names; no grid edits required for King's Road fixture.
