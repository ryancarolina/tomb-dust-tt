# Dev reflection — APP-017 WS1

**backlog_ticket:** APP-017  
**stream:** WS1 — Orchestrator reconcile helpers + sync prelude + resume trim  
**file:** `app/gm/orchestrator.py`

## What shipped

| Item | Notes |
|------|--------|
| `_read_saved_engine_status` | Reads `engine_status` dict from `_session_state_path()`; missing/parse/null → `None` |
| `_effective_awaiting_for_reconcile` | Live non-`SETUP` wins; cold `SETUP` falls back to saved snapshot awaiting |
| `_force_creation_active_if_reconcile_needed` | Idempotent; sets `creation.active = True` only when live roster empty, not `ROSTER_SETUP`, effective awaiting is `CHARACTER_CREATION` |
| `_sync_creation_from_status` prelude | APP-018 `getattr` restore hook → force-active reconcile before body |
| Sync body guard | `characters` → **`roster`** for mid-creation empty check (C3); C3 uses **`_effective_awaiting_for_reconcile`** so live `SETUP` + saved `CHARACTER_CREATION` is not clobbered by C4 else branch (T-017b) |
| `process_turn` resume trim | Removed inline `active=True` + `WORLD_INTRO→NAME` clobber; defensive `_force_creation_active_if_reconcile_needed()` if still inactive after sync |

## Constraints honored

- Force helper sets **`creation.active` only** — no `step=NAME` (R4 / APP-018 owns step restore).
- Empty roster checks use **live** `roster` only in force gate; saved roster never overrides (R2 / T-017c2).
- `ROSTER_SETUP` explicit no-op in force helper (R3 / T-017f).
- No edits to `app/ui/app.py`, APP-015/016 save paths, or `_restore_history`.
- APP-018 `_restore_creation_from_session_state` integrated via prelude `getattr` — not duplicated.

## Deviations / risks

- Resume success path still calls `_restore_creation_from_session_state()` before `_sync_creation_from_status()` (APP-018 G3c); sync prelude calls restore again — second call is no-op via once-only guard.
- **C3 fix (post-review):** Body elif now uses `_effective_awaiting_for_reconcile` — without this, prelude force-active was undone by C4 `else` when live `awaiting == SETUP` (T-017b failure).

## Verification

- `python -m py_compile app/gm/orchestrator.py` — OK
- `PYTHONPATH=../play python -c "from gm.orchestrator import Orchestrator; print('import ok')"` from `app/` — OK
- WS2 tests (`test_reconcile_empty_roster_on_load.py`) not written in this stream — T-017a–f required before ticket close.

## Handoff to WS2

- Patch `_session_state_path` to tmp save fixtures; exercise `_sync_creation_from_status()` and `_force_creation_active_if_reconcile_needed()` directly.
- T-017b: assert step not forced to NAME after reconcile from disk `SETUP` + saved `CHARACTER_CREATION`.
- T-017f: live `ROSTER_SETUP` + orphan `characters` → force helper no-op.
