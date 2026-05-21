# Dev implementation reflection — APP-024

**backlog_ticket:** APP-024  
**Date:** 2026-05-21

## What shipped

1. **`sanitize_premature_site_entry_flavor`** (`app/gm/orchestrator.py`) — module-level helper with `_SITE_ENTRY_MARKER_RES` regex set (threshold crossing, interior reveal, false in-dungeon status claims). Line-oriented drop + paragraph fallback to empty when markers remain.

2. **`_SITE_ENTRY_REFUSAL_LINE`** — code-owned refusal when gate active and sanitizer empties prose (E6).

3. **Sticky `entry_committed_this_turn`** — reset at `_llm_loop` depth 0; set on first successful `enter_dungeon` / `site_enter`; never cleared within turn (E1). `_exploration_pre_turn_mode` snapshotted at depth 0 from `party.mode`.

4. **`_exploration_gate_active` / `_compose_exploration_narration`** — gate when surface + not committed; bypass when committed or pre-turn mode is `dungeon`/`site` (E2/E3). Compose helper documents APP-077 extension point (E9).

5. **Wiring** — `process_turn` snapshots `pre_turn_mode`, composes after `_llm_loop` before `_emit_narration`. `all_failed and content` early return composes `content` before failure banner (E5); restored `\n\n{safe}` append (had been stripped by APP-028 combat work on same block).

6. **`app/tests/test_exploration_site_entry_gate.py`** — seven tests: unit sanitizer + six integration paths (no-tool strip, failed enter, successful enter, success-then-failed sticky flag, site_enter, dungeon bypass).

## Deviations / notes

- E7 drift telemetry deferred (non-blocking per plan).
- Integration tests call `setup_new_game()` for active session, then force `creation.active = False` to reach exploration branch.
- `all_failed and content` path now returns sanitized safe prose beneath banner; idempotent second compose in `process_turn` when gate inactive or prose already clean.
- Domain spec sync (refusal copy, checklist, changelog) deferred to ticket `release --done`.

## Verification

```text
cd app && python -m pytest tests/test_exploration_site_entry_gate.py -v
7 passed in 2.17s
```

## Risks / follow-ups

- Marker regex set may over-strip wilderness prose mentioning "crypt" without crossing verbs — adjust fixtures if playtest reports false positives.
- APP-077 should append status footer inside `_compose_exploration_narration` after APP-024 strip (documented in helper docstring).
