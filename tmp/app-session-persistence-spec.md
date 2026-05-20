# Spec — App Session Persistence

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/session_state.json`, autosave in `main.py` / `ui/app.py`, resume flow in orchestrator

---

## Spec

- Persist: narration lines, input history, orchestrator LLM history (trimmed), visited cells, current AV-GRID address, `creation_state`, `combat_state`, **`engine_status`** (full engine snapshot on save — APP-016).
- Autosave every 60s and on quit (Escape).
- On launch: show startup prompt based on **engine resumability** (`bridge.has_save()` / `has_save_session()`); do **not** treat a mere active session as a save. App-side `session_state.json` is **not** read at boot — only on explicit **load game** after successful engine resume path.
- **`load game`:** orchestrator calls `bridge.session_resume()`; requires `find_save_campaign()` (living slotted character). UI may restore `session_state.json` in parallel when load succeeds.
- **`new game`:** ordered session end → wipe → new campaign → session start via `setup_new_game()` — see § setup_new_game lifecycle (APP-014). **APP-015:** creation block cleared on disk **before** engine wipe — see § New game — creation block clear.
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

Symptom strings below describe player-visible failures; exact substrings may not appear in current engine code. Fixes are lifecycle ordering and reconciliation (APP-014–APP-020), not log-text matching.

- `setup_new_game` → `active session already exists` — **APP-014:** end session before wipe
- `campaign already has an open session` — **APP-014:** same lifecycle ordering
- `session_resume` → `no save session found` — **APP-071** (closed)
- Mid-creation app save but empty engine roster (Dumpy session) — **APP-064** boot path + **APP-014/015** on **`new game`**

---

## Task checklist

- [x] `session_state.json` schema with narration + creation_state
- [x] Autosave interval

**Open work:** [APP-014](backlog/app-014-setupnewgame-session-lifecycle.md)–[APP-020](backlog/app-020-document-stuck-creation-recovery.md) in [`tmp/backlog/README.md`](backlog/README.md). _(APP-064, APP-071 closed 2026-05-20.)_

- [ ] **APP-014:** `setup_new_game` ends prior session before wipe. See § setup_new_game lifecycle (APP-014).
- [x] **APP-015:** Explicit creation-block clear on **`new game`** (incl. failure autosave). See § New game — creation block clear (APP-015).
- [x] **APP-016:** Snapshot engine `status()` on app save. See § Engine status snapshot (APP-016).
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

## setup_new_game lifecycle (APP-014)

**Owner:** `app/gm/orchestrator.py` `setup_new_game`. **Bridge:** `end_session`, `force_close_all_sessions`, `wipe_all_data`, `campaign_new`, `session_start`. **Entry:** player command **`new game`** / **`start`** / **`new`**; also death restart and resume **`run_ended`** recovery.

### Required order (L1–L7)

On every `setup_new_game(campaign_slug)` call:

| Step | Action | Notes |
|------|--------|-------|
| **L1** | `bridge.end_session()` | Graceful close when `active.json` + open session exist |
| **L1b** | If L1 returns `not ok`: `bridge.force_close_all_sessions()` | Closes `ended_at IS NULL` rows and removes `active.json` without valid pointer |
| **L2** | `bridge.wipe_all_data()` | DELETE session/campaign tables; unlink `active.json`; **does not** delete `world_corpses` |
| **L3** | `bridge.init()` | Migrations only |
| **L4** | `bridge.campaign_new(campaign_slug, …)` | On `not ok` except defensive `"already exists"` swallow → **return error** (no session start) |
| **L5** | `bridge.session_start(campaign_slug)` | New `current` session + `party_state`; `_clear_save_slot` + `write_active` |
| **L6** | Orchestrator reset | `history.clear()`; `CreationState(active=True, step="NAME")` |
| **L7** | `_delete_save_file()` | Remove app `session_state.json` on **success only** |

**Ticket AC mapping:** session end (L1/L1b) → wipe (L2) → campaign new (L4) → session start (L5).

### Callers (L6)

All MUST use the same `setup_new_game` implementation — no duplicate lifecycle:

- `process_turn` — **`new game`** / **`start`** / **`new`**
- `_handle_player_death` — after `process_delver_death`
- `process_turn` — `session_resume` when `run_ended`

Callers SHOULD check `result.get("ok")` before narrating success; error surfacing in UI is **APP-019** scope.

### Success path

- Return value MUST include `ok: true` (session start dict).
- `bridge.status()` MUST show an active session with creation awaiting / empty roster as today.
- `creation.step` MUST be **`NAME`**.
- UI `_process_turn` queues `clear_narration` before orchestrator; `finally` `_save_session()` writes fresh creation block — compatible with **APP-016** `engine_status` snapshot (no change required in APP-014).

### Failure path

- If L4 fails (non-swallowed error) or L5 fails: **return** error dict; do **not** run L6–L7.
- `process_turn` surfaces `Could not start game: {error}` + JSONL `error` (`setup_new_game`).
- Prior `creation` / `session_state.json` may remain until retry — explicit failure-path clear is **APP-015**, not APP-014.

### Invariants

- **`world_corpses`** MUST persist across `setup_new_game` (death restart, **`new game`** after partial creation).
- Wipe MUST NOT leave duplicate open session rows that block L5 after L1–L2.
- Historical errors **`active session already exists`** / **`campaign already has an open session`** are resolved by L1–L2 ordering; QA validates behavior (clean NAME, no setup error), not log substring match.

### Batch — APP-014 / APP-015 / APP-016

| Ticket | Owns | APP-014 boundary |
|--------|------|------------------|
| **APP-014** | L1–L5 engine lifecycle ordering in `setup_new_game` | Does not own failure-path app save guard |
| **APP-015** | Explicit `creation_state` clear **before** L1; all exit paths (C1–C3) | Prepends C1–C2; L7 may remain on success — see § New game — creation block clear (APP-015) |
| **APP-016** | `engine_status` on `_save_session` (write); stale clear on new game via **APP-015** C2 — see § Engine status snapshot on save (APP-016) |

Parallel batch impl: APP-014 edits prepend L1/L1b in `orchestrator.py`; APP-015 may edit save helpers or UI save guard — merge carefully.

### Non-regression

- Isolated-workspace **`new game`** from cold start still reaches NAME step.
- Post-finalize / in-delve saves and **load game** unchanged.
- APP-064 startup branches unchanged.

---

## New game — creation block clear (APP-015)

**Owner:** `app/gm/orchestrator.py` — `setup_new_game`, disk helper (e.g. `_clear_creation_block_on_disk`). **Consumers:** all `setup_new_game` callers; UI `_save_session()` in `finally` must not undo an upfront clear.

### Problem

Creation block reset and `_delete_save_file()` run only **after** engine steps succeed (APP-014 L6–L7). Early return on `campaign_new` failure leaves prior `creation_state` on disk; autosave during slow setup can persist a stale block. `_is_mid_creation_resume_failure()` reads that block for variant B recovery (APP-071).

### Requirements

#### C1 — Clear before engine wipe

On **every** `setup_new_game()` entry:

1. Set in-memory `self.creation` to `CreationState(active=True, step="NAME")` with **no** carry-over (`name`, `race`, `roll_result`, table flags, etc. empty).
2. **Persist** the creation block to `app/session_state.json` **before** APP-014 L2 (`wipe_all_data`).

Order: **memory reset → disk creation block → L1–L7 engine lifecycle**.

#### C2 — Explicit disk mutation

| Approach | Rule |
|----------|------|
| **Preferred** | If `session_state.json` exists: read JSON, set `creation_state` to `export_creation_state()` from the fresh NAME state (C1), **remove** `engine_status` (or set to `null` — treat both as no snapshot on load), write back. Other keys (`narration`, `input_history`, etc.) **unchanged** unless Dev documents otherwise. |
| **Also allowed** | `unlink` entire file at **start** plus C2; L7 `_delete_save_file()` on success may remain. |
| **Forbidden** | Relying solely on L7 with no upfront `creation_state` write on failed paths. |

Do not leave `step` past `NAME` or populated `name` / `roll_result` on disk after **`new game`** is attempted.

#### C3 — All exit paths

If `setup_new_game()` returns before L5 (session start), **C1–C2 must already have run** so `_save_session()` and `_is_mid_creation_resume_failure()` never see pre-wipe creation.

#### C4 — Batch coordination

| Ticket | Relationship |
|--------|----------------|
| **APP-014** | L1–L5 engine ordering; L6–L7 orchestrator reset after success. **APP-015** prepends C1–C2 **before** L1; does not remove L7. |
| **APP-016** | `engine_status` written on `_save_session` (APP-016). **APP-015** clears stale `engine_status` on every `setup_new_game` entry (C2); fresh snapshot is recreated on next save after engine session exists. |
| **APP-018** | Load/continue restore — out of scope. |

### Acceptance criteria (ticket)

- [x] On **new game**, explicitly clear `session_state.json` **creation block** (C1–C3).

### Non-regression

- Successful **`new game`** still reaches NAME desk when setup completes.
- APP-071 variant B at NAME with `active: true` remains valid; must **not** cite a **prior** step or name from disk after **`new game`** was attempted.

---

## Engine status snapshot on save (APP-016)

**Owner:** `app/ui/app.py` `_save_session()`. **Source:** `Orchestrator.get_status()` → `GameBridge.status()` → `handle_status` (same payload as APP-005 `creation_finalize` JSONL `engine_status`). **Read path:** none in this ticket — **APP-017** / **APP-018** consume on load.

### Problem

`session_state.json` stores rich `creation_state` but only partial engine truth (`session_id`, `campaign_slug` from `active`). Mid-creation saves can show `creation_state.step` advanced while the engine has `awaiting: CHARACTER_CREATION` and an empty `roster`. Reconcile tickets need a **save-time** engine snapshot; without it, load paths rely on live DB state that may be stale or empty after partial wipes.

### Field and payload (S1)

| Key | Value |
|-----|--------|
| **`engine_status`** | Full dict returned by `get_status()` on successful read |

Reconcile-relevant keys MUST be present when a session exists: at minimum `awaiting`, `roster`, `party`, `combat`, `active`, plus any other keys `handle_status` returns today.

### Write rules (S5)

| Rule | Behavior |
|------|----------|
| **S5a — Triggers** | Every `_save_session()` write: 60s autosave, Escape quit, post-turn `finally` in `_process_turn`. **No new triggers.** |
| **S5b — Success** | When `get_status()` succeeds, persist the **full** status dict under `engine_status`. |
| **S5c — Single call** | Implementer MAY use one `get_status()` per save for both `active` session fields and `engine_status` (today `_save_session` already calls `get_status()` for `session_id` / `campaign_slug`). |
| **S5d — Failure** | On `get_status()` exception or error-shaped payload: save **proceeds**; **`engine_status` key omitted** (preferred). Do not write `engine_status: null` on failure unless Dev documents one shape — load/reconcile MUST treat **absent key** and **`null`** as “no snapshot”. |
| **S5e — Legacy** | Saves without `engine_status` load without error; `_load_session` unchanged in APP-016. |

### New game — stale snapshot (batch)

| Ticket | Owns |
|--------|------|
| **APP-014** | L7 `_delete_save_file()` on **success** removes entire `session_state.json` — no stale `engine_status`. |
| **APP-015** | On **every** `setup_new_game()` entry, C2 surgical disk write **removes** `engine_status` (see § New game — creation block clear). Prevents post-wipe disk with fresh `creation_state` (NAME) and pre-wipe `engine_status.awaiting` / `roster`. |
| **APP-016** | Write-only snapshot on `_save_session`; does **not** implement new-game clear. |

After successful **`new game`**, UI `finally` `_save_session()` writes a fresh `engine_status` matching the new empty-roster session.

### Consumers (read path — out of scope)

| Ticket | Role |
|--------|------|
| **APP-017** | Reconcile empty roster on load — reads saved `engine_status` (when present) vs live engine |
| **APP-018** | Continue / restore creation when `awaiting == CHARACTER_CREATION` — uses snapshot + `creation_state` |

APP-016 MUST NOT add `_load_session` or orchestrator resume logic for `engine_status`.

### Non-goals

- Trimming `engine_status` payload size.
- Changing startup `has_save()` / boot behavior (APP-064).
- Centralizing save logic outside `app/ui/app.py` unless a minimal refactor stays within ticket Expected files.

### Acceptance criteria (ticket)

- [x] On save, snapshot engine `status()` alongside app state (`engine_status` per S5).

---

## Tests

- Save mid-creation → relaunch → same `creation.step`.
- Save after finalize → relaunch → roster populated, not creation UI.
- `new game` from stuck partial creation → clean NAME step.

### Tests APP-014 — setup_new_game lifecycle

| ID | Case | Expected |
|----|------|----------|
| **T-014a** | Isolated workspace: `session_start` → mid-creation orchestrator state → `setup_new_game()` | `ok: true`; active session; `creation.step == NAME`; no duplicate open sessions |
| **T-014b** | Open session row + `active.json` present → `setup_new_game()` | Prior session ended or wiped; new session `current`; clean NAME |
| **T-014c** | After delver death fixture → `setup_new_game()` | `world_corpses` row retained; new session started |

```bash
python -m pytest app/tests -q -k "setup_new_game or session_lifecycle or creation_flow"
python -m pytest play/tomb_gm/tests -q -k session
```

Manual: partial creation (APP-064 boot) → **`new game`** → NAME step, no **Could not start game** (run spec human hints).

### Tests APP-015 — creation block on new game

| ID | Case | Expected |
|----|------|----------|
| **T-015a** | Temp/isolated `session_state.json` with `creation_state.step` = `SKILLS`, populated `name` / `roll_result`; `setup_new_game()` with mocked bridge (`campaign_new` succeeds) | On disk: `creation_state.step` is `NAME`, prior name/roll absent; in-memory `creation.step` == `NAME` |
| **T-015b** | Same stale file; mock `campaign_new` → `ok: false` (not `"already exists"`); early return | Disk still NAME-fresh (C3); not prior step |
| **T-015c** | After T-015a or manual mid-creation, `process_turn("load game")` with no engine save | Variant B references current memory step, not stale pre–`new game` disk step |
| **T-015d** | Stale file with `engine_status` (e.g. `awaiting` not `CHARACTER_CREATION` or non-empty `roster`); `setup_new_game()` entry (success or early return after C1–C2) | `engine_status` key **absent** or **`null`** until next `_save_session()` |

```bash
python -m pytest app/tests -q -k "creation_block or new_game_creation"
```

**Test hygiene:** Do not pollute dev `app/session_state.json`; use tmp path monkeypatch or teardown.

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

### Tests APP-016 — engine status snapshot

| ID | Case | Expected |
|----|------|----------|
| **T4a** | Mid-creation save (`CHARACTER_CREATION`, empty roster) | `engine_status.awaiting == "CHARACTER_CREATION"`, `engine_status.roster == []` |
| **T4b** | Post-finalize or in-delve save | `engine_status.roster` non-empty |
| **T4c** | `_load_session` with legacy JSON (no `engine_status`) | No error; behavior unchanged vs pre-016 |
| **T4d** | Mock `get_status()` failure during save | File written; `engine_status` absent/null |

```bash
cd app && python -m pytest app/tests -q -k "engine_status or save_session"
```

Manual: mid-creation → autosave or Escape → inspect `app/session_state.json` for `engine_status`.

---

## File map

| File | Role |
|------|------|
| `session_state.json` | App-side save; includes `engine_status` after APP-016 |
| `gm/orchestrator.py` | `setup_new_game`, `_clear_creation_block_on_disk` (APP-015), `export_creation_state`, `import_creation_state`, resume |
| `gm/bridge.py` | `end_session`, `force_close_all_sessions`, `wipe_all_data`, `session_start`, `session_resume`, `has_save` |
| `ui/app.py` | `_save_session` / `_load_session`; autosave; startup save prompt (`_init_orchestrator`) |

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
| 2026-05-20 | APP-015 PM draft: § New game — creation block clear (C1–C4); tests T-015a–c; batch notes vs APP-014/016 |
| 2026-05-20 | APP-014 PM draft: § setup_new_game lifecycle (L1–L7), batch boundaries APP-015/016, tests T-014a–c |
| 2026-05-20 | APP-016 PM draft: § Engine status snapshot on save — `engine_status` field, S5 write rules, tests T4, batch notes (APP-014/015/017/018) |
| 2026-05-20 | APP-016 PM r2 (QA round 1): added § Engine status snapshot on save (APP-016); resolved APP-015/016 ownership — APP-015 C2 removes `engine_status` on new game; Consumers APP-017/018; T-015d; persist bullet; canonical omit on save failure (S5d) |
| 2026-05-20 | APP-016 done: `_save_session()` writes full `get_status()` under `engine_status` (S5b–c); omit on failure (S5d); `test_engine_status_on_save.py` T4a–d |
