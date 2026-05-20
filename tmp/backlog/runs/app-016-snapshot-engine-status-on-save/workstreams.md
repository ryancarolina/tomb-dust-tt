# Workstreams: APP-016-snapshot-engine-status-on-save

**backlog_ticket:** APP-016  
**plan:** [plan.md](plan.md) · **spec:** [spec.md](spec.md) · **domain spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md) § Engine status snapshot on save (APP-016)

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | `_save_session` engine_status snapshot | — | `app/ui/app.py` | S5c single `get_status()`; conditional `engine_status` key; no load/trigger edits |
| WS2 | Save snapshot tests (T4a–d) | WS1 | `app/tests/test_engine_status_on_save.py`, `app/tests/conftest.py` (optional) | `pytest app/tests/test_engine_status_on_save.py -q` exit 0 |
| WS3 | Domain spec + ticket close | WS1, WS2 | `tmp/app-session-persistence-spec.md`, `tmp/backlog/app-016-snapshot-engine-status-on-save.md` | AC checked; changelog row; `release APP-016 --done` |

**Stream count:** 3 — WS1 unblocks WS2; WS3 runs at release after impl QA (not parallel with WS1).

**Batch coordination (not WS deps):** Land **APP-015** C2 (`engine_status` clear on `setup_new_game` entry) with or before APP-016 so failure-path `new game` does not leave pre-wipe snapshots on disk. APP-016 does **not** edit `orchestrator.py` or `_load_session`.

---

## WS1 — `_save_session` engine_status snapshot

**Scope:** Plan § WS1 / trace B — extend `App._save_session()` to persist the full `Orchestrator.get_status()` dict under `engine_status` when status is success-shaped. Reuse the existing single `get_status()` call for `session_id` / `campaign_slug` extraction.

**Requirements covered:** domain S5a–e; ticket AC “snapshot engine status() on save”; spec T4a/T4b/T4d write path.

### Implementation order (within stream)

| # | Task | File | Plan ref |
|---|------|------|----------|
| 1 | Add `engine_status: dict \| None = None` before `data` build | `app/ui/app.py` | B1–B3 |
| 2 | On success-shaped status, assign `engine_status = status` (full dict) | `app/ui/app.py` | B3 |
| 3 | Failure-shaped → leave `engine_status` as `None`: raised exception; `status.get("ok") is False`; or `"_error" in status` | `app/ui/app.py` | B3, open Q1 |
| 4 | `if engine_status is not None: data["engine_status"] = engine_status` — never write `engine_status: null` | `app/ui/app.py` | B4 |
| 5 | Optional one-line docstring note: save-time engine truth for APP-017/018; read path out of scope | `app/ui/app.py` | WS1.4 |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Single call | One `get_status()` per save — no second bridge round-trip (S5c) |
| Write-only | Do **not** read `engine_status` in `_load_session`, orchestrator resume, or reconcile — APP-017/018 |
| Triggers unchanged | Autosave, quit, post-turn `finally` — no new `_save_session()` call sites |
| Other keys unchanged | `narration_lines`, `creation_state`, `combat_state`, etc. — additive key only |
| Out of scope | `app/gm/orchestrator.py` (APP-015 C2); `_load_session` (APP-017/018); deep-copy not required |
| Batch | No stale-clear logic in WS1 — APP-015 owns `pop("engine_status")` on `setup_new_game` |

### Test gates (WS1 done when)

WS1 has no dedicated test file; verify by code review + WS2. Optional smoke:

```bash
cd app && python -c "from ui.app import App; print('import ok')"
```

**Expected:** import succeeds; no edits outside `app/ui/app.py`.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-016
ticket: tmp/backlog/app-016-snapshot-engine-status-on-save.md
run-folder: tmp/backlog/runs/app-016-snapshot-engine-status-on-save/
spec: spec.md | plan: plan.md § WS1, trace B | domain spec: tmp/app-session-persistence-spec.md § APP-016 (read only)
workstreams: workstreams.md § WS1

Implement WS1 only — _save_session() engine_status snapshot in app/ui/app.py.
Follow plan B1–B5: single get_status(), omit key on failure, no _load_session changes.
AGENTS.md: claim/focus APP-016 if not active; stay within Expected files.
Write reflection-dev-impl-ws1.md before return.
```

---

## WS2 — Save snapshot tests (T4a–d)

**Scope:** Plan § WS2 — new headless App test module asserting save JSON includes `engine_status` (mid-creation, post-finalize), legacy load without key, and omit-on-`get_status` failure.

**Depends on:** WS1 — tests assert `engine_status` key behavior that WS1 implements.

**Requirements covered:** domain T4a–d; spec test plan; ticket Expected files `app/tests/`.

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | New module `test_engine_status_on_save.py` | Module docstring; never write dev `app/session_state.json` | WS2 |
| 2 | Fixtures: `save_path` (monkeypatch `ui.app.SAVE_PATH`), `headless_app` (`SDL_VIDEODRIVER=dummy`, pygame init/quit), `read_save` | Inline in module or `conftest.py` if reused | Fixtures table |
| 3 | **T4a** `test_save_includes_engine_status_mid_creation` | `new game` + `Dumpy`; `_save_session()`; assert `awaiting == "CHARACTER_CREATION"`, `roster == []`, matches `get_status()` | C trace |
| 4 | **T4b** `test_save_includes_engine_status_after_finalize` | Reuse `FIXED_ROLL` / INPUTS from `test_creation_flow.py`; assert non-empty roster, `awaiting != "CHARACTER_CREATION"` | D trace |
| 5 | **T4c** `test_load_session_legacy_without_engine_status` | Seed minimal JSON without `engine_status`; `_load_session()`; no raise; narration smoke | E trace |
| 6 | **T4d** `test_save_omits_engine_status_on_get_status_failure` | Monkeypatch `get_status` → raise; assert `"engine_status" not in data`; file still written | F trace |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Isolation | `monkeypatch.setattr("ui.app.SAVE_PATH", tmp_path / "session_state.json")` — no prod save path |
| Headless pygame | Set `SDL_VIDEODRIVER=dummy` **before** `pygame.init()` |
| T4b rolls | Import or copy `FIXED_ROLL` from `test_creation_flow.py` — avoid flaky attribute rolls |
| T4c scope | Light assertions only (no exception + narration/history smoke) — APP-016 must not add load behavior |
| T4d | Assert key **omitted**, not `null`; `creation_state` may still be present |
| Out of scope | No `_load_session` production edits; no orchestrator changes; domain spec edit is WS3 |

### Test gates (WS2 done when all pass)

```bash
cd app && python -m pytest app/tests/test_engine_status_on_save.py -q
cd app && python -m pytest app/tests -q -k "engine_status or save_session"
python -m pytest play/tomb_gm/tests -q -k session
```

**Expected:** T4a–d green; no regressions in filtered app tests; engine session tests pass.

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-016
ticket: tmp/backlog/app-016-snapshot-engine-status-on-save.md
run-folder: tmp/backlog/runs/app-016-snapshot-engine-status-on-save/
spec: spec.md | plan: plan.md § WS2, traces C–F | domain spec: tmp/app-session-persistence-spec.md § T4a–d (read only)
workstreams: workstreams.md § WS2

Prerequisite: WS1 present in branch (_save_session writes engine_status).
Implement WS2 only — test_engine_status_on_save.py with T4a–d per plan.
Use headless pygame fixture; reuse test_creation_flow FIXED_ROLL for T4b.
Run: cd app && python -m pytest app/tests/test_engine_status_on_save.py -q
Write reflection-dev-impl-ws2.md before return.
```

---

## WS3 — Domain spec + ticket close

**Scope:** Plan § WS3 — on ticket release, sync domain spec checklist/changelog and mark ticket done. No blocking code dependency for WS1/WS2 merge, but runs **after** impl QA PASS.

**Depends on:** WS1, WS2 — behavior and tests must land before spec claims implementation.

**Requirements covered:** ticket “Spec sync (required on close)”; domain § APP-016 AC checklist.

### Implementation order (within stream)

| # | Task | File | Plan ref |
|---|------|------|----------|
| 1 | Tick domain spec AC checklist for S5 / T4 | `tmp/app-session-persistence-spec.md` | WS3 |
| 2 | Append changelog row: date + “implemented `engine_status` on `_save_session`” | `tmp/app-session-persistence-spec.md` | WS3 |
| 3 | Mark ticket Status → `done`, add **Closed** date | `tmp/backlog/app-016-snapshot-engine-status-on-save.md` | Spec sync |
| 4 | Run drift check; `python tmp/backlog/claim_ticket.py release APP-016 --done` | run-folder `drift-check.md` | Stage 6 |

### Critical constraints

| Constraint | Detail |
|------------|--------|
| No behavior drift | Changelog must match WS1/WS2 code exactly |
| master-spec | Confirm registry row for session persistence still accurate (no edit unless drift) |
| Batch QA | Note APP-015 T-015d + APP-016 T4a in batch manual playtest if 015 merged same batch |

### Done when

- Domain spec AC boxes checked; changelog entry dated 2026-05-20 (or close date)
- Ticket file Status `done`
- `release APP-016 --done` clears active ticket session

### Prompt seed for Task subagent (WS3 / release)

```
backlog_ticket: APP-016
run-folder: tmp/backlog/runs/app-016-snapshot-engine-status-on-save/
workstreams: workstreams.md § WS3

Prerequisite: WS1 + WS2 merged; QA impl PASS.
Update tmp/app-session-persistence-spec.md checklist + changelog; close ticket file.
Run drift-check; python tmp/backlog/claim_ticket.py release APP-016 --done
Write reflection-dev-impl-ws3.md or include in release agent reflection.
```

---

## AC mapping (quick reference)

| AC / spec | WS | Test |
|-----------|-----|------|
| Snapshot `status()` on save | WS1 | T4a, T4b (WS2) |
| Full dict / reconcile keys | WS1 | T4a `awaiting`, `roster`; T4b roster |
| Failure non-blocking | WS1 | T4d (WS2) |
| Legacy load unchanged | — (no code) | T4c (WS2) |
| Triggers unchanged | WS1 (review only) | Trace A |
| APP-015 owns new-game clear | — (batch) | T-015d (015) |
