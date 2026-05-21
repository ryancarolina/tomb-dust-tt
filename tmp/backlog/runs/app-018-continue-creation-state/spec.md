# Spec: APP-018-continue-creation-state

**Status:** draft (PM round 2 — QA spec revision)  
**backlog_ticket:** APP-018  
**ticket_path:** [tmp/backlog/app-018-continue-restores-creation-state.md](../../app-018-continue-restores-creation-state.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md)  
**registry_gap:** false (per research-brief)  
**Domain specs touched:** `tmp/app-session-persistence-spec.md`

## Problem

APP-016 persists `creation_state` and `engine_status` on every autosave. **No orchestrator path consumes `engine_status` on load.** After relaunch, `Orchestrator.__init__` leaves `creation.active == false` even when the live engine still has `awaiting == CHARACTER_CREATION` and `session_state.json` holds an in-progress step (e.g. `RACE`, `SKILLS`).

| Path | Symptom |
|------|---------|
| **Relaunch** (no boot `_load_session`) | Player types desk input before restore → exploration/LLM path; step lost |
| **`load game` / `continue`**, resume **fails** (typical mid-creation) | APP-071 variant B prose uses **in-memory** `creation.step` (empty → wrong **name** step) |
| **`load game`**, resume **succeeds** + `CHARACTER_CREATION` | `_restore_history` may import disk, then lines 573–576 **force** `step="NAME"` when `not creation.active` |
| **UI `_load_session`** | Imports `creation_state` on main thread **in parallel** with worker `process_turn` — race-prone; not a substitute for orchestrator-owned restore |

Ticket AC: when `awaiting == CHARACTER_CREATION`, **continue** must restore the creation FSM from save.

## Goals

- **P0:** Orchestrator-owned restore from `session_state.json` when saved (or live) signals mid-creation `CHARACTER_CREATION` with active `creation_state`.
- **P0:** Satisfy domain test **“Save mid-creation → relaunch → same `creation.step`”** without requiring `ui/app.py` edits (hydration in `app/gm/orchestrator.py` only).
- **P0:** Restore runs **before** NAME reset (lines 573–576), **before** `_sync_creation_from_status` downgrade side effects, and **before** APP-017 “force creation when inactive + empty roster.”
- **P1:** `load` / `load game` / `continue` / `resume` failure path restores FSM **before** variant B narration so footer and step phrase match disk.

## Non-goals

| Deferred | Owner |
|----------|--------|
| Startup `has_save()` / load chip (APP-064) | Unchanged — relaunch still shows **new game** only until player acts |
| Friendly **`new game`** errors | APP-019 |
| Reconcile inactive creation + empty roster (live vs snapshot drift) | APP-017 — runs **after** APP-018 restore |
| Read/consume `engine_status` in `ui/app.py` `_load_session` | Out of Expected files; optional redundancy only |
| Changing `find_save_campaign` / engine resume gate | Out of scope |
| Post-finalize / in-delve resume paths | Non-regression only |

## PM decisions

### Relaunch vs `load game` / `continue`

| Term | Meaning in this ticket |
|------|-------------------------|
| **Relaunch** | Process restart → fresh `Orchestrator`; APP-064 does **not** call `_load_session` at boot |
| **Continue / load** | `process_turn` commands: `continue`, `resume`, `load`, `load game` → `bridge.session_resume()` branch |

**Restore must run in both cases:**

1. **Resume commands** — on failure (before `_resume_failure_message`) and on success (before CHARACTER_CREATION / NAME branch).
2. **Relaunch** — on **first** `process_turn` for any player input **except** `new game` / `start` / `new`, when **G1** passes (same gate as resume — saved `engine_status.awaiting` preferred when present; **not** live-only). Calls `_restore_creation_from_session_state()` before creation/exploration routing (covers live `SETUP` + saved `CHARACTER_CREATION`, APP-017 **T-017b** class). Player may type desk input or `continue`; both hit `process_turn`.

Boot does **not** auto-import app save (APP-064 S4 unchanged). “Relaunch → same step” means **first turn after relaunch** restores FSM before routing — not a startup narration change.

### `engine_status` vs live engine

| Signal | Precedence |
|--------|------------|
| **Gate `awaiting == CHARACTER_CREATION`** | Prefer saved `engine_status.awaiting` when key present and non-null (APP-016); else live `bridge.status().awaiting` |
| **FSM fields** (`step`, `name`, rolls, table flags) | Always from `creation_state` via `import_creation_state` when `creation_state.active` |
| **Roster non-empty** | **No restore** — treat as post-finalize / in-delve (APP-017 may still reconcile inactive creation) |

If saved `engine_status.awaiting != CHARACTER_CREATION` but live engine is `CHARACTER_CREATION` with empty roster: **do not restore** from stale `creation_state` unless live engine also matches (avoid post–`new game` C2 wipe edge where disk still has old step — APP-015 cleared NAME block; trust APP-015 + gate).

If saved says `CHARACTER_CREATION` but live roster non-empty: **no restore**; `_sync_creation_from_status` deactivates creation per today.

### Ordering vs APP-017 (batch)

Shared helper **`_restore_creation_from_session_state()`** (name illustrative) in `orchestrator.py`:

```
1. _restore_creation_from_session_state()   # APP-018 — disk + gate; import_creation_state
2. APP-017 reconcile (inactive + empty roster → force active)  # only if still inactive after (1)
3. _sync_creation_from_status()             # roster / WORLD_INTRO rules; NAME only if step == WORLD_INTRO
4. Remove/replace NAME clobber at old 573–576 — never reset imported step to NAME
5. _creation_turn or resume recap as today
```

APP-018 **must not** depend on APP-017 landing first, but implementers in the same batch should call **(1)** from a single helper both tickets use before force-creation logic.

### `import_creation_state`

- Use existing `import_creation_state(data)` when `data.get("active")` and gate passes.
- After import, ensure `creation.active is True` (import already sets from dict; helper may set active if disk says active).
- **Forbidden:** `CreationState(active=True, step="NAME")` after successful import unless `step` missing, not in `CREATION_STEPS`, or `NAME` is the saved step.
- **WORLD_INTRO** on disk with `CHARACTER_CREATION` awaiting: `_sync_creation_from_status` may map `WORLD_INTRO` → `NAME` (existing rule) — only that downgrade is allowed post-import.

## Requirements (summary)

Full behavior and test contracts: domain spec § **Creation restore on continue / relaunch (APP-018)**.

| ID | Summary |
|----|---------|
| **R1** | Shared restore helper reads `_session_state_path()`, evaluates gate (saved `engine_status` + `creation_state.active` + empty roster) |
| **R2** | **Relaunch:** first `process_turn` (non–`new game`) calls helper when **G1** passes — same normative gate as G3b/G3c; no live-only relaunch carve-out |
| **R3** | **Resume fail:** helper before `_resume_failure_message` when mid-creation signals |
| **R4** | **Resume success:** helper before `_sync_creation_from_status` and before CHARACTER_CREATION branch; delete duplicate NAME reset |
| **R5** | Legacy saves without `engine_status`: gate on live `awaiting` + `creation_state` only |
| **R6** | Post-finalize / non–`CHARACTER_CREATION` / inactive disk block: no-op |
| **R7** | After restore, variant B and `_creation_turn` resume use restored `creation.step` and tables |

## Acceptance criteria mapping

| Ticket AC | Spec / deliverable |
|-----------|-------------------|
| When `awaiting == CHARACTER_CREATION`, restore creation from save | R1–R7; domain § APP-018 |
| Orchestrator + pytest (ticket Expected files) | R2 via `process_turn`; no `ui/app.py`; tests T-018a–f in `app/tests/` |

## Implementation pointers (Dev plan)

| Area | Path | Notes |
|------|------|-------|
| Helper | `app/gm/orchestrator.py` | New `_restore_creation_from_session_state()` → `import_creation_state` + gate |
| Entry: relaunch | `process_turn` top (after `new game` check) | R2 first-turn gate |
| Entry: resume fail | `process_turn` ~542–548 | R3 before `_resume_failure_message` |
| Entry: resume ok | ~566–579 | R4; remove second `_restore_history` + NAME clobber; keep history restore once |
| Existing | `import_creation_state`, `_session_state_path`, `_restore_history` | Consolidate creation import into helper; history may stay in `_restore_history` |
| Sync | `_sync_creation_from_status` | Call **after** restore; do not wipe imported step |
| Batch | APP-017 | Call same helper **before** force inactive → active |

**Regression:** APP-015 `new game` must leave NAME-only disk; R1 gate prevents restoring SKILLS after intentional wipe.

## Test plan

```bash
cd app && python -m pytest tests/test_engine_status_on_save.py -q
cd app && python -m pytest tests/test_session_resume_failure.py -q
cd app && python -m pytest tests/test_creation_block_on_new_game.py -q
cd app && python -m pytest tests -q -k "creation_restore or continue_creation or app018"
```

New tests (suggested IDs in domain spec § Tests APP-018):

| ID | Case |
|----|------|
| **T-018a** | Temp `session_state.json`: `engine_status.awaiting == CHARACTER_CREATION`, `creation_state.step == RACE`, `active: true`; fresh orchestrator + mock bridge status → `process_turn("continue")` fail path → `creation.step == RACE` |
| **T-018b** | Same disk seed as T-018a; mock bridge live `awaiting != CHARACTER_CREATION` (e.g. `SETUP`) with saved `engine_status.awaiting == CHARACTER_CREATION` → first non–`new-game` `process_turn` → step RACE, `_creation_turn` path (G1 saved precedence) |
| **T-018c** | Resume success fixture + CHARACTER_CREATION → step preserved (not NAME) |
| **T-018d** | Legacy JSON without `engine_status`; live `CHARACTER_CREATION` → restore from `creation_state` |
| **T-018e** | `engine_status.awaiting` not `CHARACTER_CREATION` or roster non-empty → no import; regresses post-finalize |
| **T-018f** | After `setup_new_game` (APP-015 NAME disk), old SKILLS block must not restore |

## Human playtest hints (for Stage 7)

- Mid-creation at **RACE** or **SKILLS** → Escape (autosave) → quit → relaunch → type **`continue`** or desk input → same step, code table/footer coherent (not NAME).
- Same session → **`load game`** with no engine save → variant B mentions correct step; answering clerk continues desk.
- Complete character → quit → relaunch → **load game** still loads roster save (T-018e regression).
- **`new game`** after partial creation → NAME only; no restore of prior RACE/SKILLS.

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py`
- `app/tests/test_session_resume_failure.py` (extend for T-018a–c, f)
- `app/tests/test_creation_restore.py` (new module for T-018a–f if cleaner than extending only the above — Dev choice; at least one test file must land)
- `tmp/app-session-persistence-spec.md` — § Creation restore (APP-018)

## Pointers (source of truth)

| Topic | Location |
|-------|----------|
| Restore behavior & tests | [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Creation restore on continue / relaunch (APP-018) |
| Write path / consumers | Same file § Engine status snapshot (APP-016) |
| FSM steps / labels | [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) |
| Research traces | [`research-brief.md`](research-brief.md) |
| Batch ordering | [`batch-board-APP-017-APP-018-APP-019.md`](../batch-board-APP-017-APP-018-APP-019.md) |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-018) |
| 2026-05-20 | PM round 2: relaunch unified with G1 (saved `awaiting` precedence); ticket Expected files + Affected paths include `app/tests/`; T-018b covers live `SETUP` + saved `CHARACTER_CREATION` |
