# Spec — App Session Persistence

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/session_state.json`, autosave in `main.py` / `ui/app.py`, resume flow in orchestrator

---

## Spec

- Persist: narration lines, input history, orchestrator LLM history (trimmed), visited cells, current AV-GRID address, `creation_state`, `combat_state`, **`engine_status`** (full engine snapshot on save — APP-016).
- Autosave every 60s and on quit (Escape).
- On launch: show startup prompt based on **engine resumability** (`bridge.has_save()` / `has_save_session()`); do **not** treat a mere active session as a save. App-side `session_state.json` is **not** read at boot (APP-064). **APP-018:** orchestrator restores `creation_state` from disk on **first `process_turn`** (non–`new game`) and on **`load` / `load game` / `continue` / `resume`** — see § Creation restore on continue / relaunch (APP-018).
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

**Related (not APP-071):** APP-064 startup prompt. **APP-019:** friendly **`new game`** setup failure copy — see § New game failure (APP-019).

---

## New game failure — setup_new_game errors (APP-019)

**Owner:** `app/gm/orchestrator.py` — `setup_new_game` callers; helper `_setup_new_game_failure_message` (name may vary) + existing `_emit_recovery_narration`. **Optional UI:** `app/ui/app.py` status text only (R6).

**Commands / triggers:** explicit **`new game`** / **`start`** / **`new`**; implicit restart after PC death (`_handle_player_death`); implicit restart after **`load game`** when `session_resume` returns `run_ended`.

### Failure contexts

| Context | Trigger | Must not emit on failure |
|---------|---------|---------------------------|
| **A — command** | Player **`new game`** | `_creation_turn` / NAME desk |
| **B — death** | Combat PC death → `setup_new_game` | “new game has started”, NAME prompt |
| **C — run_ended** | Resume + `run_ended` → `setup_new_game` | Success run_ended death_msg + NAME desk |

All contexts: if `setup_new_game()` returns `not ok`, callers MUST emit recovery copy and MUST NOT narrate success.

### Emit ownership (R1 — drift-safe JSONL)

**All failure paths:** `log_error("setup_new_game", …)` → build context copy → **`_emit_recovery_narration` exactly once** → return message. Never `_emit_narration` on setup failure.

| Context | Emit owner | Notes |
|---------|------------|-------|
| **A — command** | `process_turn` inline | Same function calls `setup_new_game`; no secondary caller |
| **B — death** | `_handle_player_death` on failure; combat callers on success | `_handle_player_death` returns `(message, already_emitted)` (or equivalent). On failure: recovery emit **inside** handler; both combat call sites (~1586, ~1680) **MUST NOT** `_emit_narration` when `already_emitted`. On success: caller `_emit_narration` unchanged. **Forbidden:** recovery emit in handler + caller `_emit_narration` on same failure (double JSONL) |
| **C — run_ended** | `process_turn` resume branch inline | Same as A — check `ok` before success `_emit_narration(death_msg)` |

Run spec detail: [`spec.md` R1a/R1b](backlog/runs/app-019-surface-new-game-errors/spec.md).

### Player copy (minimum)

**Context A (command):**

- Lead: could not start a fresh session.
- Mapped `{cause_line}` from engine error (see table below) — **not** verbatim `Could not start game: …`.
- Retry: type **`new game`** to try again; relaunch hint if persistent.
- Footer: `[Awaiting: new game]`.

**Context B (death):** preserve corpse line (`**{name}** is dead… **{where}**`); add run-over + could not open fresh desk + `{cause_line}` + retry; footer `[Awaiting: new game]`. **Forbidden:** success restart copy.

**Context C (run_ended):** preserve prior-delver death line + `{where}`; same failure tail as B; footer `[Awaiting: new game]`.

### Engine error → cause line

| Engine error (substring) | Player `{cause_line}` |
|--------------------------|-------------------------|
| `campaign not found` | The save campaign could not be found in the workspace database. |
| `slug must be` | The campaign name failed validation — this is an internal setup error. |
| `campaign already exists` | A leftover campaign record blocked startup (unexpected after wipe). |
| `active session already exists` / `campaign already has an open session` | A stale open session blocked startup (regression — report if seen after APP-014). |
| `permission denied`, `database is locked`, `disk I/O` | The workspace database could not be written (permissions or file lock). |
| default | Something went wrong while resetting the workspace for a new run. |

### JSONL

| Event | When |
|-------|------|
| `error` | `log_error("setup_new_game", <verbatim engine error>)` — retain context string |
| `gm_narration` | Same panel text via **`_emit_recovery_narration`** (no `_check_creation_drift`) |

Dual logging mirrors APP-071 resume failure. Do **not** use `_emit_narration` on setup-failure paths.

### UI

- Primary channel: narration panel return string + `[Awaiting: new game]` chips (orchestrator-only closes ticket).
- Optional: `_set_turn_idle("Error — try again")` on command failure only — do **not** duplicate full copy into UI `error` queue (`[Error: …]`).

### Tests APP-019

| ID | Case | Expected |
|----|------|----------|
| **T-019a** | Mock L4 failure; `process_turn("new game")` | Context A copy + dual JSONL; **one** `gm_narration` |
| **T-019b** | Mock L5 generic failure; command path | Mapped default cause |
| **T-019c** | Direct `_handle_player_death` + setup failure (no full combat integration) | Context B; no success NAME prompt; **one** `gm_narration`; caller skips `_emit_narration` when `already_emitted` |
| **T-019d** | `run_ended` + setup failure | Context C; no success NAME prompt; dual JSONL |
| **T-019e** | T-019a **and** T-019c | No spurious `creation_drift` / `awaiting_mismatch` |
| **T-019f** | Happy **`new game`** | NAME desk regression (T-014a) |

```bash
python -m pytest app/tests -q -k "setup_new_game_failure or setup_new_game"
```

Run spec: [`tmp/backlog/runs/app-019-surface-new-game-errors/spec.md`](backlog/runs/app-019-surface-new-game-errors/spec.md).

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
- [x] **APP-017:** Reconcile empty roster on load — force `creation.active`. See § Reconcile empty roster on load (APP-017).
- [x] **APP-018:** Continue restores creation FSM when `awaiting == CHARACTER_CREATION`. See § Creation restore on continue / relaunch (APP-018).
- [x] **APP-064:** Startup "saved game" prompt only when `has_save_session()` is true (not merely active session + empty roster). See § Startup save-detection (APP-064).
- [x] **APP-071:** Friendly `load game` failure narration + `gm_narration` when no resumable save. See § Resume failure.
- [x] **APP-019:** Friendly `setup_new_game` failure copy + dual JSONL; death / `run_ended` callers check `ok`. See § New game failure (APP-019).

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
- Callers surface friendly recovery copy + JSONL `error` + `gm_narration` via **`_emit_recovery_narration`** — see § New game failure (APP-019). Legacy one-liner `Could not start game: {error}` is **replaced** by APP-019.
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
| **APP-018** | Load/continue restore — see § Creation restore on continue / relaunch (APP-018). |

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

### Consumers (read path)

| Ticket | Role |
|--------|------|
| **APP-017** | Reconcile empty roster on load — reads saved `engine_status`; forces **`creation.active`** when still inactive **after** APP-018 — see § Reconcile empty roster on load (APP-017) |
| **APP-018** | Restore creation **step and fields** when `awaiting == CHARACTER_CREATION` — see § Creation restore on continue / relaunch (APP-018) |

APP-016 write-only; read logic in APP-017 / APP-018 (`orchestrator.py`).

### Non-goals

- Trimming `engine_status` payload size.
- Changing startup `has_save()` / boot behavior (APP-064).
- Centralizing save logic outside `app/ui/app.py` unless a minimal refactor stays within ticket Expected files.

### Acceptance criteria (ticket)

- [x] On save, snapshot engine `status()` alongside app state (`engine_status` per S5).

---

## Reconcile empty roster on load (APP-017)

**Owner:** `app/gm/orchestrator.py` — `_sync_creation_from_status()` and/or dedicated reconcile helper invoked from `_load_session` and post-resume sync paths. **Read source:** saved **`engine_status`** in `session_state.json` (APP-016) when live `bridge.status()` is missing or `awaiting: SETUP`. **Write source:** unchanged (APP-016).

### Problem

`engine_status` is written on save but was not read on load. `_load_session()` imports `creation_state` and syncs against **live** engine only. When `creation_state` is absent or `active: false` but the snapshot shows **empty `roster`** and **`awaiting: CHARACTER_CREATION`**, creation stays inactive — suggestion chips empty and the player may leave the desk FSM.

### Requirements

#### R1 — Force creation active

On load reconcile (UI `_load_session` and orchestrator post-resume hooks):

| Condition | Action |
|-----------|--------|
| `creation.active == false` **and** empty **`roster`** **and** mid-creation (`awaiting == CHARACTER_CREATION` live or saved) | Set **`creation.active = true`** |
| Non-empty live **`roster`** | **`creation.active = false`** (unchanged post-finalize behavior) |
| Legacy save: no **`engine_status`**, live only | Reconcile from live engine; no new errors (S5d / T-017d) |

Reconcile MUST NOT require successful `session_resume()`.

Do **not** force creation when live or saved **`awaiting`** is not **`CHARACTER_CREATION`** (e.g. **`SETUP`**, **`ROSTER_SETUP`**) even if **`roster`** is empty.

#### R1b — Empty roster uses `roster`, not `characters`

| Field | Meaning |
|-------|---------|
| **`roster`** | Slotted living characters — **sole** empty check for force-active (ticket AC “empty roster”) |
| **`characters`** | All campaign rows (incl. unslotted) — **do not** use for APP-017 force-active gate |

| Condition | Action |
|-----------|--------|
| `awaiting == ROSTER_SETUP` (`roster` empty, `characters` non-empty) | **No-op** — do not force **`creation.active`**; out of ticket AC |
| `_sync_creation_from_status` today uses `not characters` | Dev MUST switch to **`roster`** empty + **`CHARACTER_CREATION`** (R1 row 1) |

#### R2 — Live vs saved precedence

1. **Live** `bridge.status()` when session active — live **`roster`** wins over stale saved snapshot.
2. **Saved** **`engine_status`** when live absent or `awaiting: SETUP` and creation inactive — use **`roster`** / **`awaiting`** from disk.
3. **Absent/null `engine_status`:** fall back to live only; load proceeds without error.

#### R3 — Batch boundary (APP-017 vs APP-018)

| Ticket | Owns | Does not own |
|--------|------|--------------|
| **APP-017** | Flip **`creation.active`** to **`true`** under R1; read **`engine_status`** for empty-roster mid-creation detection | Restore **`step`**, **`name`**, **`race`**, **`roll_result`**, table flags |
| **APP-018** | Restore full creation FSM from **`creation_state`** + snapshot when `awaiting == CHARACTER_CREATION` | Boot startup prompt; forcing active when 017 already did |

**Merge order (canonical — APP-018 PM):** **APP-018** field restore (`import_creation_state` when gate passes) runs **first**; **APP-017** force-active runs only if roster empty and **`creation.active`** still false. APP-017 MUST NOT reset an in-progress saved step to **`NAME`** when **`creation_state`** carries a later step. Minimal exception: if **`step == WORLD_INTRO`** (invalid for active desk), reconcile MAY set **`step = "NAME"`** after APP-018 import.

| Ticket | Relationship |
|--------|--------------|
| **APP-016** | Provides **`engine_status`** snapshot on save |
| **APP-015** | Clears stale snapshot on **`new game`** — not load path |
| **APP-064** | Boot does not auto-reconcile; player types load/new |
| **APP-071** | Resume failure variant B uses mid-creation signals; 017 prevents inactive+empty-roster desync after `_load_session` |

### Acceptance criteria (ticket)

- [x] If engine roster empty and creation inactive → force creation mode (`creation.active == true` per R1).

**Spec AC mapping**

| Ticket AC | Domain rule |
|-----------|-------------|
| Empty roster + inactive creation + mid-creation → force creation | R1 table row 1 + R1b |
| Post-finalize non-empty roster unchanged | R1 table row 2 |
| Legacy / missing snapshot | R2 step 3, T-017d |
| Orphan unslotted rows (`ROSTER_SETUP`) | R1b no-op, T-017f |

### Non-regression

- Post-finalize / in-delve load with slotted character unchanged.
- APP-071 variant A/B resume failure copy unchanged.
- APP-064 startup branches unchanged (reconcile on **load**, not boot).

### Tests APP-017

| ID | Case | Expected |
|----|------|----------|
| **T-017a** | Mid-creation save; `creation.active=False` in memory; reconcile with disk `engine_status` | `creation.active is True` |
| **T-017b** | `creation_state: null`, saved empty roster + `CHARACTER_CREATION`; live `SETUP` | Force active; step restore = APP-018 |
| **T-017c** | Live **`roster`** non-empty (post-finalize) | Does not reactivate creation |
| **T-017c2** | Live **`roster`** empty, saved **`engine_status.roster`** non-empty, `CHARACTER_CREATION` | Force active — live empty wins over stale snapshot (R2) |
| **T-017d** | Legacy JSON without `engine_status`, `creation_state.active=true` | Unchanged vs pre-017 (T4c) |
| **T-017e** | After reconcile: `get_player_suggestions` | Non-empty creation chips |
| **T-017f** | Live `ROSTER_SETUP`, empty `roster`, non-empty `characters` | No force-active (R1b no-op) |

```bash
python -m pytest app/tests -q -k "reconcile or empty_roster or engine_status or load_session or app_017"
```

---

## Creation restore on continue / relaunch (APP-018)

**Owner:** `app/gm/orchestrator.py` — shared restore helper (e.g. `_restore_creation_from_session_state()`), `import_creation_state`, `process_turn` gates. **Inputs:** `creation_state`, `engine_status` from `session_state.json` (APP-016). **Does not** change `ui/app.py` or APP-064 boot `_load_session`.

### Problem

Mid-creation saves persist FSM + engine snapshot, but the orchestrator does not hydrate after relaunch or on failed `session_resume`. Successful resume can clobber disk step with `step="NAME"` (~573–576). UI `_load_session` may import in parallel — orchestrator must own FSM truth.

### Gate (G1)

Restore **only when all** hold:

| # | Condition |
|---|-----------|
| G1a | Saved `engine_status.awaiting == "CHARACTER_CREATION"` when snapshot present and non-null; else live `awaiting == "CHARACTER_CREATION"` |
| G1b | `creation_state.active == true` |
| G1c | Empty roster in snapshot when present; else live `roster` empty |
| G1d | Live `roster` empty — if live non-empty, **no restore** |

**No-op:** post-finalize; `awaiting` not `CHARACTER_CREATION`; inactive/missing `creation_state`; after APP-015 **`new game`** NAME-only disk.

### Restore action (G2)

1. Read `_session_state_path()` JSON.
2. When G1 passes: `import_creation_state(creation_state)`; ensure `creation.active` is true.
3. **Forbidden** after successful import: `CreationState(active=True, step="NAME")` unless `step` missing or not in `CREATION_STEPS`.
4. `_sync_creation_from_status()` **after** import; existing `WORLD_INTRO` → `NAME` only.

### Call sites (G3)

| ID | When |
|----|------|
| **G3a** | First `process_turn` after relaunch (input not `new game` / `start` / `new`) **when G1 passes** — same gate as G3b/G3c (saved `engine_status.awaiting` precedence; not live-only; covers live `SETUP` + saved `CHARACTER_CREATION`, APP-017 **T-017b** class) |
| **G3b** | `continue` / `resume` / `load` / `load game`; `session_resume` **failed** — before `_resume_failure_message` |
| **G3c** | Same commands; `session_resume` **succeeded** — before `_sync_creation_from_status` and CHARACTER_CREATION branch; remove NAME clobber |

“Relaunch → same step” = first player turn restores FSM (APP-064 boot unchanged).

### Batch — APP-017

See § Reconcile empty roster on load (APP-017) **Merge order** — APP-018 restore before APP-017 force-active.

### Acceptance criteria (ticket)

- [x] When `awaiting == CHARACTER_CREATION`, restore creation from save (G1–G3).

### Non-regression

- APP-071 variant A; APP-015 post–`new game`**; post-finalize load; APP-064 startup.

### Tests APP-018

| ID | Case | Expected |
|----|------|----------|
| **T-018a** | Disk `CHARACTER_CREATION` + `creation_state.step == RACE`; `process_turn("continue")` fail | `creation.step == RACE`; variant B step phrase matches |
| **T-018b** | Same disk seed; live `awaiting != CHARACTER_CREATION` (e.g. `SETUP`) + saved `CHARACTER_CREATION`; first non–`new-game` `process_turn` | RACE desk / `_creation_turn` path (G1 saved precedence) |
| **T-018c** | Resume success + `CHARACTER_CREATION` | Step not reset to NAME |
| **T-018d** | Legacy JSON without `engine_status`; live `CHARACTER_CREATION` | Restore from `creation_state` |
| **T-018e** | Non-empty roster or awaiting not `CHARACTER_CREATION` | No import |
| **T-018f** | After `setup_new_game` (APP-015) | No restore of pre-wipe SKILLS |

```bash
cd app && python -m pytest app/tests -q -k "creation_restore or continue_creation or app018 or engine_status"
```

Manual: mid-creation RACE/SKILLS → Escape → quit → relaunch → `continue` or desk input → same step; **`new game`** → NAME only.

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
| `gm/orchestrator.py` | `setup_new_game`, `_setup_new_game_failure_message` (APP-019), `_emit_recovery_narration`, `_clear_creation_block_on_disk` (APP-015), `export_creation_state`, `import_creation_state`, `_restore_creation_from_session_state` (APP-018), `_sync_creation_from_status` (APP-017), resume |
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
| 2026-05-20 | APP-019 PM draft: § New game failure — contexts A/B/C, cause mapping, dual JSONL, death/run_ended ok checks; tests T-019a–f; Expected files → orchestrator + tests |
| 2026-05-20 | APP-019 PM r2: § Emit ownership R1a/R1b — context B death caller contract (`already_emitted`); aligned cause lines; T-019c/d/e JSONL asserts |
| 2026-05-20 | APP-017 PM draft: § Reconcile empty roster on load — R1–R3, APP-018 batch boundary (017 force active / 018 restore step+fields), tests T-017a–e; checklist + APP-016 Consumers updated |
| 2026-05-20 | APP-018 PM draft: § Creation restore on continue / relaunch (G1–G3); relaunch first-turn + resume paths; merge order APP-018 before APP-017; tests T-018a–f; persist bullet; corrected APP-017 merge order |
| 2026-05-20 | APP-017 PM r2 (QA round 1): R1b roster vs characters; T-017f ROSTER_SETUP no-op; spec AC mapping; T-017c stale-snapshot note |
| 2026-05-20 | APP-018 PM round 2: G3a unified with G1 (saved `awaiting` precedence, not live-only); T-018b live `SETUP` + saved `CHARACTER_CREATION`; ticket Expected files include `app/tests/` |
| 2026-05-21 | APP-017 done: `_read_saved_engine_status`, `_effective_awaiting_for_reconcile`, `_force_creation_active_if_reconcile_needed`; sync prelude (APP-018 restore → force-active); roster-only gates; `test_reconcile_empty_roster_on_load.py` T-017a–f, T-017c2 |
| 2026-05-21 | APP-019 done: `_setup_new_game_failure_message`, `_map_setup_new_game_cause`, `PlayerDeathResult.already_emitted`; contexts A/B/C dual JSONL via `_emit_recovery_narration`; combat callers skip `_emit_narration` on failure; `test_setup_new_game_failure.py` T-019a–f |
| 2026-05-21 | APP-018 done: `_restore_creation_from_session_state()` + G1 gate + G3a–c in `orchestrator.py`; NAME clobber removed on resume success; creation import removed from `_restore_history`; `test_creation_restore.py` T-018a–f |
