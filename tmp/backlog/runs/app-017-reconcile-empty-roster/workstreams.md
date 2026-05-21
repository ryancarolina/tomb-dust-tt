# Workstreams: APP-017-reconcile-empty-roster

**backlog_ticket:** APP-017  
**plan:** [plan.md](plan.md) · **spec:** [spec.md](spec.md) · **domain spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md) § Reconcile empty roster on load (APP-017)

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Orchestrator reconcile helpers + sync | — | `app/gm/orchestrator.py` | Helpers + sync prelude + `roster` guard + resume NAME trim; import smoke OK |
| WS2 | Reconcile-on-load tests (T-017a–f, T-017c2) | WS1 | `app/tests/test_reconcile_empty_roster_on_load.py` | `pytest tests/test_reconcile_empty_roster_on_load.py -q` exit 0; filtered regression gates green |

**Stream count:** 2 — WS1 unblocks WS2; no parallel impl between streams.

**Out of workstreams (ticket release):** `tmp/app-session-persistence-spec.md` changelog + AC checkboxes + `claim_ticket.py release APP-017 --done` (plan: domain spec sync on close only).

**Batch coordination (not WS deps):** [batch-board-APP-017-APP-018-APP-019.md](../batch-board-APP-017-APP-018-APP-019.md) — land **APP-018** restore hook before or with APP-017 so prelude `getattr(self, "_restore_creation_from_session_state", None)` is not duplicated with conflicting force-active logic. APP-017 force helper sets **`creation.active` only** (no `step=NAME`); APP-018 owns step/field restore.

---

## WS1 — Orchestrator reconcile

**Scope:** Plan § WS1 — disk-aware reconcile in `app/gm/orchestrator.py`: three private helpers after `_session_state_path()` (~L313), prelude on `_sync_creation_from_status()`, `characters` → **`roster`** in sync body, remove `process_turn` resume NAME clobber (L575–576).

**Requirements covered:** spec R1–R5; ticket AC; plan flows A–D, C0–C4.

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | `_read_saved_engine_status(self) -> dict \| None` | `orchestrator.py` after `_session_state_path()` | § New helpers #1 |
| 2 | `_effective_awaiting_for_reconcile(self, live_status: dict) -> str` | same | § #2 |
| 3 | `_force_creation_active_if_reconcile_needed(self) -> None` | same | § #3 |
| 4 | Extend `_sync_creation_from_status` prelude + body | same L177–191 area | § #4, Flow C |
| 5 | Trim `process_turn` resume branch | same L572–579 | § #5, R4 |

### Task 1 — `_read_saved_engine_status`

- Path: `self._session_state_path()` (not hardcoded path in `_restore_history` L126).
- Parse JSON; return `data["engine_status"]` only if value is a `dict`.
- Missing file, parse error, absent key, or `null` → `None` (S5d / T-017d — no error).

### Task 2 — `_effective_awaiting_for_reconcile`

```python
live_awaiting = live_status.get("awaiting") or ""
if live_awaiting and live_awaiting != "SETUP":
    return live_awaiting
saved = self._read_saved_engine_status()
if saved:
    return saved.get("awaiting") or live_awaiting
return live_awaiting
```

- Live non-`SETUP` wins; cold engine (`SETUP`) falls back to saved snapshot (T-017b).
- **Roster for empty check:** always `live_status.get("roster") or []` — never saved roster (R2 / T-017c2).

### Task 3 — `_force_creation_active_if_reconcile_needed`

Idempotent; safe to call multiple times per load (R1).

| Gate | Action |
|------|--------|
| `self.creation.active` already true | return |
| `bridge.status()` raises | return |
| non-empty live `roster` | return (T-017c) |
| live `awaiting == "ROSTER_SETUP"` | return (T-017f / R3) |
| `_effective_awaiting_for_reconcile(live) != "CHARACTER_CREATION"` | return |
| else | `self.creation.active = True` only — **do not** set `step=NAME` (R4 / APP-018) |

### Task 4 — `_sync_creation_from_status` prelude + body

**Prelude (merge order):**

```python
restore = getattr(self, "_restore_creation_from_session_state", None)
if callable(restore):
    restore()
self._force_creation_active_if_reconcile_needed()
```

**Body:** keep C2/C4 logic; replace L186 `not status.get("characters")` with `not status.get("roster")` (R3). C3: `WORLD_INTRO` → `NAME` only when activating mid-creation (unchanged semantics, roster guard).

### Task 5 — `process_turn` resume trim (L572–579)

**Remove:** redundant `_restore_history()` + `CreationState(active=True, step="NAME")` at L574–576.

**Keep:** `_creation_turn` return when `awaiting == CHARACTER_CREATION` and empty live `roster`.

**Optional defensive:** if `not self.creation.active` after sync at L567, call `_force_creation_active_if_reconcile_needed()` once (no-op if A3 prelude already ran).

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Orchestrator-only disk read | Use `_session_state_path()`; **no** `app/ui/app.py` edits (R5) |
| APP-016 / APP-015 unchanged | Do not change `_save_session` write path or new-game `engine_status` clear |
| `_restore_history` | Out of scope (L126 hardcoded path) unless APP-018 touches it |
| APP-018 hook | Prelude `getattr` only — no-op until 018 lands; 018 must not duplicate force-active |
| R4 boundary | Force helper sets `active` only; remove resume NAME clobber; sync `WORLD_INTRO→NAME` is only allowed path for step bump |
| Live roster wins | Empty check and force gate use **live** `roster` only (T-017c2) |
| `ROSTER_SETUP` | Explicit no-op in force helper (orphan `characters` rows) |

### Test gates (WS1 done when)

WS1 has no dedicated test file; verify by code review + WS2.

```bash
cd app && python -c "from gm.orchestrator import Orchestrator; print('import ok')"
```

**Expected:** import succeeds; edits only in `app/gm/orchestrator.py`.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-017
ticket: tmp/backlog/app-017-reconcile-empty-roster-on-load.md
run-folder: tmp/backlog/runs/app-017-reconcile-empty-roster/
spec: spec.md | plan: plan.md § WS1, New helpers, Flow C, process_turn trim | domain spec: tmp/app-session-persistence-spec.md § APP-017 (read only)
workstreams: workstreams.md § WS1

Implement WS1 only — orchestrator reconcile helpers + _sync_creation_from_status prelude/body + process_turn resume trim.
Place helpers after _session_state_path(); roster not characters; force-active sets active only; APP-018 getattr hook in prelude.
Do not edit app/ui/app.py, creation.py, or APP-016/015 paths.
AGENTS.md: claim/focus APP-017 if not active; stay within Expected files.
Write reflection-dev-impl-ws1.md before return.
```

---

## WS2 — Reconcile-on-load tests (T-017a–f, T-017c2)

**Scope:** Plan § WS2 — new module `app/tests/test_reconcile_empty_roster_on_load.py` covering disk + live desync, legacy baseline, suggestions regression, and `ROSTER_SETUP` no-op.

**Depends on:** WS1 — tests call `_sync_creation_from_status()`, `_force_creation_active_if_reconcile_needed()`, and/or `_load_session()` against behavior WS1 implements.

**Requirements covered:** spec test plan T-017a–f / T-017c2; plan § Tests; ticket Expected files.

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | New module + docstring | Never write dev `app/session_state.json` | § Tests hygiene |
| 2 | Fixtures/helpers | `save_path`, `headless_app`, `read_save` (reuse pattern from `test_engine_status_on_save.py`); `_patch_session_state_path(orchestrator, save_path)` (pattern `test_creation_block_on_new_game.py:11-12`); `_write_session_state(save_path, **overrides)`; `_patch_live_status(monkeypatch, orchestrator, *, awaiting, roster, characters=None)` | WS2 items 2–4 |
| 3 | **T-017a** `test_t017a_force_active_when_inactive_and_disk_mid_creation` | `new game` + name; `_save_session`; `creation.active = False`; disk has `engine_status`; `_sync_creation_from_status()` → `creation.active is True` | T-017a |
| 4 | **T-017b** `test_t017b_force_active_from_disk_when_live_setup` | Fresh orch, live `SETUP`; disk `creation_state: null`, `engine_status: {awaiting: CHARACTER_CREATION, roster: []}`; `import_creation_state(None)`; sync → active true; **step not forced to NAME** (default `NAME` ok; assert not clobbered from later step if seeded) | T-017b |
| 5 | **T-017c** `test_t017c_post_finalize_non_empty_roster_no_reactivate` | Full creation INPUTS + `_save_session`; monkeypatch `roll_attributes` like T4b; `creation.active = False`; sync → stays false | T-017c |
| 6 | **T-017c2** `test_t017c2_live_empty_roster_wins_over_stale_saved_roster` | Patch live: `CHARACTER_CREATION`, `roster: []`; disk `engine_status.roster: [{display_name: "Ghost"}]`; sync → active true | T-017c2 |
| 7 | **T-017d** `test_t017d_legacy_without_engine_status_unchanged` | Copy legacy fixture from `test_engine_status_on_save.py:90-118`; record `pre_active`; `_load_session()` → `creation.active == pre_active`; no exception | T-017d / T4c |
| 8 | **T-017e** `test_t017e_suggestions_nonempty_after_reconcile` | Mid-creation `EQUIPMENT_GOLD`; `creation.active=False`; disk + live `CHARACTER_CREATION`; reconcile; `get_player_suggestions()` == `["Yes, confirm", "I need different gear"]` | T-017e |
| 9 | **T-017f** `test_t017f_roster_setup_orphan_rows_no_force_active` | Patch live: `ROSTER_SETUP`, `roster: []`, `characters: [{id: "x"}]`; `creation.active=False`; sync → stays false | T-017f |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Isolation | `monkeypatch.setattr("ui.app.SAVE_PATH", tmp_path / "session_state.json")` and `orchestrator._session_state_path` → same tmp file |
| Headless pygame | `SDL_VIDEODRIVER=dummy` before `pygame.init()` when using `headless_app` |
| T-017c rolls | Import/copy `FIXED_ROLL` + INPUTS from `test_creation_flow.py` / T4b pattern — avoid flaky rolls |
| T-017b/f mocking | Prefer `monkeypatch` on `orchestrator.bridge.status` via `_patch_live_status`; verify patch suffices before SQLite orphan seeding |
| T-017d | Intentionally leaves `creation.active == False` when live is `SETUP` without saved mid-creation — do not “fix” (T4c contract) |
| T-017e chips | Match `app/ui/suggestions.py` desk strings; use `orchestrator.get_player_suggestions()` |
| Out of scope | No production edits outside test module; domain spec is release-only |

### Test gates (WS2 done when all pass)

```bash
cd app && python -m pytest tests/test_reconcile_empty_roster_on_load.py -q
cd app && python -m pytest tests -q -k "reconcile or empty_roster or app_017"
cd app && python -m pytest tests -q -k "engine_status or load_session or inactive_creation or session_resume"
```

**Expected:** T-017a–f and T-017c2 green; adjacent APP-016/065/071 filters pass.

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-017
ticket: tmp/backlog/app-017-reconcile-empty-roster-on-load.md
run-folder: tmp/backlog/runs/app-017-reconcile-empty-roster/
spec: spec.md § Test plan | plan: plan.md § WS2, Tests table | domain spec: tmp/app-session-persistence-spec.md § T-017a–f (read only)
workstreams: workstreams.md § WS2

Prerequisite: WS1 present in branch (orchestrator reconcile helpers + sync prelude).
Implement WS2 only — test_reconcile_empty_roster_on_load.py with T-017a–f and T-017c2 per plan.
Reuse save_path/headless_app patterns from test_engine_status_on_save.py; patch _session_state_path to tmp_path.
Run: cd app && python -m pytest tests/test_reconcile_empty_roster_on_load.py -q
Write reflection-dev-impl-ws2.md before return.
```

---

## AC mapping (quick reference)

| AC / spec | WS | Test |
|-----------|-----|------|
| R1: inactive + empty roster + `CHARACTER_CREATION` → force active | WS1 | T-017a, T-017b |
| R1: non-empty live roster → no reactivate | WS1 | T-017c |
| R1: non–`CHARACTER_CREATION` → no-op | WS1 | T-017f |
| R2: live roster wins over stale saved | WS1 | T-017c2 |
| R2: absent/null `engine_status` | WS1 | T-017d |
| R3: `roster` not `characters` + `ROSTER_SETUP` guard | WS1 | T-017f |
| R4: no NAME step clobber on resume | WS1 | T-017b |
| R5: orchestrator-only disk read | WS1 | all disk tests |
| Chips after reconcile | WS1 + WS2 | T-017e |
| Reconcile without successful resume | WS1 (sync prelude from `_load_session`) | T-017a, T-017b |
