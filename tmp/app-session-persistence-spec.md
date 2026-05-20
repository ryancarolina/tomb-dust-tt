# Spec — App Session Persistence

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/session_state.json`, autosave in `main.py` / `ui/app.py`, resume flow in orchestrator

---

## Spec

- Persist: narration lines, input history, orchestrator LLM history (trimmed), visited cells, current AV-GRID address, `creation_state`, `combat_state`.
- Autosave every 60s and on quit (Escape).
- On launch: restore UI from save if present; orchestrator calls `session_resume` when workspace has active session.
- **`new game`:** wipe app save + engine workspace via `setup_new_game()`.
- App save and engine SQLite must **reconcile** — no PRE_DELVE in UI while engine `awaiting: CHARACTER_CREATION`.

---

## Problem (from logs)

- `setup_new_game` → `active session already exists`
- `campaign already has an open session`
- `session_resume` → `no save session found`
- Mid-creation app save but empty engine roster (Dumpy session)

---

## Task checklist

- [x] `session_state.json` schema with narration + creation_state
- [x] Autosave interval
- [ ] `setup_new_game()` ends open session before wipe: `session end` → `wipe_all_data` → `campaign new` → `session start`
- [ ] On `new game`, clear `session_state.json` creation block explicitly
- [ ] On save: snapshot engine `status()` alongside app state
- [ ] On load: if engine roster empty but creation inactive → force creation mode
- [ ] `continue` when `awaiting == CHARACTER_CREATION`: restore `creation` from save
- [ ] Surface clear error when `new game` fails (cause + retry hint)
- [ ] Document recovery in `app/README.md` — stuck creation → type **`new game`**

---

## Tests

- Save mid-creation → relaunch → same `creation.step`.
- Save after finalize → relaunch → roster populated, not creation UI.
- `new game` from stuck partial creation → clean NAME step.

---

## File map

| File | Role |
|------|------|
| `session_state.json` | App-side save |
| `gm/orchestrator.py` | `setup_new_game`, `export_creation_state`, `import_creation_state`, resume |
| `gm/bridge.py` | `wipe_all_data`, `session_start`, `force_close_all_sessions` |
| `ui/app.py` | Autosave trigger |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged session-new-game-lifecycle content |
