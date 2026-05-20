# Spec — App Session Persistence

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/session_state.json`, autosave in `main.py` / `ui/app.py`, resume flow in orchestrator

---

## Spec

- Persist: narration lines, input history, orchestrator LLM history (trimmed), visited cells, current AV-GRID address, `creation_state`, `combat_state`.
- Autosave every 60s and on quit (Escape).
- On launch: show startup prompt based on **engine resumability** (`bridge.has_save()` / `has_save_session()`); do **not** treat a mere active session as a save. App-side `session_state.json` is **not** read at boot — only on explicit **load game** after successful engine resume path.
- **`load game`:** orchestrator calls `bridge.session_resume()`; requires `find_save_campaign()` (living slotted character). UI may restore `session_state.json` in parallel when load succeeds.
- **`new game`:** wipe app save + engine workspace via `setup_new_game()`.
- App save and engine SQLite must **reconcile** — no PRE_DELVE in UI while engine `awaiting: CHARACTER_CREATION`.

### Resume failure — `load game` with no engine save (APP-071)

Commands: `load game`, `load`, `continue`, `resume` → `Orchestrator.process_turn` → `bridge.session_resume()`.

**Variant selection (ordered):** evaluate **mid-creation signals first**; if any match, use variant B; else variant A. Mid-creation signals: `creation.active`; in-progress `creation.step` / app save; engine `awaiting == CHARACTER_CREATION` with empty `roster`.

| Condition | Player narration | Footer / chips | JSONL |
|-----------|------------------|----------------|-------|
| Resume fails, **variant A** (cold — no mid-creation signals) | No saved game found; suggest **`new game`**. | `[Awaiting: new game]` allowed (`_creation_drift_scope()` false) | `error` (`session_resume`) **and** `gm_narration` via **`_emit_recovery_narration`** (not `_emit_narration`) |
| Resume fails, **variant B** (mid-creation) | No **finished** save; name current creation step; continue desk or **`new game`** in prose (warn wipe). Distinct copy from variant A. | `[{format_creation_status(creation)}]` only — e.g. `[Awaiting: RACE_INPUT]`. **No** human phrases (`new game`, `continue creation`) in bracket `Awaiting:` | Same dual logging via `_emit_recovery_narration`; **no** `creation_drift` / `awaiting_mismatch` from recovery footer alone |
| Resume succeeds | Existing recap / creation resume paths unchanged | Desk FSM footers as today | `gm_narration` on narrated paths; `_emit_narration` + drift check as today |

Engine error `no save session found` is **not** shown verbatim to the player. UI `_load_session()` may still run on load commands; app save does not imply an engine roster save.

**Drift / logging:** Recovery failure copy is outside desk FSM narration — use `_emit_recovery_narration` (`log_gm_narration` only, skips `_check_creation_drift`). See [`app-logging-qa-spec.md`](app-logging-qa-spec.md) § `creation_drift` healthy path.

**Related (not APP-071):** APP-064 startup prompt. **APP-019:** toast / UI error channel for **`new game`** failures — APP-071 delivers narration + JSONL for **`load game`** resume failure only; APP-019 remains open.

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

**Open work:** [APP-014](backlog/app-014-setupnewgame-session-lifecycle.md)–[APP-020](backlog/app-020-document-stuck-creation-recovery.md) in [`tmp/backlog/README.md`](backlog/README.md). _(APP-064, APP-071 closed 2026-05-20.)_

- [x] **APP-064:** Startup "saved game" prompt only when `has_save_session()` is true (not merely active session + empty roster). See § Startup save-detection (APP-064).
- [x] **APP-071:** Friendly `load game` failure narration + `gm_narration` when no resumable save. See § Resume failure.

---

## Startup save-detection (APP-064)

**Owner:** `app/ui/app.py` `_init_orchestrator` (startup branch). **Eligibility source:** engine `has_save_session()` via `GameBridge.has_save()`.

### Detection rule (S1)

- Startup **`has_save`** MUST equal **`bridge.has_save()`** only.
- MUST **NOT** widen with `has_active and awaiting not in ("SETUP", "SESSION_ENDED")` or any equivalent "active session counts as save" override.
- Engine truth: `has_save_session(conn)` ≡ `find_save_campaign(conn) is not None` — requires at least one **living character with a roster slot** on the save campaign (`play/tomb_gm/domain/session.py`).

### UI branches (S2–S3)

| `bridge.has_save()` | Narration | Suggestion chips |
|---------------------|-----------|------------------|
| **true** | Include "You have a saved game." after title block | `["load game", "new game"]` |
| **false** | "Type 'new game' to create a character and enter the world." | `["new game"]` only |

**false** includes: no workspace session; active session in `CHARACTER_CREATION` with **empty roster**; active session in `ROSTER_SETUP` with no resumable campaign per engine.

### Engine vs app save (S4)

- Presence of `session_state.json` alone does **not** set startup `has_save`.
- Boot does **not** auto-restore app save; `_load_session()` runs only when the player chooses **load game** (and engine resume succeeds or is attempted per orchestrator flow).
- After APP-064 fix, partial creation with only app save + empty engine roster shows the **new-game** path at boot — player must type **new game** to proceed (mid-creation continue without engine save: APP-018 / APP-071 scope).

### Non-regression

- Post-finalize or in-delve saves with slotted living character continue to pass `has_save()` → saved-game prompt unchanged.
- Do not change `session_resume`, `find_save_campaign`, or bridge wrappers in APP-064 unless a separate ticket requires it.

---

## Tests

- Save mid-creation → relaunch → same `creation.step`.
- Save after finalize → relaunch → roster populated, not creation UI.
- `new game` from stuck partial creation → clean NAME step.

### Tests APP-064

| ID | Case | Expected |
|----|------|----------|
| **T1a** | Active session, `awaiting: CHARACTER_CREATION`, empty roster → relaunch | No "You have a saved game"; suggestions `["new game"]` only |
| **T1b** | Post-finalize or in-delve: living slotted character → quit → relaunch | "You have a saved game" + `["load game", "new game"]`; load succeeds |
| **T1c** | No active session, no engine save | New-game path only |
| **T2** | _(optional)_ Headless test: mock `Orchestrator` + `bridge.has_save()` / `get_status()` in `_init_orchestrator` | Assert suggestion queue matches S2/S3 table without PyGame display |

```bash
python -m pytest play/tomb_gm/tests -q -k session
python -m pytest app/tests -q   # optional after T2 added
```

### Tests APP-071 — resume failure

| ID | Case | Expected |
|----|------|----------|
| **T3a** | Isolated workspace, no engine save; `process_turn("load game")` | Variant A copy + `new game` hint; JSONL `error` + `gm_narration`; no spurious `creation_drift` |
| **T3b** | Mid-creation (`new game` → name or later); `load game` | Variant B copy; differs from T3a; footer matches `format_creation_status`; **no** `creation_drift` with `awaiting_mismatch` from recovery line |
| **T3c** | Living slotted save present | Resume success unchanged (regression) |

```bash
python -m pytest app/tests -q -k "session_resume or load_game"
```

Manual: `cd app && python main.py` — fresh `load game`; mid-creation `load game` (run spec TC-A/B).

---

## File map

| File | Role |
|------|------|
| `session_state.json` | App-side save |
| `gm/orchestrator.py` | `setup_new_game`, `export_creation_state`, `import_creation_state`, resume |
| `gm/bridge.py` | `wipe_all_data`, `session_start`, `force_close_all_sessions` |
| `ui/app.py` | Autosave trigger; startup save prompt (`_init_orchestrator`) |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged session-new-game-lifecycle content |
| 2026-05-20 | APP-071: § Resume failure behavior + tests (friendly `load game` when no engine save) |
| 2026-05-20 | APP-071 PM r2: ordered variant selection; `_emit_recovery_narration`; mid-creation `format_creation_status` footer; APP-019 scope split |
| 2026-05-20 | APP-064 PM draft: § Startup save-detection — engine-only `has_save()` at boot; tests T1–T2 |
| 2026-05-20 | APP-064 done: removed `_init_orchestrator` active-session `has_save` override; startup uses `bridge.has_save()` only |
| 2026-05-20 | APP-071 done: `_emit_recovery_narration`, variant A/B resume failure copy, `test_session_resume_failure.py` T1–T3 |
