# Workstreams: APP-018-continue-creation-state

**backlog_ticket:** APP-018  
**ticket_path:** tmp/backlog/app-018-continue-restores-creation-state.md  
**domain_spec:** tmp/app-session-persistence-spec.md (§ Creation restore on continue / relaunch, APP-018)

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Restore helper + G1 gate + G3 wiring | — | `app/gm/orchestrator.py` | `_restore_creation_from_session_state`, `_creation_restore_gate`, once-only flag, G3a–c wired; NAME clobber removed; creation import stripped from `_restore_history`; import smoke green |
| WS2 | T-018a–f tests | WS1 | `app/tests/test_creation_restore.py`, `app/tests/test_session_resume_failure.py` (optional) | `pytest app/tests/test_creation_restore.py -q` green; regression `-k` filters green |

**Stream count:** 2 — WS1 is the required fix (~80–120 LOC); WS2 locks domain tests T-018a–f and APP-071 non-regression.

**Out of workstreams (ticket release):** `tmp/app-session-persistence-spec.md` changelog; `python tmp/backlog/claim_ticket.py release APP-018 --done`; manual Stage 7 playtest ([human-test-plan.md](human-test-plan.md)).

**Explicitly not in any stream:** `app/ui/app.py`, `app/gm/bridge.py`, APP-064 boot chips, APP-017 force-active reconcile (017 consumes helper when batched), `find_save_campaign`.

**APP-017 batch note:** Canonical merge order is restore (018) → force-active (017) → `_sync_creation_from_status`. WS1 G3c leaves inline force-active placeholder; 018 tests must pass without 017 landed.

---

## WS1 — Restore helper + G1 gate + G3 wiring

**Scope:** Plan § G1 gate, § Restore helper, § Once-only relaunch guard, § Call sites G3a–c; refactor `_restore_history`; remove NAME clobber (~573–576).

**Requirements covered:** spec R1–R6; domain G1–G3; ticket AC (restore when `awaiting == CHARACTER_CREATION`).

### Implementation order (within stream)

| # | Task | File:area | Plan ref |
|---|------|-----------|----------|
| 1 | Add `self._creation_disk_restore_done: bool = False` in `__init__` | `orchestrator.py` | W1.1 |
| 2 | Reset `_creation_disk_restore_done = False` in `setup_new_game` / `_reset_creation_for_new_game` entry | `orchestrator.py` | W1.1, § Once-only guard |
| 3 | Implement `_creation_restore_gate(data, live_status) -> bool` — pure G1 evaluation | `orchestrator.py` near `_session_state_path` | § G1 gate |
| 4 | Implement `_restore_creation_from_session_state() -> bool` — load once, gate, `import_creation_state`, set flag | `orchestrator.py` | § Restore helper |
| 5 | Strip `creation_state` import from `_restore_history` (narration + combat only) | `orchestrator.py` ~L123–137 | W1.3 |
| 6 | **G3a** — after `new game`/`start`/`new` early return, before resume branch: call helper when `lower not in ("new game", "start", "new")` | `orchestrator.py` ~L535–540 | § G3a |
| 7 | **G3b** — resume fail path: call helper before `_resume_failure_message` | `orchestrator.py` resume branch | § G3b |
| 8 | **G3c** — resume success: `_restore_history()` then helper then `_sync_creation_from_status()`; delete NAME clobber; keep WORLD_INTRO→NAME via sync only | `orchestrator.py` ~L566–579 | § G3c |
| 9 | Remove duplicate inner `_restore_history()` and `CreationState(active=True, step="NAME")` block | `orchestrator.py` | § G3c, Root cause table |

### G1 gate — `_creation_restore_gate(data, live_status) -> bool`

| # | Rule | Implementation |
|---|------|----------------|
| **G1d** | Live roster non-empty → **no restore** | `if live_status.get("roster"): return False` |
| **G1a** | `awaiting == CHARACTER_CREATION` | If `engine_status` key present and `engine_status.get("awaiting")` is not `None`: use **saved** `awaiting` only — must equal `"CHARACTER_CREATION"`. Else (legacy): require **live** `awaiting == "CHARACTER_CREATION"`. **Stale rule:** saved `awaiting != CHARACTER_CREATION` → **no restore** even if live matches. |
| **G1c** | Empty roster | If snapshot has `engine_status.roster`: require `== []`. Else rely on G1d for live roster. |
| **G1b** | Active creation block | `creation_state` exists and `creation_state.get("active") is True` |

**Invalid step:** If `step` missing or not in `CREATION_STEPS` after import path evaluation — treat as no restore; do not fabricate NAME except via existing `_sync_creation_from_status` `WORLD_INTRO` → `NAME`.

Return `False` on missing file, parse error, or any failed row.

### Restore helper — `_restore_creation_from_session_state() -> bool`

| Step | Action |
|------|--------|
| 1 | If `self._creation_disk_restore_done`: return `False` |
| 2 | `save_path = self._session_state_path()`; if not exists → `False` |
| 3 | `data = json.loads(...)`; `live = self.bridge.status()` (try/except → `{}`) |
| 4 | If not `_creation_restore_gate(data, live)`: return `False` |
| 5 | `import_creation_state(data.get("creation_state"))`; assert `self.creation.active` |
| 6 | Set `self._creation_disk_restore_done = True`; return `True` |

**Does not** call `_sync_creation_from_status` — callers run sync **after** restore per merge order.

### G3c success-path shape (post-018; APP-017 batch placeholder)

```python
self._restore_history()
self._restore_creation_from_session_state()
self._sync_creation_from_status()
self._sync_combat_from_status()
status = self.bridge.status()
if status.get("awaiting") == "CHARACTER_CREATION" and not status.get("roster"):
    if not self.creation.active:
        self.creation.active = True
        if self.creation.step == "WORLD_INTRO":
            self.creation.step = "NAME"
    return self._creation_turn("[SYSTEM: Resume character creation. ...]")
```

When APP-017 lands in same batch, replace inline force-active with `_reconcile_empty_roster_on_load()` that calls helper first — 018 does **not** implement 017 unless batching.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Once-only guard | After successful restore, later turns must **not** re-read disk over in-memory FSM progress (race pick, second `continue`) |
| `new game` reset | `setup_new_game` / `_reset_creation_for_new_game` clears flag so APP-015 wipe can restore NAME on next load |
| No double import | Creation import **only** via helper — removed from `_restore_history` |
| Saved `awaiting` precedence | When `engine_status.awaiting` present and non-null, G1 uses saved value only (T-018b: live `SETUP` + saved `CHARACTER_CREATION`) |
| Stale snapshot | Saved `awaiting != CHARACTER_CREATION` → no restore even if live matches (post–`new game` / APP-015) |
| NAME clobber | **Delete** `CreationState(active=True, step="NAME")` block — never reset imported step to NAME |
| Sync order | G3c: restore **before** `_sync_creation_from_status` and **before** any APP-017 force-active |
| Out of scope | `ui/app.py`, APP-064 boot, duplicate disk read for APP-017 |

### Test gates (WS1 done when)

WS1 has **no dedicated test file** until WS2; smoke after WS1:

```bash
python -c "from gm.orchestrator import Orchestrator; print('import ok')"
```

Full gates run in WS2.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-018
ticket: tmp/backlog/app-018-continue-restores-creation-state.md
run-folder: tmp/backlog/runs/app-018-continue-creation-state/
spec: spec.md | plan: plan.md § G1, Restore helper, G3a–c | domain: tmp/app-session-persistence-spec.md (§ Creation restore APP-018)
workstreams: workstreams.md § WS1

Implement WS1 only — _creation_restore_gate, _restore_creation_from_session_state, once-only flag, G3a–c wiring, trim _restore_history, remove NAME clobber per plan.
AGENTS.md: claim APP-018 before app/ edits; only app/gm/orchestrator.py.
Do not edit app/ui/app.py, bridge.py, play/tomb_gm.
Reset _creation_disk_restore_done in setup_new_game / _reset_creation_for_new_game.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — T-018a–f tests

**Scope:** Plan § WS2, § Test plan T-018a–f — new `test_creation_restore.py`; optional variant B tweak in `test_session_resume_failure.py`.

**Depends on:** WS1 — tests assert helper + G3 call-site behavior.

**Requirements covered:** domain T-018a–f; ticket AC; APP-071 variant A/B non-regression; APP-015 post–`new game` (T-018f).

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | Add `seed_session_state(tmp_path, monkeypatch)` fixture | Patch `Orchestrator._session_state_path` → `tmp_path / "session_state.json"` | § Test plan fixture |
| 2 | **T-018a** | Seed RACE + `CHARACTER_CREATION`; `session_resume` → `ok: false`; `process_turn("continue")` → `step == "RACE"`; variant B mentions race; footer `[Awaiting: RACE_INPUT]` | Test table |
| 3 | **T-018b** | Same seed; live `awaiting=SETUP`; `process_turn("Dwarf")` → G3a restores; `creation.active`, `step == "RACE"` (spy `_creation_turn` if needed) | Test table |
| 4 | **T-018c** | Seed RACE; resume success; `process_turn("load game")` → `step == "RACE"` not NAME | Test table |
| 5 | **T-018d** | Seed without `engine_status`; live `CHARACTER_CREATION`; step SKILLS; continue fail → `step == "SKILLS"` | Test table |
| 6 | **T-018e** | Seed post-finalize (`roster` non-empty or `awaiting=PLAYER_ACTIONS`); continue → no stale import | Test table |
| 7 | **T-018f** | Seed SKILLS + `CHARACTER_CREATION`; `setup_new_game()`; continue/desk input → no restore to SKILLS; NAME flow | Test table |
| 8 | (Optional) Update `test_load_game_mid_creation_variant_b` comment/expectations if overlap | Prefer new module for disk seeds | W2.3 |

### Test matrix (domain IDs)

| ID | Setup | Action | Assert |
|----|-------|--------|--------|
| **T-018a** | `engine_status.awaiting=CHARACTER_CREATION`, `roster=[]`, `creation_state.active=true`, `step=RACE`, `name` set | `session_resume` → `ok: false`; `process_turn("continue")` | `creation.step == "RACE"`; variant B text contains `race`; footer `[Awaiting: RACE_INPUT]` |
| **T-018b** | Same seed; `bridge.status` → `awaiting=SETUP`, `roster=[]` | `process_turn("Dwarf")` | G3a restores; `creation.active`, step RACE |
| **T-018c** | Seed RACE; `session_resume` → `ok: true`; status → `CHARACTER_CREATION`, `roster=[]` | `process_turn("load game")` | `creation.step == "RACE"` (not NAME) |
| **T-018d** | Seed **without** `engine_status`; live `CHARACTER_CREATION`, empty roster; active `creation_state` step SKILLS | `process_turn("continue")` fail | `creation.step == "SKILLS"` |
| **T-018e** | Seed post-finalize: `engine_status.roster` non-empty **or** `awaiting=PLAYER_ACTIONS` | `process_turn("continue")` | Creation not imported; step unchanged from default inactive |
| **T-018f** | Seed SKILLS + `CHARACTER_CREATION`; run `setup_new_game()` | `process_turn("continue")` or desk input | No restore to SKILLS; disk NAME-only; `creation.step` in NAME flow |

**T-018b note:** Prefer asserting `creation.step == "RACE"` and `creation.active` immediately after first `process_turn` with spied `_creation_turn` — avoid full LLM stub chain unless necessary.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Isolation | Never write dev `app/session_state.json`; tmp path only via monkeypatch |
| Monkeypatch | Path helper must match WS1 `_session_state_path()` name |
| Collection imports | Follow APP-049 — no module-level `Orchestrator` import in test module |
| WS2 only | Do not re-open orchestrator except WS1 bugfix |
| APP-071 | Keep existing variant A/B tests green; extend variant B expectations only if disk seed changes behavior |

### Test gates (WS2 done when)

```bash
python -m pytest app/tests/test_creation_restore.py -q
python -m pytest app/tests/test_engine_status_on_save.py -q
python -m pytest app/tests/test_session_resume_failure.py -q
python -m pytest app/tests/test_creation_block_on_new_game.py -q
python -m pytest app/tests -q -k "creation_restore or continue_creation or app018"
```

### Post-impl (not WS2 — ticket release)

- `tmp/app-session-persistence-spec.md` changelog: APP-018 creation restore on continue/relaunch
- Mark ticket AC done; `release APP-018 --done`
- Manual Stage 7: RACE/SKILLS autosave → quit → relaunch → `continue` or desk input ([human-test-plan.md](human-test-plan.md))
- If APP-017 batched: run `test_reconcile_empty_roster_on_load.py` after merge order wired

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-018
ticket: tmp/backlog/app-018-continue-restores-creation-state.md
run-folder: tmp/backlog/runs/app-018-continue-creation-state/
spec: spec.md | plan: plan.md § Test plan T-018a–f | domain: tmp/app-session-persistence-spec.md (§ Tests APP-018)
workstreams: workstreams.md § WS2

Prerequisite: WS1 merged — helper, gate, G3a–c, NAME clobber removed in orchestrator.py.
Implement WS2 only — test_creation_restore.py T-018a–f; seed_session_state fixture; optional test_session_resume_failure.py tweak.
AGENTS.md: claim APP-018 if not active; stay within app/tests/.
Run: pytest commands in workstreams.md § WS2 Test gates.
Write reflection-dev-impl-WS2.md before return.
```

---

## AC mapping

| Requirement | Stream | Verification |
|-------------|--------|--------------|
| R1 shared restore helper + G1 gate | WS1 | T-018a–f gate matrix |
| R2 relaunch first turn (G3a) | WS1 | T-018b |
| R3 resume fail before variant B | WS1 | T-018a |
| R4 resume success; remove NAME clobber | WS1 | T-018c |
| R5 legacy no `engine_status` | WS1 | T-018d |
| R6 post-finalize no-op | WS1 | T-018e |
| APP-015 post–`new game` | WS1 | T-018f |
| Ticket AC: restore when `CHARACTER_CREATION` | WS1 + WS2 | T-018a–d |
| APP-071 variant A/B non-regression | WS2 | `test_session_resume_failure.py` |
| APP-017 batch merge | WS1 (placeholder) | 018 tests pass without 017 |
