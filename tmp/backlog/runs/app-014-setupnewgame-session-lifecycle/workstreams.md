# Workstreams: APP-014-setupnewgame-session-lifecycle

**backlog_ticket:** APP-014

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | setup_new_game L1/L1b lifecycle | — | `app/gm/orchestrator.py` | L1 `end_session` + L1b `force_close_all_sessions` prepend before `wipe_all_data`; docstring updated; callers unchanged unless WS2 proves gap |
| WS2 | Lifecycle pytest T-014a–c | WS1 | `app/tests/test_setup_new_game_lifecycle.py` | `python -m pytest app/tests/test_setup_new_game_lifecycle.py -q` exit 0; regression `-k "setup_new_game or session_lifecycle or creation_flow"` green |

**Stream count:** 2 — WS1 owns orchestrator ordering (plan §1); WS2 owns pytest AC (plan §2) and depends on WS1 behavior.

**Read-only (no stream):** `app/gm/bridge.py`, `app/ui/app.py`, `app/main.py` — trace/reference only per plan.

**Out of workstreams (ticket release):** `tmp/app-session-persistence-spec.md` checklist + changelog; `python tmp/backlog/claim_ticket.py release APP-014 --done`; optional ticket Expected-files line for test module (qa-plan-pass note).

---

## WS1 — setup_new_game L1/L1b lifecycle

**Scope:** Plan §1 — prepend graceful session end (L1) and `force_close_all_sessions` fallback (L1b) to `Orchestrator.setup_new_game` before existing L2–L7 body. Update docstring one line.

**Requirements covered:** spec L1, L2 (ordering fix only — L2–L7 body unchanged), L6 (hub method; callers already route here).

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | Prepend L1/L1b before wipe | `setup_new_game` ~348–361, **before** `self.bridge.wipe_all_data()` | §1, B1–B2 |
| 2 | Docstring | Same function | §1 — “end prior session before wipe” |
| 3 | Caller smoke (no edits unless gap) | `process_turn` ~495–500, `_handle_player_death` ~383, resume `run_ended` ~518 | §1 callers table |

### Task 1 — L1/L1b insert (plan §1)

**Insert immediately before** `self.bridge.wipe_all_data()`:

```python
end_result = self.bridge.end_session()
if not end_result.get("ok"):
    self.bridge.force_close_all_sessions()
```

**Leave unchanged after insert:** `wipe_all_data` → `init` → `campaign_new` (incl. `"already exists"` swallow) → `session_start` → `history.clear()` → `CreationState(..., step="NAME")` → `_delete_save_file()` → `return session`.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| No short-circuit on L1 | Always run L1b (when `not ok`) then proceed to L2 — do not return early on `end_session` failure |
| L1b explicit | `GameBridge.end_session` only auto-falls back on **exception**, not `{"ok": false}` — orchestrator must call `force_close_all_sessions()` when L1 `not ok` |
| APP-015 boundary | Do **not** add creation-block disk clear before L1 (C1–C2) — APP-015 owns `_save_session` / failure autosave |
| Bridge/UI | No edits to `bridge.py` or `app/ui/app.py` unless WS2 proves API gap |
| Caller `ok` checks | Do **not** add death/resume guards — **APP-019** unless WS2 failure forces minimal fix |
| Batch merge | APP-015 may prepend **before** L1 later — land APP-014 first or rebase 015 atop 014 |

### Test gates (WS1 done when)

```bash
# Optional smoke — full lifecycle file added in WS2
python -m pytest app/tests/test_smoke.py -q
```

**Minimum WS1 close:** Both lines + docstring in `orchestrator.py`; grep confirms `wipe_all_data` is not first statement in `setup_new_game`.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-014
ticket: tmp/backlog/app-014-setupnewgame-session-lifecycle.md
run-folder: tmp/backlog/runs/app-014-setupnewgame-session-lifecycle/
spec: spec.md | plan: plan.md §1 | domain spec: tmp/app-session-persistence-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only — prepend end_session + force_close_all_sessions before wipe_all_data in setup_new_game (~348–361).
AGENTS.md: claim APP-014 before app/ edits; stay within Expected files; no test file edits.
Verify callers (process_turn new game, _handle_player_death, run_ended) need no duplicate lifecycle.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Lifecycle pytest T-014a–c

**Scope:** Plan §2 — new `app/tests/test_setup_new_game_lifecycle.py` with T-014a (mid-creation reset), T-014b (prior session closed), T-014c (`world_corpses` preserved).

**Depends on:** WS1 — tests assert L1/L1b + L2–L7 ordering in `setup_new_game`.

**Requirements covered:** spec T-014a–c, ticket AC (pytest + clean NAME after mid-creation).

### Implementation order (within stream)

| # | Test ID | Setup | Assert | Plan ref |
|---|---------|-------|--------|----------|
| 1 | **T-014a** | `bridge.session_start("salt-road")`; `orch.creation` → `step="SKILLS"`, `name="Test"`; `setup_new_game()` | `result["ok"]`; `creation.step == "NAME"`; `bridge.status()["active"]`; open sessions ≤ 1 logical current | §2 table |
| 2 | **T-014b** | `session_start` → engine `active.json`; `setup_new_game()` | Prior row `ended_at` set **or** deleted; new session `current`; `creation.step == "NAME"` | §2 table |
| 3 | **T-014c** | Death pattern: character + `process_delver_death` via bridge; count `world_corpses`; `setup_new_game()` | Corpse count unchanged; `result["ok"]` | §2 table, `test_death_rules.py:115–134` |

### Module helpers (plan §2)

| Helper | SQL / role |
|--------|------------|
| `count_open_sessions(conn)` | `SELECT COUNT(*) FROM sessions WHERE ended_at IS NULL` |
| `count_corpses(conn)` | `SELECT COUNT(*) FROM world_corpses` |

Use fixtures: `orchestrator`, `bridge`, `isolated_workspace` from `app/tests/conftest.py`. File/docstring should enable `-k "setup_new_game or session_lifecycle"`.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| T-014b style | Prefer “no stray open sessions except new current” over matching obsolete log substrings |
| T-014c fixture | Minimal bridge `process_delver_death` path — read `play/tomb_gm/tests/test_death_rules.py` + `death_db` prerequisites; avoid full combat death unless needed |
| No bridge/orch edits | Unless WS1 missing — then escalate, do not patch around in tests |
| Conftest | No change unless helper belongs in shared `helpers.py` and plan approves |
| Out of scope | Domain spec edit, UI, APP-015 failure autosave race |

### Test gates (WS2 done when all pass)

```bash
# Primary
python -m pytest app/tests/test_setup_new_game_lifecycle.py -q

# Regression (from repo root)
python -m pytest app/tests -q -k "setup_new_game or session_lifecycle or creation_flow"
python -m pytest play/tomb_gm/tests -q -k session
```

### Post-impl (not WS2 — ticket release)

- `tmp/app-session-persistence-spec.md`: mark APP-014 checklist `[x]`; changelog dated **done**
- `python tmp/backlog/claim_ticket.py release APP-014 --done`
- Stage 7: `human-test-plan.md` manual (APP-064 partial creation → `new game` → NAME)

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-014
ticket: tmp/backlog/app-014-setupnewgame-session-lifecycle.md
run-folder: tmp/backlog/runs/app-014-setupnewgame-session-lifecycle/
spec: spec.md | plan: plan.md §2 | domain spec: tmp/app-session-persistence-spec.md § Tests APP-014
workstreams: workstreams.md § WS2

Prerequisite: WS1 present — setup_new_game prepends end_session + force_close before wipe.
Implement WS2 only — app/tests/test_setup_new_game_lifecycle.py (T-014a, T-014b, T-014c + helpers).
AGENTS.md: claim APP-014 if not active; no orchestrator edits unless WS1 incomplete.
Run: python -m pytest app/tests/test_setup_new_game_lifecycle.py -q && python -m pytest app/tests -q -k "setup_new_game or session_lifecycle or creation_flow"
Write reflection-dev-impl-WS2.md before return.
```
