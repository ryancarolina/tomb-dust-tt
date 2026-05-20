# QA PASS: Implementation

**Task:** APP-049-create-app-tests-package  
**backlog_ticket:** APP-049  
**Verdict:** **PASS**  
**Tests run:** `python -m pytest app/tests -q` (repo root); ephemeral `test_orchestrator_fixture` (QA-only, removed)  
**Diff scope reviewed:** `app/tests/__init__.py`, `app/tests/helpers.py`, `app/tests/conftest.py`, `app/tests/test_smoke.py`  
**Ticket AC:** R1–R4 — all satisfied in committed code

---

## Pytest output (primary gate)

```text
python -m pytest app/tests -q
.                                                                        [100%]
1 passed in 0.09s
```

Exit code **0**; **1** test collected (avoids empty-collection exit code 5).

---

## Acceptance criteria mapping

### R1 — Package layout

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `app/tests/__init__.py` | PASS | Package marker present |
| `helpers.py`: `REPO = parents[2]`, `APP`, `PLAY`, `BUILD`, `make_isolated_workspace` | PASS | `app/tests/helpers.py:9-24` — mirrors engine contract; **not** `parents[3]` |
| `conftest.py` loads before collection | PASS | Pytest discovers fixtures; `sys.path` + `_TESTS_DIR` insert at import |

### R2 — Import paths (`conftest.py`)

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Insert `REPO/app`, `REPO/play`, `REPO/build/tools` if missing | PASS | `app/tests/conftest.py:18-21` via `APP`, `PLAY`, `BUILD / "tools"` from helpers |
| `import gm.bridge` / `import tomb_gm.config` from repo root | PASS | Smoke test exercises `GameBridge` without `cd app` |

### R3 — Fixtures (`conftest.py`)

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `isolated_workspace` → `make_isolated_workspace(tmp_path)`; never `play/workspace` | PASS | `conftest.py:24-26`; no `PLAY/workspace` references |
| `bridge` → `GameBridge(workspace=…)`, `init()`, teardown `ctx.conn.close()` | PASS | `conftest.py:29-36` |
| `app_config` → `app/config.yaml` dict | PASS | `conftest.py:39-42` |
| `mock_openrouter_client` patches **`gm.orchestrator.create_client`** | PASS | `conftest.py:69` — not `gm.openrouter.create_client` |
| Import-order: no module-level `Orchestrator` in `app/tests/**` | PASS | Grep: only lazy import inside `orchestrator` fixture (`conftest.py:86`) |
| `orchestrator` workspace-safe (preferred GameBridge factory patch) | PASS | `monkeypatch.setattr("gm.orchestrator.GameBridge", …)` + assert workspace + teardown (`conftest.py:77-91`) |

**QA ad-hoc:** Ephemeral test using `orchestrator` fixture passed (`1 passed in 0.48s`); `play/workspace/tomb_gm.db` mtime unchanged.

### R4 — Smoke test

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `test_bridge_status_after_init` uses `bridge` | PASS | `app/tests/test_smoke.py:4-9` |
| Asserts `status()` is `dict` with `roster` list | PASS | Lines 7-9 |
| `pytest app/tests -q` exit 0, ≥1 test | PASS | See pytest output above |

---

## Adversarial checks (patch targets, pollution)

| Check | Result | Notes |
|-------|--------|-------|
| `parents[2]` depth | PASS | `helpers.py:9`; comment documents engine `parents[3]` contrast |
| Lazy imports | PASS | `GameBridge` / `Orchestrator` imported inside fixtures only |
| `gm.orchestrator.create_client` patch | PASS | Bound name in orchestrator module (`orchestrator.py:45`, `:82`) |
| `gm.orchestrator.GameBridge` factory monkeypatch | PASS | Replaces module-level `from gm.bridge import GameBridge` binding used in `__init__` |
| `play/workspace` pollution | PASS | `git status -- play/workspace` unchanged after app/tests; pre-existing untracked `tomb_gm.db` mtime stable across runs |

---

## Out of scope / handoff notes

| Item | Status |
|------|--------|
| Domain spec changelog / ticket `done` | Pending **release** (`tmp/app-logging-qa-spec.md` checklist still “implementation pending”) |
| `orchestrator` fixture in committed tests | Not required by R4; fixture registered and verified ad-hoc — APP-057 will exercise |
| Engine regression `play/tomb_gm/tests` | **1 pre-existing failure** (`test_init_status_check_suggest`); unrelated to APP-049; not in ticket AC |

---

## Files reviewed

- `app/tests/__init__.py`
- `app/tests/helpers.py`
- `app/tests/conftest.py`
- `app/tests/test_smoke.py`
