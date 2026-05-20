# Research Brief: APP-016-snapshot-engine-status-on-save

**Date:** 2026-05-20
**Question:** Where does the app persist session state today, and how should `bridge.status()` be snapshotted on save so downstream reconcile/load tickets (APP-017, APP-018) have engine truth at save time?

**backlog_ticket:** APP-016
**ticket_path:** tmp/backlog/app-016-snapshot-engine-status-on-save.md
**domain_spec:** tmp/app-session-persistence-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) owns `session_state.json`, autosave, and reconcile policy (“App save and engine SQLite must reconcile”). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row: **Session persistence** → that spec. APP-016 is additive schema on an existing owner; no new `tmp/app-*-spec.md` required.

## Summary

Mid-creation drift (Dumpy session) stems from `session_state.json` storing rich `creation_state` while the engine may show `awaiting: CHARACTER_CREATION` with an empty `roster`. Saves today copy only `session_id` / `campaign_slug` from a partial `get_status()` call; they do **not** persist `awaiting`, `roster`, `party`, or `combat`. The domain spec already requires reconcile but does not yet define a saved engine snapshot field.

**APP-016 scope (write path only):** extend `_save_session()` in `app/ui/app.py` to call `Orchestrator.get_status()` → `GameBridge.status()` → `play/tomb_gm/cli/cmd_core.handle_status` and store the full dict (recommend key **`engine_status`**, matching APP-005 JSONL `creation_finalize`). All save triggers already funnel through `_save_session` (60s autosave, Escape quit, post-turn `finally` in `_process_turn`).

**Out of scope for this ticket’s AC:** reading the snapshot on load (APP-017, APP-018), trimming payload size, or changing boot/`has_save()` behavior. PM should document the new field in the session-persistence spec; implementers should not break backward compatibility when `engine_status` is absent on old saves.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| App save / load | `app/ui/app.py` | `SAVE_PATH`, `_save_session`, `_load_session` |
| Orchestrator status | `app/gm/orchestrator.py` | `get_status()`, `_restore_history()`, resume → `_sync_creation_from_status` |
| Bridge | `app/gm/bridge.py` | `status()` → `handle_status` |
| Engine status | `play/tomb_gm/cli/cmd_core.py` | `handle_status` — `awaiting`, `roster`, `party`, `combat`, `active` |
| Creation FSM | `app/gm/creation.py` | `CreationState.to_dict()` exported as `creation_state` |
| Prior art (JSONL) | `app/gm/orchestrator.py`, `app/gm/logger.py` | `_log_creation_finalize_status` logs full `engine_status` on finalize (APP-005) |
| Session eligibility | `play/tomb_gm/domain/session.py` | `has_save_session` / `find_save_campaign` (engine save ≠ app save) |

## Code-path traces

### Save (all triggers → one writer)

1. **Autosave:** `App._autosave` every 60s → `_save_session()`
2. **Quit:** `QUIT` / `K_ESCAPE` → `_save_session()`
3. **Post-turn:** `_process_turn` `finally` (when narration produced) → `_save_session()`
4. **`_save_session`:** builds `data` dict; calls `get_status()` only to extract `active.session_id` and `campaign_slug` (errors swallowed)
5. **Persisted today:** `session_id`, `campaign_slug`, `narration_lines`, `input_history`, `visited_cells`, `current_address`, `orchestrator_history`, `creation_state`, `combat_state`
6. **Gap:** no `awaiting` / `roster` / full `party` snapshot at save time

### Load (consumer context for APP-017/018)

1. **Trigger:** player types `load game` / `continue` → `_process_turn` queues `load_session` **before** `process_turn`
2. **`_load_session`:** restores UI + `import_creation_state` / `import_combat_state`; then `_sync_creation_from_status` / `_sync_combat_from_status` from **live** `get_status()`; overwrites map address from `party` if present
3. **Orchestrator resume:** `session_resume()` → on success with `CHARACTER_CREATION` + empty roster → `_restore_history()` reads `session_state.json` for creation/history only (not engine snapshot)
4. **Mid-creation failure detection:** `_is_mid_creation_resume_failure()` already reads saved `creation_state` **and** live `bridge.status()` — would benefit from saved `engine_status.awaiting` when DB is empty/stale

### Engine `status()` shape (reconcile-relevant)

From `handle_status` when session row exists:

- `awaiting`: `CHARACTER_CREATION` (no roster, no chars), `ROSTER_SETUP`, `PLAYER_ACTIONS`, `COMBAT_TURN`, `DYING`/`DOWNED`, `SESSION_ENDED`
- `roster`: slotted characters (HP, spells, etc.)
- `party`: `address`, `phase`, `mode`, site/dungeon fields
- `combat`: round/turn when active
- `active`: session metadata including `campaign_slug`

## Existing specs & docs

- **Ticket domain spec:** `tmp/app-session-persistence-spec.md` — § Spec reconcile bullet; § Problem (empty roster + app save); file map lists `session_state.json` but no `engine_status` field yet
- **Parent:** `tmp/app-master-spec.md` — Session persistence row
- **Related open tickets:** APP-017 (reconcile on load), APP-018 (restore creation when `CHARACTER_CREATION`), APP-035 (UI reads live status, separate)
- **Closed pattern:** APP-005 logs `engine_status` to JSONL on finalize — same payload source, different sink

## Tests & commands

```bash
# After implement — assert new key on save (isolated workspace via app/tests conftest):
cd app && python -m pytest app/tests -q -k "save or session"  # extend or add test_save_includes_engine_status

# Manual: mid-creation, wait for autosave or Escape, inspect session_state.json:
cd app && python main.py
# Expect: "engine_status": { "awaiting": "CHARACTER_CREATION", "roster": [], ... }

# Engine session tests (regression, no app save):
python -m pytest play/tomb_gm/tests -q -k session
```

**Suggested test (PM/Dev):** headless `Orchestrator` + temp `SAVE_PATH` or monkeypatch `SAVE_PATH`; call `_save_session` logic; assert `engine_status["awaiting"]` matches `bridge.status()["awaiting"]` mid-creation.

## Risks & unknowns

- **Payload size:** full `handle_status` includes `characters`, `roster` spell lines — file may grow; trimming is a PM non-goal unless perf issues appear
- **Stale snapshot vs live DB:** save-time snapshot can disagree with DB at load; APP-017 must define precedence (likely live DB wins, snapshot used when engine session missing or for `awaiting` only)
- **Exception swallowing:** `_save_session` already ignores `get_status()` failures — snapshot may be `null`/omitted; reconcile code must handle missing `engine_status` on legacy files
- **Ticket Expected files** says `app/save/load code` — no such package; actual paths are `app/ui/app.py` (primary), spec update only unless orchestrator centralizes save later
- **No boot restore:** spec says app save not read at launch; snapshot does not fix startup prompt without APP-017/018 read path
- **Batch coupling:** APP-014/015/016 run in parallel; 016 is independent write-only but 017/018 depend on this field existing

## Raw notes

- Live `app/session_state.json` (workspace): has `creation_state.step: SKILLS`, `session_id: "current"`, no `engine_status` — confirms gap
- `_save_session` lines 393–425 `app/ui/app.py`; `_load_session` 427–463
- `Orchestrator._restore_history` reads same path but only `orchestrator_history`, `creation_state`, `combat_state`
- Domain spec reconcile: “no PRE_DELVE in UI while engine `awaiting: CHARACTER_CREATION`” — needs saved `awaiting` when UI reloads without successful `session_resume`
- APP-071 variant B already uses live `creation_state` from file for mid-creation **resume failure**; APP-016 enables consistent **save-time** engine truth for load/reconcile
