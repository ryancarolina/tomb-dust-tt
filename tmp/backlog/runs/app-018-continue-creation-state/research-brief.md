# Research Brief: APP-018-continue-creation-state

**Date:** 2026-05-20  
**Question:** How should **continue** / **load game** restore the in-progress creation FSM when the engine (live or saved snapshot) has `awaiting == CHARACTER_CREATION`, using `creation_state` and `engine_status` from `session_state.json`?

**backlog_ticket:** APP-018  
**ticket_path:** tmp/backlog/app-018-continue-restores-creation-state.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) is registered in [`tmp/app-master-spec.md`](../../../app-master-spec.md) as **Session persistence** (owns `session_state.json`, autosave, resume). APP-016 § Engine status snapshot — Consumers explicitly assigns **APP-018** the read path for `engine_status` + `creation_state` when `awaiting == CHARACTER_CREATION`. Domain spec test intent (“Save mid-creation → relaunch → same `creation.step`”) lives in the same file. No new registry row required.

## Summary

APP-016 writes `creation_state` and full `engine_status` on every `_save_session()`. APP-015 clears stale blocks on **`new game`**. **No code today consumes `engine_status` on load** — `_load_session()` in `ui/app.py` imports `creation_state` only and never reads `engine_status`.

On **`load game` / `continue`**, `process_turn` calls `bridge.session_resume()` first. Mid-creation workspaces usually have **no resumable engine save** (`find_save_campaign` requires a living slotted character), so resume fails and APP-071 variant B narrates using **in-memory** `self.creation.step` — which is **empty after relaunch** because `Orchestrator.__init__` does not hydrate from disk. `_is_mid_creation_resume_failure()` reads disk for variant **selection** only; it does not call `import_creation_state`.

When `session_resume` **succeeds** with `awaiting == CHARACTER_CREATION` and empty `roster`, orchestrator **overwrites** restored state: if `not self.creation.active`, it sets `CreationState(active=True, step="NAME")` before `_creation_turn` — the same bug class noted in APP-006 research (“Resume overwrote restored creation step with NAME”). `_restore_history()` can import `creation_state` from disk but runs **after** failed resume only on the success branch ordering is wrong on success path (restore called at 566, then NAME reset at 573–576).

UI queues `load_session` at the start of a load turn; `_load_session()` imports creation and calls `_sync_creation_from_status()` on the main thread while `process_turn` runs in a worker — **race-prone** and not a substitute for orchestrator-owned restore. Ticket **Expected files** list only `app/gm/orchestrator.py`; boot-time “relaunch → same step” likely needs orchestrator-side hydration (e.g. `__init__` or first-turn gate), not only UI `_load_session`.

APP-017 (batch) reconciles **inactive** creation + empty roster; APP-018 should **restore** active FSM from save when `CHARACTER_CREATION` — coordinate so restore runs before force-creation and before NAME reset.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Load / continue commands | `app/gm/orchestrator.py` — `process_turn` (~542–592) | `session_resume`; CHARACTER_CREATION branch ~572–579 |
| Disk restore (partial) | `orchestrator.py` — `_restore_history`, `import_creation_state`, `_session_state_path` | History + creation; no `engine_status` |
| Resume failure / variant B | `orchestrator.py` — `_is_mid_creation_resume_failure`, `_resume_failure_message` | Reads disk for signals; does not import into FSM |
| Creation ↔ engine sync | `orchestrator.py` — `_sync_creation_from_status` | Forces `active=True` when `CHARACTER_CREATION` + no `characters`; only downgrades `WORLD_INTRO` → `NAME` |
| App save write | `app/ui/app.py` — `_save_session` | `creation_state`, `engine_status` (APP-016) |
| App save read | `app/ui/app.py` — `_load_session` | Import creation/combat; **ignores `engine_status`**; comment “only valid when DB has no roster” |
| Load turn ordering | `app/ui/app.py` — `_process_turn` (~281–289) | Queues `load_session` then calls `process_turn` in worker thread |
| Engine resume gate | `play/tomb_gm/domain/session.py` — `find_save_campaign`, `resume_session` | Resume fails without slotted living character |
| Engine awaiting | `play/tomb_gm/cli/cmd_core.py` — `handle_status` | Empty roster → `CHARACTER_CREATION` |
| Creation FSM types | `app/gm/creation.py` — `CreationState.to_dict` / `from_dict` | Full step + picks persisted in `creation_state` |
| Tests (adjacent) | `app/tests/test_engine_status_on_save.py`, `test_session_resume_failure.py`, `test_creation_block_on_new_game.py` | T4a mid-creation snapshot; variant B uses in-memory RACE; no APP-018 restore test |
| Batch | APP-017, APP-019 | Reconcile inactive creation; UI errors for new game |

## Code-path traces

### Save mid-creation (APP-016 — write path)

1. Entry: player advances creation → `_process_turn` `finally` → `_save_session()`.
2. `get_status()` → full dict stored as `engine_status` (`awaiting: CHARACTER_CREATION`, `roster: []` per T4a).
3. `export_creation_state()` when `creation.active` → `creation_state` with `step`, `name`, rolls, table flags, etc.
4. Exit: `app/session_state.json` updated.

### Relaunch (gap — domain test intent)

1. Entry: `python main.py` → `_init_orchestrator` → fresh `Orchestrator()` (`creation.active` default **false**).
2. `bridge.has_save()` false for empty roster → startup **new game** chips only (APP-064).
3. **No** `_load_session()` at boot.
4. Engine workspace may still have **active session** with live `awaiting == CHARACTER_CREATION`.
5. Player input before restore (e.g. race name) → `process_turn` skips `_creation_turn` → exploration/LLM path (**regression risk**).
6. Exit: step not restored until APP-018 adds orchestrator hydration and/or load-path restore.

### `load game` — engine resume fails (common mid-creation)

1. Entry: `_process_turn` queues `load_session`; worker runs `process_turn("load game")`.
2. `bridge.session_resume()` → `find_save_campaign` None → `ok: false`, `no save session found`.
3. `_resume_failure_message` → variant B if `_is_mid_creation_resume_failure()` (memory **or** disk `creation_state` / live `CHARACTER_CREATION`).
4. `_emit_recovery_narration` — **no** `import_creation_state` from disk.
5. Parallel: `_load_session()` may import creation on main thread — **unordered** vs step 3; orchestrator may still have `active=False` when message built.
6. Exit: player told correct step in prose only if memory already had step; after relaunch, message may say **name** step incorrectly unless disk import is added.

### `load game` — engine resume succeeds + CHARACTER_CREATION

1. Entry: rare for mid-creation (needs `find_save_campaign`); possible with recovered campaign edge cases.
2. `_restore_history()` — may import `creation_state` from disk.
3. `_sync_creation_from_status()` — aligns with live engine.
4. If `awaiting == CHARACTER_CREATION` and empty `roster`: if `not self.creation.active` → **force** `step="NAME"` (lines 573–576) — **clobbers** restored step.
5. `_creation_turn("[SYSTEM: Resume character creation…]")`.
6. Exit: desk restarts at NAME despite save at RACE/SKILLS/etc.

### `_load_session` (UI — partial restore)

1. Entry: main thread on `load_session` queue message.
2. Restore narration, map, `orchestrator.history`.
3. `import_creation_state(data.get("creation_state"))` — no `engine_status` consult.
4. `_sync_creation_from_status()` — live DB; may set `active=True` but preserves non–`WORLD_INTRO` steps.
5. Exit: UI state richer; orchestrator may already have returned from failed `session_resume` without matching FSM.

### Intended APP-018 restore (research recommendation — not implementation)

1. Read `session_state.json` via `_session_state_path()` (or shared helper).
2. Determine `awaiting`: prefer saved `engine_status.awaiting` when present (APP-016), else live `bridge.status().awaiting`.
3. When `awaiting == CHARACTER_CREATION` and `creation_state.active` on disk: `import_creation_state` + set `creation.active=True`; do **not** reset to NAME unless step missing/invalid.
4. Invoke on: successful resume CHARACTER_CREATION branch, failed resume variant B (before narration), and **orchestrator boot** if live engine + app save agree — to satisfy relaunch AC within `orchestrator.py` only.
5. Call **before** `_sync_creation_from_status` NAME downgrade or APP-017 force-creation logic.

## Existing specs & docs

- Ticket: [`tmp/backlog/app-018-continue-restores-creation-state.md`](../../app-018-continue-restores-creation-state.md) — AC: restore creation from save when `awaiting == CHARACTER_CREATION`; consumer of APP-016 snapshot.
- Domain: [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) — § Engine status snapshot Consumers (APP-017/018); Tests “Save mid-creation → relaunch → same `creation.step`”; APP-015 defers load restore to APP-018.
- Master: [`tmp/app-master-spec.md`](../../../app-master-spec.md) — Session persistence row.
- Related closed: APP-064 (boot does not offer load without engine save), APP-071 (failure copy), APP-016 (write `engine_status`).
- Character creation: [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) — FSM steps/labels for restored `step`.
- APP-064 research: [`tmp/backlog/runs/app-064-startup-save-prompt/research-brief.md`](../app-064-startup-save-prompt/research-brief.md) — documents mid-creation load failure; points to APP-018.

## Tests & commands

```bash
# Existing coverage (no restore-after-relaunch test)
cd app && python -m pytest tests/test_engine_status_on_save.py -q
cd app && python -m pytest tests/test_session_resume_failure.py -q
cd app && python -m pytest tests/test_creation_block_on_new_game.py -q

# Suggested APP-018 targets (PM/Dev)
# - Relaunch: new game → NAME → RACE → quit → relaunch → same step without NAME reset
# - load game fail mid-creation: orchestrator.creation.step matches saved creation_state
# - load game success + CHARACTER_CREATION (fixture): step preserved from disk
# - engine_status absent (legacy): fall back to live status + creation_state only

cd app && python -m pytest tests -q -k "creation_restore or continue_creation or engine_status"
```

Manual (Stage 7):

```text
cd app && python main.py
# Mid-creation at RACE or SKILLS → Escape (autosave) → quit → relaunch
# Type load game OR continue (per PM spec) → desk at same step, tables/inputs coherent
# Inspect session_state.json: creation_state.step + engine_status.awaiting
```

## Risks & unknowns

- **Relaunch without `load game`:** Domain spec test implies same step after relaunch; ticket Expected files omit `ui/app.py`. Boot hydration must live in `orchestrator.py` or AC must narrow to “after load/continue command” — PM must decide.
- **`session_resume` almost always fails** mid-creation: restore logic must run on **failure** path and/or init, not only post-success resume.
- **Thread race:** `load_session` vs `process_turn` — orchestrator-owned restore avoids relying on UI queue ordering.
- **`engine_status` vs live drift:** Saved snapshot may disagree with live engine after partial wipe; need precedence rules (snapshot for `awaiting`, creation block for FSM fields).
- **APP-017 overlap:** “force creation mode” when inactive + empty roster may duplicate restore if ordering wrong — batch implementers should share one helper.
- **`_sync_creation_from_status`:** Uses `not status.get("characters")` (line 186) vs `roster` elsewhere — verify empty-roster mid-creation still sets `active=True`.
- **Stale `creation_state` after `new game`:** APP-015 clears to NAME — restore must not run across intentional wipe (check `step==NAME` + fresh session).
- **Post-finalize save:** `creation_state` may be null/inactive while `engine_status.awaiting != CHARACTER_CREATION` — restore must no-op.
- **No automated APP-018 tests yet** — pytest gap for relaunch + load failure paths.

## Raw notes

- NAME reset on successful resume (bug):

```572:579:app/gm/orchestrator.py
            if status.get("awaiting") == "CHARACTER_CREATION" and not status.get("roster"):
                if not self.creation.active:
                    self._restore_history()
                if not self.creation.active:
                    self.creation = CreationState(active=True, step="NAME")
                return self._creation_turn(
                    "[SYSTEM: Resume character creation. Continue from the current step.]"
                )
```

- `_restore_history` imports creation but not `engine_status`:

```123:137:app/gm/orchestrator.py
    def _restore_history(self):
        ...
            creation_data = data.get("creation_state")
            if creation_data and creation_data.get("active"):
                self.creation = CreationState.from_dict(creation_data)
```

- `_load_session` ignores `engine_status`:

```446:451:app/ui/app.py
                self._orchestrator.import_creation_state(data.get("creation_state"))
                self._orchestrator.import_combat_state(data.get("combat_state"))
                self._orchestrator._sync_creation_from_status()
```

- Domain consumer table (APP-016):

| Ticket | Role |
|--------|------|
| APP-017 | Reconcile empty roster on load |
| APP-018 | Restore creation when `CHARACTER_CREATION` |

- APP-006 research: “Resume overwrote restored creation step with NAME” — same lines as above.
