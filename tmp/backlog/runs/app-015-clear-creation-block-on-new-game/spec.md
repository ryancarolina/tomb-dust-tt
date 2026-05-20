# Spec: APP-015-clear-creation-block-on-new-game

**Status:** draft  
**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**registry_gap:** false  
**Domain specs touched:** tmp/app-session-persistence-spec.md (§ New game — creation block clear)

## Summary

Stale `creation_state` in `app/session_state.json` can survive **`new game`** when `setup_new_game()` returns early or when autosave runs before in-memory reset. **Authoritative behavior** is in the domain spec; this file is the run-local index.

## Problem

- Creation block is cleared only at the **end** of a successful `setup_new_game()` via `_delete_save_file()` (whole-file unlink).
- `campaign_new` failure skips memory reset and disk clear; UI `_save_session()` in `finally` can **rewrite** the old block.
- `_is_mid_creation_resume_failure()` reads disk `creation_state` and misclassifies recovery after a failed wipe.

## Goals

- Clear creation persistence **first** on every `new game` attempt, before fragile engine steps.
- Satisfy ticket AC: **explicit** `session_state.json` `creation_state` reset, not only implicit delete on success.

## Non-goals

- APP-014 session-end ordering (`end_session` / `force_close_all_sessions` before wipe).
- APP-016 `engine_status` snapshot on save.
- APP-018 continue / load-game restore of creation.
- APP-019 UI toast for `new game` failures.
- UI-only clear on `clear_narration` queue.
- Stripping non-creation keys from `session_state.json` unless required for the creation block AC.

## Requirements (pointer)

| ID | Topic | Domain spec |
|----|--------|-------------|
| **C1** | Order: in-memory + disk clear before APP-014 L1/L2 (`end_session` / `wipe_all_data`) | § New game — creation block clear |
| **C2** | Disk: surgical `creation_state` = fresh NAME export | same |
| **C3** | All exit paths (incl. `campaign_new` failure) | same |
| **C4** | Batch boundaries vs APP-014 / APP-016 | same |
| **C5** | Tests T-015a–c | § Tests APP-015 |

## Acceptance criteria (ticket)

- [x] On **new game**, explicitly clear `session_state.json` **creation block** (mapped to **C1–C3** in domain spec).

## Test plan

```bash
python -m pytest app/tests -q -k "creation_block or new_game_creation"
python -m pytest app/tests -q -k "creation_flow or session_resume"
```

See domain spec § Tests APP-015 for case IDs.

## Human playtest hints (Stage 7)

- Mid-creation (e.g. SKILLS) → inspect `app/session_state.json` → **new game** → file must not retain prior `step` / `name` / `roll_result`.
- Force or simulate `new game` failure (if reproducible) → reload app → **load game** must not show variant B copy referencing old step from disk.
- Happy path: **new game** from stuck partial creation → clerk at **NAME**, not prior step.

## Affected paths

- `app/gm/orchestrator.py` — `setup_new_game`, new `_clear_creation_block_on_disk` (or equivalent), callers unchanged except ordering.
- `app/tests/` — new or extended test module for on-disk `creation_state` (isolated temp path or cleanup).
- **Out of scope unless Dev proves necessary:** `app/ui/app.py` (orchestrator-first clear must make UI `finally` save idempotent).

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | PM draft — pointers to domain spec § New game — creation block clear |
