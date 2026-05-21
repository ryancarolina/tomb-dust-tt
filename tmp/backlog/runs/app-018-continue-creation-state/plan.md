# Implementation Plan: APP-018-continue-creation-state

**Status:** draft (Dev plan round 1)  
**backlog_ticket:** APP-018  
**ticket_path:** [tmp/backlog/app-018-continue-restores-creation-state.md](../../app-018-continue-restores-creation-state.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md) § Creation restore on continue / relaunch (APP-018)  
**run-folder:** `tmp/backlog/runs/app-018-continue-creation-state/`  
**Spec:** [spec.md](spec.md) · [research-brief.md](research-brief.md) · [qa-spec-pass.md](qa-spec-pass.md)

## Approach

Add orchestrator-owned **`_restore_creation_from_session_state()`** that evaluates **G1**, imports **`creation_state`** when the gate passes, and is invoked at **G3a–c** before routing, sync, NAME clobber, and APP-071 variant B copy. Use a **once-only relaunch guard** so later turns do not overwrite in-memory FSM progress with stale disk. **Remove** the post-resume `CreationState(active=True, step="NAME")` block (~573–576). **Do not** edit `ui/app.py` (APP-064 boot unchanged).

**Batch:** APP-018 restore runs **before** APP-017 force-active (canonical merge order). Ship helper in APP-018; APP-017 calls the same helper first in its reconcile entry — APP-018 must not block on APP-017 landing.

---

## Root cause (current vs required)

| Path | Today | Required (G1–G3) |
|------|--------|-------------------|
| Relaunch, first desk input | `creation.active == false`; exploration/LLM | G3a: restore when G1, then `_creation_turn` |
| `continue` / `load game`, resume **fail** | Variant B uses empty in-memory `creation.step` | G3b: restore **before** `_resume_failure_message` |
| Resume **success** + `CHARACTER_CREATION` | `_restore_history` may import, then **NAME clobber** | G3c: restore once, delete NAME reset |
| UI `_load_session` | Parallel import; race with worker | Orchestrator owns FSM; UI unchanged |

NAME clobber (delete):

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

Partial disk read today (`_restore_history` — no `engine_status`, no G1):

```123:137:app/gm/orchestrator.py
    def _restore_history(self):
        ...
            creation_data = data.get("creation_state")
            if creation_data and creation_data.get("active"):
                self.creation = CreationState.from_dict(creation_data)
```

---

## G1 gate — `_creation_restore_gate(data, live_status) -> bool`

Pure evaluation on loaded JSON + live `bridge.status()` (caller loads file once).

| # | Rule | Implementation |
|---|------|----------------|
| **G1d** | Live roster non-empty → **no restore** | `if live_status.get("roster"): return False` |
| **G1a** | `awaiting == CHARACTER_CREATION` | If `engine_status` key present and `engine_status.get("awaiting")` is not `None`: use **saved** `awaiting` only — must equal `"CHARACTER_CREATION"`. Else (legacy / absent snapshot): require **live** `awaiting == "CHARACTER_CREATION"`. **Stale rule:** saved `awaiting != CHARACTER_CREATION` → **no restore** even if live matches (post–`new game` / APP-015 wipe). |
| **G1c** | Empty roster | If snapshot has `engine_status.roster`: require `== []`. Else require live `roster` empty (already enforced by G1d for live). |
| **G1b** | Active creation block | `creation_state` exists and `creation_state.get("active") is True` |

**Invalid step after import:** If `step` missing or not in `CREATION_STEPS`, treat as no restore (or no-op import) — do not fabricate NAME except via existing `_sync_creation_from_status` `WORLD_INTRO` → `NAME`.

Return `False` on missing file, parse error, or any failed row.

---

## Restore helper — `_restore_creation_from_session_state() -> bool`

**Location:** `app/gm/orchestrator.py` (near `_session_state_path`, `import_creation_state`).

| Step | Action |
|------|--------|
| 1 | If `self._creation_disk_restore_done`: return `False` (once-only guard — see below) |
| 2 | `save_path = self._session_state_path()`; if not exists → `False` |
| 3 | `data = json.loads(...)`; `live = self.bridge.status()` (try/except → `{}`) |
| 4 | If not `_creation_restore_gate(data, live)`: return `False` |
| 5 | `import_creation_state(data.get("creation_state"))`; assert `self.creation.active` |
| 6 | Set `self._creation_disk_restore_done = True`; return `True` |

**Does not** call `_sync_creation_from_status` — callers run sync **after** restore per merge order.

**Refactor `_restore_history`:** Keep narration `orchestrator_history` + combat import only; **remove** creation import from `_restore_history` (avoid double-import). Success-path resume calls `_restore_history()` then `_restore_creation_from_session_state()` (or helper first if history ordering matters — history independent of creation).

---

## Once-only relaunch guard

| Field | Value |
|-------|--------|
| `Orchestrator.__init__` | `self._creation_disk_restore_done: bool = False` |
| After successful restore (step 6 above) | Set `True` |
| `setup_new_game` / `_reset_creation_for_new_game` | Reset to `False` so intentional wipe can restore NAME on next load |
| Effect | G3a first desk turn restores once; later `process_turn` (e.g. race pick, second `continue`) does **not** re-read disk over player progress |
| G3b / G3c | Same flag — first successful restore per orchestrator lifetime unless `new game` resets |

**QA note (non-blocking):** If resume fail path must re-read disk after player cleared creation in-memory without `new game`, that edge is out of scope; `new game` resets flag.

---

## Call sites (G3) — `process_turn`

### G3a — Relaunch first turn

Insert **after** `new game` / `start` / `new` early return (~535–540), **before** resume branch and **before** `if self.creation.active: return self._creation_turn`:

```python
if lower not in ("new game", "start", "new"):
    self._restore_creation_from_session_state()
```

Covers desk input (`Dwarf`), `continue`, etc. G1 uses saved `awaiting` when snapshot present (T-018b: live `SETUP` + saved `CHARACTER_CREATION`).

### G3b — Resume failure

Inside `elif lower in ("continue", "resume", "load", "load game")`, when `not result.get("ok")`:

```python
self._restore_creation_from_session_state()
message = self._resume_failure_message(result)
```

Update **`test_load_game_mid_creation_variant_b`** expectations: after fix, variant B can use disk RACE without in-memory advance — extend in `test_creation_restore.py` (T-018a), keep APP-071 regression in `test_session_resume_failure.py`.

### G3c — Resume success

After `run_ended` branch, on success path (~566):

```python
self._restore_history()
self._restore_creation_from_session_state()
self._sync_creation_from_status()
self._sync_combat_from_status()
status = self.bridge.status()
if status.get("awaiting") == "CHARACTER_CREATION" and not status.get("roster"):
    if not self.creation.active:
        # APP-017: force active only — no NAME reset (018 removed clobber)
        self.creation.active = True
        if self.creation.step == "WORLD_INTRO":
            self.creation.step = "NAME"
    return self._creation_turn("[SYSTEM: Resume character creation. ...]")
```

**Delete:** inner `_restore_history()` duplicate, `CreationState(active=True, step="NAME")` block.

**APP-017 placeholder:** If 017 lands in same batch, replace inline force-active with `_reconcile_empty_roster_on_load()` that calls `_restore_creation_from_session_state()` then force-active — 018 does **not** implement 017 force-active unless batching.

---

## Merge with APP-017 (batch)

Canonical order (domain § R3 / run spec):

```
1. _restore_creation_from_session_state()   # APP-018 — fields + step
2. APP-017 reconcile — active=True if still inactive + G1-like awaiting/roster
3. _sync_creation_from_status()
4. _creation_turn / recap
```

| Ticket | This plan |
|--------|-----------|
| **APP-018** | Implements helper + G3; removes NAME clobber; G3a guard |
| **APP-017** | Consumes helper at step 1; adds force-active at step 2 only when `not creation.active` after restore |
| **Independence** | 018 tests pass without 017; T-018b covers saved `CHARACTER_CREATION` + live `SETUP` via G3a alone |
| **Shared surface** | Single `_restore_creation_from_session_state()` — 017 must not duplicate disk read |

**`_sync_creation_from_status` (018 touch):** When implementing 017 in batch, switch empty check from `not status.get("characters")` to `not status.get("roster")` in 017 only; 018 does not require that change for T-018a–f if tests monkeypatch `roster: []`.

---

## Task breakdown

### WS1 — Helper + gate + flag (`app/gm/orchestrator.py`)

| Task | Detail |
|------|--------|
| W1.1 | Add `_creation_disk_restore_done` on `__init__`; reset in `setup_new_game` |
| W1.2 | Implement `_creation_restore_gate` + `_restore_creation_from_session_state` |
| W1.3 | Strip creation import from `_restore_history` |
| W1.4 | Wire G3a / G3b / G3c; remove NAME clobber block |

### WS2 — Tests (`app/tests/`)

| Task | Detail |
|------|--------|
| W2.1 | Add `test_creation_restore.py` with `seed_session_state(tmp_path, monkeypatch)` patching `Orchestrator._session_state_path` |
| W2.2 | Implement T-018a–f per table below |
| W2.3 | Extend `test_session_resume_failure.py` if T-018a overlaps variant B — prefer new module for disk seeds |

### WS3 — Spec sync (on ticket close)

| Task | Detail |
|------|--------|
| W3.1 | Domain spec checklist + changelog (APP-018 done) |
| W3.2 | `release APP-018 --done` |

---

## Test plan — T-018a–f

**Fixture pattern:** `@pytest.fixture` patches `gm.orchestrator.Orchestrator._session_state_path` → `tmp_path / "session_state.json"`. Seed JSON via helper. Use existing `orchestrator` fixture + `monkeypatch` on `bridge.session_resume` / `bridge.status` as needed.

| ID | Setup | Action | Assert |
|----|--------|--------|--------|
| **T-018a** | Seed: `engine_status.awaiting=CHARACTER_CREATION`, `roster=[]`, `creation_state.active=true`, `step=RACE`, `name` set | `session_resume` → `ok: false`; `process_turn("continue")` | `creation.step == "RACE"`; variant B text contains `race`; footer `[Awaiting: RACE_INPUT]` |
| **T-018b** | Same seed; `bridge.status` returns `awaiting=SETUP`, `roster=[]` | `process_turn("Dwarf")` (non–new-game) | G3a restores; `_creation_turn` path (`creation.active`, step RACE) — mock LLM or assert step before/after without full LLM if using spy |
| **T-018c** | Seed RACE on disk; `session_resume` → `ok: true`; `status` → `CHARACTER_CREATION`, `roster=[]` | `process_turn("load game")` | `creation.step == "RACE"` (not NAME); no `CreationState(..., step="NAME")` after resume |
| **T-018d** | Seed **without** `engine_status`; live status `CHARACTER_CREATION`, empty roster; active `creation_state` step SKILLS | `process_turn("continue")` fail | `creation.step == "SKILLS"` |
| **T-018e** | Seed post-finalize: `engine_status.roster` non-empty **or** `awaiting=PLAYER_ACTIONS` | `process_turn("continue")` | Creation not imported from stale block; step unchanged from default inactive |
| **T-018f** | Seed SKILLS + `CHARACTER_CREATION`; run `setup_new_game()` (APP-015 clears disk) | `process_turn("continue")` or desk input | No restore to SKILLS; disk NAME-only; `creation.step` in NAME flow |

**Regression (existing):**

```bash
cd app && python -m pytest tests/test_engine_status_on_save.py -q
cd app && python -m pytest tests/test_session_resume_failure.py -q
cd app && python -m pytest tests/test_creation_block_on_new_game.py -q
cd app && python -m pytest tests/test_creation_restore.py -q
cd app && python -m pytest tests -q -k "creation_restore or continue_creation or app018"
```

**T-018b implementation note:** Prefer asserting `creation.step == "RACE"` and `creation.active` immediately after first `process_turn` with spied `_creation_turn` or second turn only if first turn triggers restore without needing LLM completion.

---

## Verification (impl complete)

| Check | Command / action |
|-------|------------------|
| Unit | pytest commands above |
| Manual (Stage 7) | [human-test-plan.md](human-test-plan.md) — RACE/SKILLS autosave → quit → relaunch → `continue` or desk input |
| Drift | Domain § Creation restore matches code |
| Batch | If APP-017 in same PR: run `test_reconcile_empty_roster_on_load.py` after merge order wired |

---

## Risks

| Risk | Mitigation |
|------|------------|
| `session_state.json` path is under `app/`, not workspace | Tests **must** patch `_session_state_path` |
| Double restore via `_restore_history` + helper | Remove creation from `_restore_history` |
| Stale `creation_state` after `new game` | G1a saved `awaiting` + APP-015 `pop(engine_status)`; T-018f |
| Thread race with UI `_load_session` | Orchestrator restore on G3b/c/G3a; no `ui/app.py` change |
| APP-017 duplicate logic | Document merge order; 017 calls shared helper only |

---

## Files (ticket Expected files)

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | Helper, gate, G3a–c, flag, remove NAME clobber, `_restore_history` trim |
| `app/tests/test_creation_restore.py` | **New** — T-018a–f (primary) |
| `app/tests/test_session_resume_failure.py` | Optional tweak if variant B test needs disk seed comment |
| `tmp/app-session-persistence-spec.md` | Changelog on close only |

**Out of scope:** `app/ui/app.py`, `find_save_campaign`, APP-064 boot chips.
