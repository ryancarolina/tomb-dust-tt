# APP-049: Create app/tests package



| Field | Value |

|-------|-------|

| **ID** | APP-049 |

| **Type** | chore |

| **Priority** | P1 |

| **Status** | done |

| **Domain spec** | [`app-logging-qa-spec.md`](../app-logging-qa-spec.md) |

| **Created** | 2026-05-20 |

| **Closed** | 2026-05-20 |



## Summary



App test suite structure missing. Add pytest package with import paths, isolated workspaces, shared fixtures, and one smoke test so `python -m pytest app/tests -q` exits 0 (avoids empty-collection exit code 5). Downstream APP-051 / APP-057 depend on these fixtures.



## Acceptance criteria



Traceability: run spec [`spec.md`](runs/app-049-create-app-tests-package/spec.md) R1–R4; authoritative detail in domain spec § App test package + § Fixture inventory.



### R1 — Package layout



- [x] `app/tests/__init__.py` exists (empty package marker).

- [x] `app/tests/helpers.py` with `REPO = Path(__file__).resolve().parents[2]`, `APP = REPO / "app"`, `PLAY`, `BUILD`, `make_isolated_workspace` (mirror engine helpers contract; **not** `parents[3]`).

- [x] `app/tests/conftest.py` loads before collection when running from repo root.



### R2 — Import paths (`conftest.py`)



- [x] At module import, insert if missing: `REPO/app`, `REPO/play`, `REPO/build/tools` where `REPO = Path(__file__).resolve().parents[2]`.

- [x] `import gm.bridge` and `import tomb_gm.config` succeed with cwd = repo root (no `cd app`).



### R3 — Fixtures (`conftest.py`)



- [x] `isolated_workspace(tmp_path)` → `make_isolated_workspace(tmp_path)`; never uses `play/workspace`.

- [x] `bridge(isolated_workspace)` → `GameBridge(workspace=…)`, `init()`, yield; teardown closes connection if needed.

- [x] `app_config` → loads `app/config.yaml` dict (same shape as `main.load_config()`).

- [x] `mock_openrouter_client(monkeypatch)` → patches **`gm.orchestrator.create_client`** (not `gm.openrouter.create_client`); stub returns minimal assistant message; no `OPENROUTER_API_KEY`. Import-order rule: no module-level `from gm.orchestrator import Orchestrator` in `app/tests/**`; lazy-import `Orchestrator` inside fixtures after patch.

- [x] `orchestrator` fixture → workspace-safe construction (see domain spec § Orchestrator fixture workspace safety): patch/mock before default `GameBridge()` opens `play/workspace`; swap to isolated bridge immediately; teardown closes default bridge if opened.



### R4 — Smoke test



- [x] `app/tests/test_smoke.py` with one test (e.g. `test_bridge_status_after_init`) using `bridge` fixture.

- [x] Asserts `bridge.status()` is a `dict` with key `roster` (list).

- [x] `python -m pytest app/tests -q` from repo root: ≥1 test collected, exit code 0.



## Expected files



- `app/tests/__init__.py`

- `app/tests/helpers.py`

- `app/tests/conftest.py`

- `app/tests/test_smoke.py`

- `tmp/app-logging-qa-spec.md` (changelog on close)



## Spec sync (required on close)



1. Mark **Status** → `done` in this ticket (add **Closed** date).

2. Update the domain spec checklist / changelog in [`app-logging-qa-spec.md`](../app-logging-qa-spec.md).

3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.



## Notes



**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-049-create-app-tests-package`



**QA drift (2026-05-20):** No spec ↔ code drift. See `runs/app-049-create-app-tests-package/drift-check.md`. Release `--done` pending orchestrator.


