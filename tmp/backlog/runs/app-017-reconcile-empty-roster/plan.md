# Implementation Plan: APP-017-reconcile-empty-roster

**Status:** draft (Dev plan phase)  
**backlog_ticket:** APP-017  
**ticket_path:** tmp/backlog/app-017-reconcile-empty-roster-on-load.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Summary

APP-016 writes `engine_status` on save but nothing reads it on load. When disk has `creation_state: null` (or memory `creation.active == false`) while the snapshot shows **empty `roster`** and **`awaiting: CHARACTER_CREATION`**, `_sync_creation_from_status()` deactivates creation (live `SETUP` or `characters`-based guard) — suggestion chips go empty (`test_inactive_creation_ignores_step`).

**Fix:** Add disk-aware reconcile helpers in `app/gm/orchestrator.py`, invoke them at the top of `_sync_creation_from_status()` (covers UI `_load_session` and post-resume sync without editing `app/ui/app.py`). Switch the sync guard from `characters` → **`roster`**. Add `app/tests/test_reconcile_empty_roster_on_load.py` for T-017a–f / T-017c2.

**Batch:** APP-018 restore runs **before** APP-017 force-active via optional `_restore_creation_from_session_state` hook (no-op until 018 lands). Domain spec sync on ticket close only (not in impl Expected files).

---

## Root cause (current)

```177:191:app/gm/orchestrator.py
    def _sync_creation_from_status(self) -> None:
        """Ensure we do not stay in creation mode when a roster already exists."""
        try:
            status = self.bridge.status()
        except Exception:
            return
        if status.get("roster"):
            self.creation.active = False
            self.creation.step = "WORLD_INTRO"
        elif status.get("awaiting") == "CHARACTER_CREATION" and not status.get("characters"):
            self.creation.active = True
            if self.creation.step == "WORLD_INTRO":
                self.creation.step = "NAME"
        else:
            self.creation.active = False
```

| Gap | Symptom | Spec ref |
|-----|---------|----------|
| Never reads `session_state.json` → `engine_status` | Live `awaiting: SETUP` + disk mid-creation snapshot → `else` branch deactivates | R2 |
| Empty check uses `characters` not `roster` | `ROSTER_SETUP` (orphan rows) incorrectly treated as mid-creation | R3 |
| `process_turn` resume branch clobbers step | `CreationState(active=True, step="NAME")` at L576 — APP-018 boundary violation | R4 |
| No reconcile on failed `session_resume` | UI `_load_session` syncs before resume; without disk read, inactive stays inactive | R1 |

**Symptom path:** `ui/suggestions.py:95-96` returns `[]` when `engine_awaiting == "CHARACTER_CREATION"` and `creation_active` is false.

**Producer (unchanged):** `app/ui/app.py:393-426` `_save_session()` writes `engine_status` via `get_status()` (APP-016).

**Consumer call sites (fix via sync prelude — no UI edit):**

| Caller | File:symbol | Lines |
|--------|-------------|-------|
| UI load | `app/ui/app.py:_load_session` | 449–451: `import_creation_state` → `_sync_creation_from_status` |
| Resume success | `app/gm/orchestrator.py:process_turn` | 566–567: `_restore_history` → `_sync_creation_from_status` |
| Resume failure | Same file | 542–548: `_load_session` already ran in UI queue; sync at 451 must reconcile from disk |

---

## Code-path traces (current → planned)

### Flow A — UI load (`load game` / `continue` / `resume`)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| A1 | `app/ui/app.py:_process_turn` | ~198: queue `("load_session", None)` before orchestrator | unchanged |
| A2 | `app/ui/app.py:_load_session` | 449: `import_creation_state(data.get("creation_state"))` | unchanged — 018 may extend import gate later |
| A3 | same | 451: `_sync_creation_from_status()` | **Prelude inside sync:** optional `_restore_creation_from_session_state()` → `_force_creation_active_if_reconcile_needed()` → body |
| A4 | `orchestrator.py:process_turn` | 543–548: resume fail → recovery narration | reconcile already applied at A3 |
| A5 | same | 566–579: resume ok → sync → NAME clobber | **Remove L575–576** NAME reset; rely on reconcile + sync (R4) |

### Flow B — Disk desync (target case)

| Step | Action | Planned |
|------|--------|---------|
| B1 | Mid-creation play → `_save_session` | `engine_status.awaiting == "CHARACTER_CREATION"`, `roster == []` (T4a) |
| B2 | Memory `creation.active` → false (sync else-branch or bug) | Next save: `creation_state: null`, snapshot retained |
| B3 | Relaunch → `_load_session` | `import_creation_state(None)` → inactive default |
| B4 | `_sync_creation_from_status` | **Read disk** → force `creation.active = true` when R1 row 1 passes |
| B5 | `get_player_suggestions` | Non-empty chips at desk step (T-017e) |

### Flow C — `_sync_creation_from_status` (planned body)

| Step | Condition | Action |
|------|-----------|--------|
| C0 | Start | Optional APP-018 restore (callable hook) |
| C1 | | `_force_creation_active_if_reconcile_needed()` |
| C2 | `live roster` non-empty | `creation.active = False`, `step = WORLD_INTRO` |
| C3 | `live awaiting == CHARACTER_CREATION` **and** `not live roster` | `creation.active = True`; `WORLD_INTRO` → `NAME` only |
| C4 | else | `creation.active = False` |

**Key change:** C3 guard uses **`roster`**, not `characters` (R3).

### Flow D — Live vs saved precedence (R2)

| Live `awaiting` | Live `roster` | Saved `engine_status` | Force-active? |
|-----------------|---------------|----------------------|---------------|
| `CHARACTER_CREATION` | `[]` | any | Yes if inactive (T-017a) |
| `SETUP` | `[]` | `CHARACTER_CREATION`, `roster: []` | Yes (T-017b) |
| `CHARACTER_CREATION` | `[]` | `roster: [{…}]` (stale) | Yes — live empty wins (T-017c2) |
| `PLAYER_ACTIONS` / post-finalize | non-empty | any | No (T-017c) |
| `ROSTER_SETUP` | `[]`, `characters` non-empty | any | No (T-017f) |
| `SETUP` | `[]` | absent / null | No new force — legacy T-017d path |

Engine derivation (`play/tomb_gm/cli/cmd_core.py:178-182`): empty roster + no chars → `CHARACTER_CREATION`; empty roster + chars → `ROSTER_SETUP`.

---

## New helpers — `app/gm/orchestrator.py`

Place after `_session_state_path()` (~L313) so disk IO is colocated with APP-015 `_clear_creation_block_on_disk`.

### 1. `_read_saved_engine_status(self) -> dict | None`

- Path: `self._session_state_path()` (not hardcoded path in `_restore_history` L126).
- Parse JSON; return `data["engine_status"]` only if value is a `dict`.
- Missing file, parse error, absent key, or `null` → `None` (S5d — no error).

### 2. `_effective_awaiting_for_reconcile(self, live_status: dict) -> str`

Resolve **`awaiting`** for R1 mid-creation gate:

```python
live_awaiting = live_status.get("awaiting") or ""
if live_awaiting and live_awaiting != "SETUP":
    return live_awaiting
saved = self._read_saved_engine_status()
if saved:
    return saved.get("awaiting") or live_awaiting
return live_awaiting
```

Live non-`SETUP` wins. Cold engine (`SETUP`) falls back to saved snapshot (T-017b).

**Roster for empty check:** always `live_status.get("roster") or []` — never saved roster (R2 stale-snapshot rule, T-017c2).

### 3. `_force_creation_active_if_reconcile_needed(self) -> None`

Idempotent; safe to call multiple times per load (R1).

```python
if self.creation.active:
    return
try:
    live = self.bridge.status()
except Exception:
    return

roster = live.get("roster") or []
if roster:  # R1 row 2 — post-finalize / in-delve
    return

live_awaiting = live.get("awaiting") or ""
if live_awaiting == "ROSTER_SETUP":  # R3 / T-017f
    return

effective = self._effective_awaiting_for_reconcile(live)
if effective != "CHARACTER_CREATION":
    return

self.creation.active = True
# R4: do NOT set step=NAME here — APP-018 restores step; only sync body may WORLD_INTRO→NAME
```

### 4. Modify `_sync_creation_from_status(self) -> None`

**Prelude (merge order):**

```python
restore = getattr(self, "_restore_creation_from_session_state", None)
if callable(restore):
    restore()
self._force_creation_active_if_reconcile_needed()
```

**Body:** replace `not status.get("characters")` with `not status.get("roster")` at L186.

### 5. Trim `process_turn` resume NAME clobber — L572–579

**Before:**

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

**After (minimal):**

- Drop L574–576 (redundant `_restore_history` + NAME clobber).
- If `not self.creation.active` after sync at L567, reconcile failed — optional defensive `self._force_creation_active_if_reconcile_needed()` once (should be no-op if sync prelude ran).
- Keep `_creation_turn` return unchanged.

---

## Task breakdown

### WS1 — Orchestrator reconcile (`app/gm/orchestrator.py`)

1. Add `_read_saved_engine_status`, `_effective_awaiting_for_reconcile`, `_force_creation_active_if_reconcile_needed`.
2. Extend `_sync_creation_from_status` prelude + `roster` guard.
3. Remove resume NAME clobber in `process_turn` (L575–576).
4. Do **not** change APP-016 write path, APP-015 clear, or `_restore_history` (018 scope).

### WS2 — Tests (`app/tests/test_reconcile_empty_roster_on_load.py`)

1. Reuse fixtures from `test_engine_status_on_save.py`: `save_path`, `headless_app`, `read_save`.
2. Add `_patch_session_state_path(orchestrator, save_path)` (pattern from `test_creation_block_on_new_game.py:11-12`).
3. Add `_write_session_state(save_path, **overrides)` helper for disk fixtures.
4. Add `_patch_live_status(monkeypatch, orchestrator, *, awaiting, roster, characters=None)` for T-017b/f when live engine shape must be simulated without full DB setup.
5. Implement T-017a–f, T-017c2 as parametrized or named tests (see § Tests).

---

## Files (must ⊆ ticket Expected files)

| Path | Change |
|------|--------|
| `app/gm/orchestrator.py` | Helpers + `_sync_creation_from_status` + `process_turn` resume trim |
| `app/tests/test_reconcile_empty_roster_on_load.py` | **New** — T-017a–f, T-017c2 |

**Out of scope (batch / close):**

| Path | Owner |
|------|-------|
| `app/ui/app.py` | Reconcile inside orchestrator — no caller edit |
| `tmp/app-session-persistence-spec.md` | Changelog on ticket close |
| `app/gm/creation.py` | APP-018 |

---

## Tests

### Module: `app/tests/test_reconcile_empty_roster_on_load.py`

**Hygiene:** monkeypatch `orchestrator._session_state_path` → `tmp_path/session_state.json`; monkeypatch `ui.app.SAVE_PATH` when using `headless_app._load_session`. Never write dev `app/session_state.json`.

| ID | Test function (proposed) | Setup | Assert |
|----|--------------------------|-------|--------|
| **T-017a** | `test_t017a_force_active_when_inactive_and_disk_mid_creation` | `new game` + name; `_save_session`; `orchestrator.creation.active = False`; disk has `engine_status` | `_sync_creation_from_status()` → `creation.active is True` |
| **T-017b** | `test_t017b_force_active_from_disk_when_live_setup` | Fresh orch (live `SETUP`); disk: `creation_state: null`, `engine_status: {awaiting: CHARACTER_CREATION, roster: []}`; `import_creation_state(None)` | `_sync_creation_from_status()` → `creation.active is True`; `creation.step` unchanged (not forced NAME) |
| **T-017c** | `test_t017c_post_finalize_non_empty_roster_no_reactivate` | Full creation INPUTS + `_save_session`; `creation.active = False` | `_sync_creation_from_status()` → `creation.active is False` |
| **T-017c2** | `test_t017c2_live_empty_roster_wins_over_stale_saved_roster` | Patch live: `CHARACTER_CREATION`, `roster: []`; disk `engine_status.roster: [{display_name: "Ghost"}]` | `_sync_creation_from_status()` → `creation.active is True` |
| **T-017d** | `test_t017d_legacy_without_engine_status_unchanged` | Copy legacy fixture from `test_engine_status_on_save.py:90-118`; `pre_active = orchestrator.creation.active`; `_load_session()` | `creation.active == pre_active`; no exception (T4c baseline) |
| **T-017e** | `test_t017e_suggestions_nonempty_after_reconcile` | Mid-creation at `EQUIPMENT_GOLD`: set `creation.active=False`, disk + live `CHARACTER_CREATION`; reconcile | `get_player_suggestions()` == `["Yes, confirm", "I need different gear"]` |
| **T-017f** | `test_t017f_roster_setup_orphan_rows_no_force_active` | Patch live: `awaiting: ROSTER_SETUP`, `roster: []`, `characters: [{id: "x"}]`; `creation.active=False` | `_sync_creation_from_status()` → `creation.active is False` |

### Commands

| Step | Command | Expected |
|------|---------|----------|
| New module | `cd app && python -m pytest tests/test_reconcile_empty_roster_on_load.py -q` | T-017a–f, T-017c2 green |
| Filter (spec) | `cd app && python -m pytest tests -q -k "reconcile or empty_roster or app_017"` | All APP-017 tests green |
| Adjacent regression | `cd app && python -m pytest tests -q -k "engine_status or load_session or inactive_creation or session_resume"` | No regressions (T4c, APP-071, APP-065) |
| Full app suite (optional gate) | `cd app && python -m pytest tests -q` | Green |

---

## Acceptance criteria mapping

| Ticket AC / Spec | Implementation | Test |
|------------------|----------------|------|
| R1: inactive + empty roster + `CHARACTER_CREATION` → force active | `_force_creation_active_if_reconcile_needed` | T-017a, T-017b |
| R1: non-empty live roster → no reactivate | early return in force helper + sync C2 | T-017c |
| R1: non–`CHARACTER_CREATION` awaiting → no-op | effective awaiting gate | T-017f |
| R2: live roster wins over stale saved | roster from live only | T-017c2 |
| R2: absent/null `engine_status` | `_read_saved_engine_status` → None | T-017d |
| R3: `roster` not `characters` | sync C3 + ROSTER_SETUP guard | T-017f |
| R4: no NAME step clobber | remove L575–576; force helper sets active only | T-017b |
| R5: orchestrator-only disk read | `_session_state_path` | all disk tests |
| Chips after reconcile | sync called before suggestions | T-017e |

---

## Rollback / flags

- Revert helpers and restore L186 `characters` guard — behavior returns to pre-017 (chips bug returns).
- No feature flag; reconcile is idempotent and gated on `CHARACTER_CREATION`.

---

## Open questions

1. **APP-018 hook timing** — If 018 lands in same batch, implementer adds `_restore_creation_from_session_state` on `Orchestrator`; prelude `getattr` call requires no APP-017 rework. Coordinate so 018 does not duplicate force-active logic.
2. **T-017d vs import+sync** — Legacy path intentionally leaves `creation.active == False` after load when live is `SETUP`; do not “fix” in 017 (T4c contract).
3. **`_restore_history` hardcoded path** (L126) — inconsistent with `_session_state_path()`; out of scope unless 018 touches it.
4. **`_is_mid_creation_resume_failure`** (L331–357) — does not read `engine_status`; APP-071 variant B may miss disk-only mid-creation until after `_load_session` reconcile — acceptable; optional follow-up ticket.

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Dev plan — helpers, sync prelude, test matrix T-017a–f |
