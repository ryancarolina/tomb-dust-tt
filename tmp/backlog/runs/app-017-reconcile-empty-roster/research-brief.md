# Research Brief: APP-017-reconcile-empty-roster

**Date:** 2026-05-20
**Question:** Where and how should load paths reconcile `creation.active == false` with an empty engine roster so the desk FSM is forced back into creation mode?

**backlog_ticket:** APP-017
**ticket_path:** tmp/backlog/app-017-reconcile-empty-roster-on-load.md
**domain_spec:** tmp/app-session-persistence-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) already owns session persistence, reconcile policy (line 16), and APP-016 § Consumers explicitly assigns APP-017 read-path behavior. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Session persistence** covers `session_state.json`, autosave, and resume — no new domain spec required.

## Summary

APP-017 closes a gap left by APP-016: `engine_status` is written on save but **never read**. Today, `_load_session()` and `_restore_history()` restore `creation_state` and call `_sync_creation_from_status()` against **live** `bridge.status()` only. When `creation_state` is absent or `active: false` on disk but the saved (or live) engine snapshot shows an **empty roster**, the orchestrator can remain in non-creation mode — suggestion chips go empty (`test_inactive_creation_ignores_step`) and the player may enter exploration/combat LLM paths instead of the desk FSM.

Successful `load game` with a live `CHARACTER_CREATION` session already has a partial guard in `process_turn` (lines 572–579), but the UI `_load_session()` path runs **before** `session_resume()` and does not consult saved `engine_status`. The fix belongs primarily in `app/gm/orchestrator.py`: extend reconcile logic (likely `_sync_creation_from_status` and/or a dedicated helper invoked from existing load hooks) to treat **empty roster + inactive creation** as “force creation mode”, using saved `engine_status` when live engine state is missing or `awaiting: SETUP`. APP-018 (same batch) owns restoring step/fields once active; APP-017 owns flipping `creation.active` to `true`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Ticket scope | `app/gm/orchestrator.py` | Expected files per ticket; all reconcile helpers should live here |
| UI load (caller) | `app/ui/app.py` `_load_session`, `_process_turn` | Queues `load_session` before `process_turn` on load/continue/resume; calls `import_creation_state`, `_sync_creation_from_status` — does **not** read `engine_status` |
| UI save (producer) | `app/ui/app.py` `_save_session` | Writes full `get_status()` under `engine_status` (APP-016) |
| Session file | `app/session_state.json` | Keys: `creation_state`, `engine_status`, `orchestrator_history`, UI fields |
| Engine status shape | `play/tomb_gm/cli/cmd_core.py` `handle_status` | `roster` = slotted living chars; `characters` = all campaign rows; `awaiting` derived from roster/char presence |
| Creation FSM | `app/gm/creation.py` `CreationState` | Default `active=False`; `export_creation_state()` returns `None` when inactive — autosave can drop creation block while `engine_status` still shows mid-creation |
| Suggestions (symptom) | `app/ui/suggestions.py`, `Orchestrator.get_player_suggestions` | `creation_active=False` + `engine_awaiting=CHARACTER_CREATION` → **no chips** (documented failure mode) |
| Bridge | `app/gm/bridge.py` `status()`, `session_resume()`, `has_save()` | Live truth for `_sync_creation_from_status`; resume requires slotted living character |
| Related batch | APP-018, APP-019 | 018 restores FSM fields; 019 surfaces new-game errors — out of 017 scope |

## Code-path traces

### Flow A — Player types `load game` / `continue` / `resume`

1. Entry: `app/ui/app.py` `_process_turn` — if command is load family, queues `("load_session", None)` **before** orchestrator turn.
2. UI handler: `_load_session()` reads `session_state.json`, restores narration/map/history, then:
   - `orchestrator.import_creation_state(data.get("creation_state"))`
   - `orchestrator._sync_creation_from_status()` (live bridge only)
   - `orchestrator._sync_combat_from_status()`
3. Orchestrator: `process_turn` → `bridge.session_resume()`.
4. On **failure**: APP-071 recovery narration; creation may stay inactive despite disk `engine_status.roster == []` — **APP-017 gap**.
5. On **success**: `_restore_history()` (re-reads disk creation/history), `_sync_creation_from_status()`, then if live `awaiting == CHARACTER_CREATION` and empty `roster` and not `creation.active`, resets to `CreationState(active=True, step="NAME")` and `_creation_turn` — **step reset is APP-018 territory**.

### Flow B — `_restore_history()` (orchestrator-only disk read)

1. Entry: `Orchestrator._restore_history()` — called after successful `session_resume`, not at boot.
2. Reads `session_state.json`; restores `orchestrator_history`, `creation_state` (if `active`), `combat_state`.
3. Does **not** read `engine_status`.
4. Exit: caller runs `_sync_creation_from_status()`.

### Flow C — `_sync_creation_from_status()` (current reconcile)

1. Entry: `Orchestrator._sync_creation_from_status()` — called from `_load_session` and post-resume paths.
2. Live `status = bridge.status()`.
3. If `roster` non-empty → `creation.active = False`, `step = WORLD_INTRO`.
4. Elif `awaiting == CHARACTER_CREATION` and **not** `characters` → `creation.active = True` (reset step NAME if was WORLD_INTRO).
5. Else → `creation.active = False`.
6. **Gap:** uses `characters` (all rows), not `roster`; ignores saved `engine_status`; when live session absent (`awaiting: SETUP`), always deactivates creation even if disk snapshot says empty roster mid-creation.

### Flow D — Autosave can desync creation block from engine

1. Mid-creation play → `_save_session()` writes `creation_state` (only if `export_creation_state()` non-null) + `engine_status` (always when `get_status()` succeeds).
2. If memory `creation.active` becomes false (sync else-branch, bug, or manual state), next save writes `creation_state: null` but `engine_status.awaiting == CHARACTER_CREATION`, `engine_status.roster == []` (T4a in `test_engine_status_on_save.py`).
3. On next load (Flow A), `import_creation_state(None)` leaves default inactive `CreationState`; reconcile must use `engine_status` to re-enter creation.

### Flow E — Boot (out of ticket AC, context only)

1. `_init_orchestrator` creates fresh `Orchestrator`; **no** `_load_session`, **no** `_sync_creation_from_status`.
2. APP-064: startup `has_save` from engine only; empty roster → `new game` chips only.
3. Player must type load/new; APP-017 AC is **on load**, not boot auto-restore (APP-018 may extend continue behavior).

## Existing specs & docs

- Ticket: [`tmp/backlog/app-017-reconcile-empty-roster-on-load.md`](../../app-017-reconcile-empty-roster-on-load.md) — AC: empty roster + inactive creation → force creation mode.
- Domain spec: [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) — reconcile policy; APP-016 § Consumers assigns APP-017 read path; APP-016 S5d: absent/null `engine_status` must not error.
- Batch: [`tmp/backlog/runs/batch-board-APP-017-APP-018-APP-019.md`](../batch-board-APP-017-APP-018-APP-019.md) — parallel implementation; coordinate with APP-018 (step restore vs force-active).
- AGENTS.md: no ticket no change; spec sync on close required.

## Tests & commands

No APP-017-specific tests exist yet. Recommended cases for PM/Dev (names illustrative):

| ID | Case | Expected |
|----|------|----------|
| **T-017a** | Save mid-creation; mutate in-memory `creation.active=False`; `_load_session` or orchestrator reconcile helper with disk `engine_status` | `creation.active is True` after reconcile |
| **T-017b** | Disk: `creation_state: null`, `engine_status.roster==[]`, live `awaiting: SETUP` (no active session) | Force creation active (NAME or preserved step per 018 boundary) |
| **T-017c** | Post-finalize save: non-empty `engine_status.roster` | Reconcile does **not** reactivate creation |
| **T-017d** | Legacy save: no `engine_status`, `creation_state.active=true` | Behavior unchanged (T4c baseline) |
| **T-017e** | Regression: `get_player_suggestions` after reconcile of inactive+CHARACTER_CREATION | Non-empty creation chips or NAME-appropriate chips (not `[]`) |

```bash
# Existing coverage touching adjacent behavior
python -m pytest app/tests -q -k "engine_status or load_session or session_resume or creation_block"

# After implementation
python -m pytest app/tests -q -k "reconcile or empty_roster or app_017"
```

Fixtures: reuse `save_path` monkeypatch from `test_engine_status_on_save.py`, `isolated_workspace` orchestrator from `conftest.py`; never write dev `app/session_state.json`.

## Risks & unknowns

1. **APP-017 vs APP-018 boundary** — Forcing `active=True` may reset step to NAME (existing resume branch) vs restoring saved step; PM must split AC so 017 does not silently scope-creep into full FSM restore.
2. **`characters` vs `roster` in `_sync_creation_from_status`** — Engine sets `awaiting: ROSTER_SETUP` when unslotted chars exist; ticket AC says “empty roster” — confirm whether orphan characters should still force creation or a different recovery path.
3. **Expected files vs UI caller** — Reconcile must run on `_load_session` path; if new public method is needed, ticket lists orchestrator only — implement via `_sync_creation_from_status` reading `_session_state_path()` internally to avoid `ui/app.py` edits, or expand ticket Expected files.
4. **Live-vs-saved precedence** — When live engine shows roster but saved `engine_status` empty (stale snapshot), live should win; define ordering: live `bridge.status()` first, fall back to saved snapshot only when roster empty and creation inactive.
5. **Missing `engine_status`** — Legacy saves and S5d omit path must still reconcile from live engine when session exists; absent snapshot cannot block load.
6. **Double reconcile** — `_load_session` and post-resume `_restore_history` both sync; idempotent reconcile required.
7. **`export_creation_state() → None`** — Root cause of disk `creation_state` loss; APP-017 mitigates on read but does not fix write path (acceptable per ticket scope).

## Raw notes

- `CreationState` default: `active=False` (`creation.py:218`).
- `export_creation_state` returns `None` when inactive (`orchestrator.py:193–196`) → `_save_session` persists `"creation_state": null`.
- APP-016 T4a proves mid-creation save shape: `engine_status.awaiting == CHARACTER_CREATION`, `roster == []`.
- `test_inactive_creation_ignores_step` (`test_ui_suggestions.py:46–53`) — reproduces empty chips when `creation_active=False` and `engine_awaiting=CHARACTER_CREATION`.
- `test_load_session_legacy_without_engine_status` (T4c) intentionally does **not** call `_sync_creation_from_status` via full reconcile — documents pre-017 load behavior; update carefully.
- `_is_mid_creation_resume_failure` already inspects disk `creation_state` for APP-071 variant B but not `engine_status`.
- Engine `has_save_session` ≡ slotted living character — mid-creation empty roster never passes `has_save()` (APP-064).
