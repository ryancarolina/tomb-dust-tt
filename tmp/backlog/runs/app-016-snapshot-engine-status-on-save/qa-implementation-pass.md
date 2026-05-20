# QA PASS: Implementation

**Task:** APP-016-snapshot-engine-status-on-save  
**backlog_ticket:** APP-016  
**Round:** 1  
**Verdict:** **PASS**

## Summary

`_save_session()` persists the full `Orchestrator.get_status()` dict under `engine_status` on success-shaped reads (S5b–S5c); omits the key on exception or error-shaped payload (S5d). Load path unchanged (S5e). Four new tests in `test_engine_status_on_save.py` cover T4a–d; batch T-015d regression included in focused filter.

**Blocker count:** 0

---

## Tests run

| Command | Result |
|---------|--------|
| `cd app; python -m pytest tests -q -k "engine_status or save_session"` | **pass** — 6 passed, 17 deselected in 2.16s |
| `cd app; python -m pytest tests -q` | **pass** — 23 passed in 4.74s |
| `python -m pytest play/tomb_gm/tests -q -k session` (repo root) | **pass** — 5 passed, 131 deselected in 1.94s |

Focused filter: 4× APP-016 T4 + 2× APP-015 T-015d (`engine_status` clear on `setup_new_game`).

---

## Ticket AC → code + tests

| Ticket AC | On disk | Result |
|-----------|---------|--------|
| On save, snapshot engine `status()` alongside app state | `_save_session()` sets `engine_status = status` when success-shaped; conditional write L429–430 | **PASS** |

---

## Spec R1 — Snapshot on save → implementation

| AC | Status | Evidence |
|----|--------|----------|
| Every `_save_session()` includes `engine_status` when `get_status()` succeeds | **PASS** | T4a, T4b; `if engine_status is not None: data["engine_status"] = engine_status` |
| `engine_status` is full `get_status()` / `handle_status` dict | **PASS** | `engine_status = status` (full reference); T4a asserts `es` matches live `get_status()` for `awaiting`/`roster` |
| Reconcile keys present when session exists (`awaiting`, `roster`, `party`, `combat`, `active`, …) | **PASS** | Full dict persisted; `handle_status` always sets those keys (see `play/tomb_gm/cli/cmd_core.py`) |
| On `get_status()` failure: save proceeds; `engine_status` key omitted | **PASS** | Exception swallowed; T4d asserts key absent, `creation_state` intact; code also gates on `ok is False` / `_error` |
| Legacy saves without `engine_status` load without error | **PASS** | T4c; `_load_session` unchanged (no read of `engine_status`) |

---

## Spec R2 — Save triggers unchanged

| AC | Status | Evidence |
|----|--------|----------|
| Autosave (60s), Escape quit, post-turn `finally` only — no new triggers | **PASS** | `_save_session()` call sites unchanged at L57, L78, L220, L325 |

---

## Spec R3 — Batch coordination

| AC | Status | Evidence |
|----|--------|----------|
| APP-014: no change required for APP-016 | **PASS** | No APP-014 edits in APP-016 diff scope |
| APP-015: C2 clears stale `engine_status` on `setup_new_game` (T-015d) | **PASS** | T-015d green in focused filter; APP-015 owns orchestrator clear — not APP-016 impl |
| APP-017/018 read path documented; out of scope | **PASS** | No `_load_session` / resume reads of `engine_status` |

---

## Test plan T4a–d → tests

| ID | Test | Result |
|----|------|--------|
| **T4a** | `test_save_includes_engine_status_mid_creation` | **PASS** |
| **T4b** | `test_save_includes_engine_status_after_finalize` | **PASS** |
| **T4c** | `test_load_session_legacy_without_engine_status` | **PASS** |
| **T4d** | `test_save_omits_engine_status_on_get_status_failure` | **PASS** |

---

## Diff scope reviewed

| Path | Role | Verdict |
|------|------|---------|
| `app/ui/app.py` | `_save_session()` — `engine_status` snapshot, S5c single call, S5d omit | **PASS** |
| `app/tests/test_engine_status_on_save.py` | T4a–d (new, untracked — stage commit) | **PASS** |
| `tmp/app-session-persistence-spec.md` | § Engine status snapshot (APP-016), S5 rules, T4 table (PM r2) | **PASS** — behavior documented; AC checkbox + impl changelog deferred to release |

**Out of scope (correct):** `_load_session`, orchestrator resume, APP-015 C2 in `orchestrator.py`.

---

## Non-blocking (release / drift stage)

- **T4d** covers exception path only; error-shaped payload (`ok: false`, `_error`) omit behavior is implemented (B3 gate) but not separately tested.
- **T4a/T4b** do not assert `party`/`combat`/`active` keys explicitly; mitigated by assigning the full status dict.
- Domain spec AC checkbox and **done** changelog entry — tick at `release APP-016 --done`.
- `test_engine_status_on_save.py` is untracked (`??`); include in Stage 7 commit.

---

## Handoff

**Ready for:** Drift check, `release APP-016 --done`, spec changelog sync, `human-test-plan.md` (Stage 7 manual playtest).
