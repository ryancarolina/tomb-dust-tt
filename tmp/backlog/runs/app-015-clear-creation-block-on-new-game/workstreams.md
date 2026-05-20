# Workstreams: APP-015-clear-creation-block-on-new-game

**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**domain_spec:** tmp/app-session-persistence-spec.md (§ New game — creation block clear, T-015a–d)

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Orchestrator helpers + C1–C2 prepend | — | `app/gm/orchestrator.py` | `_reset_creation_for_new_game` + `_clear_creation_block_on_disk` at `setup_new_game` entry; `engine_status` popped on disk R-M-W; existing `setup_new_game` callers unchanged except ordering |
| WS2 | T-015a–d tests | WS1 | `app/tests/test_creation_block_on_new_game.py`, `app/tests/conftest.py` (optional) | `pytest app/tests/test_creation_block_on_new_game.py -q` green; regression `-k` filters green |

**Stream count:** 2 — WS1 is the required fix (~60–90 LOC); WS2 locks domain tests T-015a–d and recovery probe (T-015c).

**Out of workstreams (ticket release):** `tmp/app-session-persistence-spec.md` changelog; `python tmp/backlog/claim_ticket.py release APP-015 --done`; manual Stage 7 playtest (plan § Tests step 4).

**Explicitly not in any stream:** `app/ui/app.py`, `app/gm/bridge.py`, `play/tomb_gm/**`, domain spec body edits during impl (changelog on close only).

**APP-014 merge note:** When APP-014 lands in the same function, final `setup_new_game` order is **C1 → C2 → L1 → L1b → L2 → … → L7**. WS1 prepends C1–C2 at the **first line** of the function body regardless of whether L1 exists yet.

---

## WS1 — Orchestrator helpers + ordering

**Scope:** Plan § WS1 — `_session_state_path`, `_reset_creation_for_new_game`, `_clear_creation_block_on_disk`; prepend C1–C2 at `setup_new_game` entry; optional unify disk path in `_is_mid_creation_resume_failure` / `_delete_save_file`.

**Requirements covered:** domain C1 (memory NAME before engine), C2 (surgical disk `creation_state` + remove `engine_status`), C3 (all exit paths via entry prepend), C4 batch boundary (clear stale snapshot; APP-016 owns write-on-save).

### Implementation order (within stream)

| # | Task | File:area | Plan ref |
|---|------|-----------|----------|
| 1 | Add `_session_state_path() -> Path` (or module `SESSION_STATE_PATH`) | `orchestrator.py` | WS1 §1 |
| 2 | Add `_reset_creation_for_new_game()` — `CreationState(active=True, step="NAME")` | `orchestrator.py` | WS1 §2 |
| 3 | Add `_clear_creation_block_on_disk()` — R-M-W save; set `creation_state` from `export_creation_state()`; `data.pop("engine_status", None)`; preserve other keys; swallow IO/JSON errors | `orchestrator.py` | WS1 §3 |
| 4 | Prepend to `setup_new_game` (first statements in body): `_reset_creation_for_new_game()` then `_clear_creation_block_on_disk()` | `orchestrator.py` ~L348+ | WS1 §4 |
| 5 | Keep L6 idempotent memory reset + `history.clear()` on success path | `orchestrator.py` | WS1 §5 |
| 6 | Keep `_delete_save_file()` on success (L7) | `orchestrator.py` | WS1 §6 |
| 7 | (Optional) Point `_is_mid_creation_resume_failure` disk probe and `_delete_save_file` at `_session_state_path()` | `orchestrator.py` ~L294–321, ~L394 | WS1 §7 |

### `_clear_creation_block_on_disk` behavior (plan § WS1.3)

| Case | Action |
|------|--------|
| Save file exists | `json.loads` → `data["creation_state"] = export` → `data.pop("engine_status", None)` → write `indent=2` |
| Save file missing | No-op (C3 via memory only) |
| JSON/IO error | Swallow — do not block `new game` (match `_delete_save_file` tolerance) |
| Other keys | **Do not** strip `narration_lines`, `input_history`, etc. |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Call order | `_reset_creation_for_new_game()` **before** `_clear_creation_block_on_disk()` so disk export is NAME-fresh |
| Entry point | C1–C2 run **before** any bridge/engine call (`wipe_all_data`, APP-014 `end_session`, etc.) |
| `engine_status` | Must be **absent** or **null** after C2 — never leave pre-wipe snapshot beside fresh NAME `creation_state` (PLAN-001 / T-015d) |
| Callers | Trace E — `process_turn("new game")`, `_handle_player_death`, resume `run_ended` all use same `setup_new_game`; no duplicate lifecycle |
| Autosave window | C1 at entry closes Trace D risk (autosave mid-setup) |
| Failure path | Trace G — `campaign_new` / `session_start` early return still leaves memory + disk NAME-fresh |
| Out of scope | UI-only clear, `bridge.py` lifecycle (APP-014), APP-016 snapshot **write** on `_save_session` |

### Test gates (WS1 done when)

WS1 has **no dedicated test file** until WS2; smoke after WS1:

```bash
python -c "from gm.orchestrator import Orchestrator; print('import ok')"
```

Full gates run in WS2.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-015
ticket: tmp/backlog/app-015-clear-creation-block-on-new-game.md
run-folder: tmp/backlog/runs/app-015-clear-creation-block-on-new-game/
spec: spec.md | plan: plan.md § WS1 | domain: tmp/app-session-persistence-spec.md (§ New game — creation block clear)
workstreams: workstreams.md § WS1

Implement WS1 only — orchestrator helpers + prepend C1–C2 at setup_new_game entry per plan Traces F–G.
AGENTS.md: claim APP-015 before app/ edits; only app/gm/orchestrator.py.
Do not edit app/ui/app.py, bridge.py, play/tomb_gm.
Preserve L6/L7 success-path behavior; optional unify _session_state_path in _delete_save_file / _is_mid_creation_resume_failure.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Tests (T-015a–d)

**Scope:** Plan § WS2 — new `test_creation_block_on_new_game.py`; fixtures; T-015a–d; regression `-k` filters.

**Depends on:** WS1 — tests call `setup_new_game()` / `process_turn("new game")` and assert C1–C2 effects.

**Requirements covered:** domain T-015a–d; ticket AC (explicit disk clear, all exit paths, recovery probe, stale `engine_status`).

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | Add `session_state_file(tmp_path, monkeypatch)` | Monkeypatch `orchestrator._session_state_path` to tmp `session_state.json` | WS2 fixtures |
| 2 | Add `seed_stale_creation(save_path, *, with_engine_status=True)` | SKILLS block + optional `engine_status.awaiting` / `roster` | WS2 fixtures |
| 3 | **T-015a** | Stale file + `setup_new_game()` success → disk NAME, keys preserved, memory NAME | WS2 table |
| 4 | **T-015b** | Mock `campaign_new` failure → disk + **memory** NAME (`creation.name == ""`) | WS2 table, QA T-015b |
| 5 | **T-015c** | After setup, `process_turn("load game")` → variant B/A must not cite SKILLS / old name from pre-wipe disk | Trace H |
| 6 | **T-015d** | Stale `engine_status` + `creation_state` → after `setup_new_game` (success or early return after C1–C2) → `engine_status` absent/null; `narration_lines` preserved | PLAN-002 |
| 7 | (Optional) Shared fixture in `conftest.py` | Only if reused; else keep helpers in test module | WS2 |
| 8 | Regression | `-k "creation_block or new_game_creation"` and `-k "creation_flow or session_resume"` | plan § Tests |

### Test matrix (domain IDs)

| ID | Setup | Action | Assert |
|----|-------|--------|--------|
| T-015a | Stale SKILLS + name on disk | `setup_new_game()` success (isolated bridge or mock) | `step == "NAME"`, `name == ""`, `roll_result == {}`; narration/history preserved; memory NAME |
| T-015b | Stale file | Mock `campaign_new` → `{ok: false}` | Early return; disk NAME; `orchestrator.creation.step == "NAME"`, `name == ""` |
| T-015c | Post T-015a state | `process_turn("load game")`, no engine save | No SKILLS/old name in copy; NAME footer / `[Awaiting: NAME_INPUT]` |
| T-015d | Stale file + mismatched `engine_status` | `setup_new_game()` success **or** fail after C1–C2 | `engine_status` absent or null; `creation_state.step == "NAME"`; non-creation keys preserved |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Isolation | Never write dev `app/session_state.json`; tmp path only |
| Monkeypatch | Path helper must match WS1 `_session_state_path()` name |
| T-015d timing | Assert after prepend even on engine failure (mock failure **after** C1–C2 if needed) |
| Collection imports | Follow APP-049 — no module-level `Orchestrator` import in test module |
| WS2 only | Do not re-open orchestrator except WS1 bugfix |

### Test gates (WS2 done when)

```bash
python -m pytest app/tests/test_creation_block_on_new_game.py -q
python -m pytest app/tests -q -k "creation_block or new_game_creation"
python -m pytest app/tests -q -k "creation_flow or session_resume"
```

### Post-impl (not WS2 — ticket release)

- `tmp/app-session-persistence-spec.md` changelog: APP-015 C1–C2 at `setup_new_game` entry
- Mark ticket AC done; `release APP-015 --done`
- Manual Stage 7: mid-creation SKILLS → `new game` → inspect save (plan § Tests step 4)

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-015
ticket: tmp/backlog/app-015-clear-creation-block-on-new-game.md
run-folder: tmp/backlog/runs/app-015-clear-creation-block-on-new-game/
spec: spec.md | plan: plan.md § WS2, Traces H | domain: tmp/app-session-persistence-spec.md (§ Tests APP-015)
workstreams: workstreams.md § WS2

Prerequisite: WS1 merged — C1–C2 at setup_new_game entry in orchestrator.py.
Implement WS2 only — test_creation_block_on_new_game.py T-015a–d; tmp-path fixtures; optional conftest.py.
AGENTS.md: claim APP-015 if not active; stay within app/tests/.
Run: pytest commands in workstreams.md § WS2 Test gates.
Write reflection-dev-impl-WS2.md before return.
```
