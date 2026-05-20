# Implementation Plan: APP-016-snapshot-engine-status-on-save

**Status:** draft (Dev plan round 1)  
**backlog_ticket:** APP-016  
**ticket_path:** [tmp/backlog/app-016-snapshot-engine-status-on-save.md](../../app-016-snapshot-engine-status-on-save.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md) § Engine status snapshot on save (APP-016)  
**run-folder:** `tmp/backlog/runs/app-016-snapshot-engine-status-on-save/`  
**Spec:** [spec.md](spec.md) · [research-brief.md](research-brief.md) · [qa-spec-pass.md](qa-spec-pass.md)

## Approach

Extend **`App._save_session()`** in `app/ui/app.py` to persist the **full** `Orchestrator.get_status()` dict under **`engine_status`** on successful status read (S5b–S5c). Reuse the existing single `get_status()` call for `session_id` / `campaign_slug` and the snapshot — no second bridge round-trip.

**Write-only:** do not read `engine_status` in `_load_session`, orchestrator resume, or reconcile — **APP-017** / **APP-018**. Do not implement new-game stale clear — **APP-015** C2 / **T-015d** (`pop` / `null` on every `setup_new_game` entry).

**Batch:** Land **APP-015** C2 with or before APP-016 so failure-path `new game` does not leave pre-wipe `engine_status` on disk (domain PM r2; [qa-spec-pass.md](qa-spec-pass.md) implement-order note).

---

## Root cause (current vs required)

```393:425:app/ui/app.py
    def _save_session(self):
        """Persist narration history and visited map cells."""
        session_id = None
        campaign_slug = None
        if self._orchestrator:
            try:
                status = self._orchestrator.get_status()
                active = status.get("active") or {}
                session_id = active.get("session_id")
                campaign_slug = active.get("campaign_slug")
            except Exception:
                pass
        data = {
            "session_id": session_id,
            "campaign_slug": campaign_slug,
            ...
            "combat_state": (...),
        }
```

| Aspect | Today | Required (S5) |
|--------|--------|----------------|
| Engine truth on disk | `session_id`, `campaign_slug` only | Full `handle_status` payload as `engine_status` |
| `get_status()` calls per save | 1 (partial use) | 1 (session fields + full snapshot) |
| Failure | Swallowed; no snapshot | Save continues; **`engine_status` key omitted** (S5d) |
| Load | N/A for this ticket | Unchanged; legacy files without key OK (S5e / T4c) |

**Source of truth for payload:** `Orchestrator.get_status()` → `GameBridge.status()` → `play/tomb_gm/cli/cmd_core.handle_status` — same dict as APP-005 `creation_finalize` JSONL `engine_status` ([orchestrator.py `_log_creation_finalize_status`](../../../../app/gm/orchestrator.py)).

---

## Deep code-path traces

### A. Save triggers (unchanged — R2)

All paths already call `_save_session()` only; APP-016 adds a field, not a trigger.

| Trigger | File:symbol | When |
|---------|-------------|------|
| Autosave | `app/ui/app.py:_autosave` (~60s) | Main loop |
| Quit | `app/ui/app.py:run` | `QUIT` / `K_ESCAPE` |
| Post-turn | `app/ui/app.py:_process_turn` `finally` | After narration-producing turn |

### B. `_save_session` (planned)

| Step | Action |
|------|--------|
| B1 | If `self._orchestrator`: `status = self._orchestrator.get_status()` in `try` |
| B2 | Extract `session_id`, `campaign_slug` from `status.get("active") or {}` (unchanged) |
| B3 | If status is **success-shaped**: set `engine_status = status` (full dict). **Failure-shaped** (omit key): raised exception; or `status.get("ok") is False`; or `"_error" in status` (defensive; matches finalize logging pattern) |
| B4 | Build `data` with existing keys; **`if engine_status is not None: data["engine_status"] = engine_status`** — do not set `engine_status: null` on failure (S5d preferred) |
| B5 | `SAVE_PATH.write_text(json.dumps(data, indent=2), ...)` — outer `try/except` unchanged |

**Reconcile-relevant keys** (when session row exists): `awaiting`, `roster`, `party`, `combat`, `active`, plus any other keys `handle_status` returns today (e.g. `characters`, `ok`, `workspace`).

### C. Mid-creation save (T4a target)

| Step | File:symbol | Action |
|------|-------------|--------|
| C1 | `orchestrator.process_turn("new game")` | Engine session + `CHARACTER_CREATION`, empty roster |
| C2 | `orchestrator.process_turn("Dumpy")` | App `creation_state` may advance; engine often still `CHARACTER_CREATION` + `roster: []` |
| C3 | `App._save_session()` | Writes `creation_state` + **`engine_status.awaiting == "CHARACTER_CREATION"`**, **`engine_status.roster == []`** |

### D. Post-finalize / in-delve save (T4b target)

| Step | Action |
|------|--------|
| D1 | Reuse [test_creation_flow.py](../../../../app/tests/test_creation_flow.py) INPUTS through finalize (or shorter path after `character_create`) |
| D2 | `_save_session()` | `engine_status.roster` non-empty; `engine_status.awaiting != "CHARACTER_CREATION"` (expect `PLAYER_ACTIONS` or delver phase) |

### E. Load legacy (T4c — no new read logic)

| Step | File:symbol | Action |
|------|-------------|--------|
| E1 | Seed `session_state.json` **without** `engine_status` |
| E2 | `App._load_session()` | Restores narration/history/map; `import_creation_state` / `_sync_*` unchanged |
| E3 | Assert | No exception; `engine_status` not required by load path |

### F. `get_status()` failure (T4d)

| Step | Action |
|------|--------|
| F1 | `monkeypatch` `orchestrator.get_status` → raise `RuntimeError("simulated")` |
| F2 | `_save_session()` | File written; **`"engine_status" not in data`**; `session_id`/`campaign_slug` may be null; `creation_state` still exported if orchestrator present |

### G. Batch — new game (coordination only)

| Ticket | Role |
|--------|------|
| **APP-014** | L7 deletes whole `session_state.json` on successful setup — no stale snapshot |
| **APP-015** | C2 removes `engine_status` on every `setup_new_game` entry — **not APP-016** |
| **APP-016** | Next `_save_session()` after session exists writes fresh snapshot |

---

## Task breakdown

### WS1 — `_save_session` snapshot (`app/ui/app.py`)

1. Refactor the existing `get_status()` block:
   - Keep `session_id` / `campaign_slug` extraction.
   - Add `engine_status: dict | None = None` before `data` build.
   - On success-shaped status, assign `engine_status = status` (full dict, not a shallow copy required — treat as immutable snapshot at write time).

2. Add `engine_status` to `data` only when non-`None` (omit key on failure — S5d).

3. **Do not** change `_load_session`, save triggers, `SAVE_PATH`, or other persisted keys.

4. **Optional docstring** one line: notes `engine_status` is save-time engine truth for APP-017/018 (read path out of scope).

### WS2 — Tests (`app/tests/test_engine_status_on_save.py`)

**New module** — headless App + isolated save path; never write dev `app/session_state.json`.

**Fixtures (in test module or `conftest.py` if reused):**

| Fixture | Purpose |
|---------|---------|
| `save_path(tmp_path, monkeypatch)` | `monkeypatch.setattr("ui.app.SAVE_PATH", tmp_path / "session_state.json")` |
| `headless_app(app_config, orchestrator, save_path)` | `SDL_VIDEODRIVER=dummy`, `pygame.init()`, `App(app_config)`, `_layout(800, 600)`, attach `orchestrator`, yield, `pygame.quit()` |
| `read_save(save_path)` | `json.loads(save_path.read_text())` |

**Cases (domain T4a–d / spec test plan):**

| ID | Test | Setup | Assert |
|----|------|-------|--------|
| **T4a** | `test_save_includes_engine_status_mid_creation` | `new game` + `Dumpy`; `_save_session()` | Save has `engine_status`; `awaiting == "CHARACTER_CREATION"`; `roster == []`; matches `orchestrator.get_status()` for those fields |
| **T4b** | `test_save_includes_engine_status_after_finalize` | Full creation INPUTS (reuse `FIXED_ROLL` monkeypatch from `test_creation_flow.py`); `_save_session()` | `len(engine_status["roster"]) >= 1`; `awaiting != "CHARACTER_CREATION"` |
| **T4c** | `test_load_session_legacy_without_engine_status` | Write minimal legacy JSON (narration + `creation_state` only); `_load_session()` | No raise; narration restored; orchestrator import/sync runs (smoke: `creation.active` or history length unchanged vs pre-load) |
| **T4d** | `test_save_omits_engine_status_on_get_status_failure` | Monkeypatch `get_status` → raise; `_save_session()` | File exists; `"engine_status" not in data`; other keys present (`creation_state`, etc.) |

**T4b note:** Prefer calling shared INPUTS loop from `test_creation_flow` constants to avoid drift; keep test file focused on save JSON, not full FSM narration asserts.

### WS3 — Domain spec changelog (ticket close)

- **`tmp/app-session-persistence-spec.md`:** § APP-016 already drafted (PM r2). On impl close: tick AC checklist, append changelog row with date + “implemented `engine_status` on `_save_session`”.
- **Not in WS1 diff** unless PM left AC boxes unchecked — impl agent updates on **release --done**.

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/ui/app.py` | `_save_session()` — S5c single `get_status()`, conditional `engine_status` |
| `app/tests/test_engine_status_on_save.py` | **New** — T4a–d |
| `app/tests/conftest.py` | **Optional** — `headless_app` / `save_path` fixtures if cleaner than inline |
| `tmp/app-session-persistence-spec.md` | Changelog + AC checkboxes on ticket close (not blocking code PR) |

**Explicitly out of scope:**

| File | Owner |
|------|--------|
| `app/gm/orchestrator.py` | APP-015 (`engine_status` clear on new game) |
| `app/ui/app.py` `_load_session` | APP-017 / APP-018 |

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `cd app && python -m pytest app/tests/test_engine_status_on_save.py -q` | T4a–d green |
| 2 | `cd app && python -m pytest app/tests -q -k "engine_status or save_session"` | Same module + no regressions |
| 3 | `python -m pytest play/tomb_gm/tests -q -k session` | Engine regression (no app save changes in engine) |
| 4 | Manual (Stage 7) | Mid-creation autosave/Escape → `app/session_state.json` shows `engine_status`; load/continue behavior unchanged |

---

## Rollback / flags

- No feature flag. Rollback = revert `_save_session` hunk + delete test module.
- Additive JSON key; legacy saves and load path remain valid.

---

## Open questions

| # | Question | Recommendation |
|---|----------|----------------|
| 1 | Error-shaped status besides exception? | Treat `ok is False` or `_error` in dict as omit; `handle_status` normally returns `ok: True` |
| 2 | Deep-copy `status` before write? | **Not required** — snapshot is point-in-time; no mutator on saved dict in APP-016 |
| 3 | Pygame in CI? | Use `SDL_VIDEODRIVER=dummy` before `pygame.init()` in fixture (standard headless pattern) |
| 4 | APP-015 merge order? | Implement 015 C2 before or with 016; run T-015d + T4a in same batch QA |

## Acceptance criteria mapping

| Ticket / spec AC | Implementation | Test |
|------------------|----------------|------|
| Snapshot `status()` on save | `engine_status` in `_save_session` when get_status succeeds | T4a, T4b |
| Full dict / reconcile keys | Assign full `status` dict | T4a asserts `awaiting`, `roster`; T4b asserts roster |
| Failure non-blocking | Omit key on exception / error-shaped | T4d |
| Legacy load unchanged | No `_load_session` edits | T4c |
| Triggers unchanged | No new call sites | Trace A only (review) |
| APP-015 owns new-game clear | No orchestrator change | Batch note + T-015d (015) |
