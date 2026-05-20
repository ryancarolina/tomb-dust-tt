# Spec: APP-049-create-app-tests-package

**Status:** draft  
**backlog_ticket:** APP-049  
**ticket_path:** tmp/backlog/app-049-create-app-tests-package.md  
**domain_spec:** tmp/app-logging-qa-spec.md  
**registry_gap:** false (per research-brief; PM confirms)  
**Domain specs touched:** [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) — § App test package, Fixture inventory, Task checklist, Changelog

## Problem

`app/tests/` does not exist. Downstream tickets (APP-051 golden path, APP-057 creation flow, APP-054 green gate) need a shared pytest package with correct `sys.path`, isolated workspaces, and headless-safe fixtures before any behavioral tests land.

## Goals

- Add `app/tests/` as a discoverable pytest package runnable from **repo root**: `python -m pytest app/tests -q`.
- Centralize import path setup (`gm.*`, `tomb_gm.*`) in `conftest.py` (mirror `app/main.py` + explicit `app/` on `sys.path`).
- Provide reusable fixtures for isolated engine workspaces, `GameBridge`, app config, mocked OpenRouter, and `Orchestrator` — without mutating `play/workspace`.
- Include one minimal smoke test so collection is non-empty and fixtures are exercised (avoids pytest exit code 5).

## Non-goals

- Behavioral tests: creation FSM (APP-057), mock LLM golden path (APP-051), orchestrator turn-loop assertions.
- Changing `Orchestrator.__init__` or `GameBridge` API (no workspace constructor param on orchestrator).
- CI workflow / `pytest.ini` / `requirements.txt` pytest pin (APP-050).
- JSONL `LOG_DIR` monkeypatch or log pollution policy (later ticket if needed).
- Duplicating engine CLI subprocess fixtures (`run_tomb_gm`) unless a future ticket needs them.

## Requirements

### R1: Package layout

**Acceptance criteria**

- [ ] `app/tests/` exists with `__init__.py` (empty package marker).
- [ ] `app/tests/helpers.py` mirrors `play/tomb_gm/tests/helpers.py` contract (`REPO`, `APP`, `PLAY`, `BUILD`, `make_isolated_workspace`) — preferred over importing engine test helpers to keep trees independent.
- [ ] **`app/tests/helpers.py` path depth:** `REPO = Path(__file__).resolve().parents[2]` (app tree is one level shallower than engine tests). Engine uses `parents[3]` at `play/tomb_gm/tests/helpers.py`; **do not copy-paste** engine `parents[3]` into app tests. Also define `APP = REPO / "app"`.
- [ ] `app/tests/conftest.py` loads before collection when running from repo root.

**Authoritative detail:** [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) § App test package.

### R2: `conftest.py` — import paths

**Acceptance criteria**

- [ ] At module import (before fixtures), insert into `sys.path` if missing: `REPO/app`, `REPO/play`, `REPO/build/tools` where `REPO = Path(__file__).resolve().parents[2]` (same depth as `helpers.py`).
- [ ] `import gm.bridge` and `import tomb_gm.config` succeed with cwd = repo root (no `cd app`).

### R3: `conftest.py` — fixtures

**Acceptance criteria**

- [ ] `isolated_workspace(tmp_path)` → `make_isolated_workspace(tmp_path)`; never uses `play/workspace`.
- [ ] `bridge(isolated_workspace)` → `GameBridge(workspace=isolated_workspace)`; calls `bridge.init()` before yield; closes connection on teardown if needed (or rely on tmp_path GC).
- [ ] `app_config` → loads `app/config.yaml` (same shape as `main.load_config()` / PyGame `App` config dict).
- [ ] `mock_openrouter_client(monkeypatch)` → patches **`gm.orchestrator.create_client`** (the name bound at import in `orchestrator.py`, not `gm.openrouter.create_client` alone). Returns a stub `OpenAI`-compatible client whose `chat.completions.create` returns a minimal assistant message (content string, empty `tool_calls`, `finish_reason="stop"`). No `OPENROUTER_API_KEY` required.
- [ ] **Import-order rule (mandatory):** No module-level `from gm.orchestrator import Orchestrator` (or `import gm.orchestrator` before patch) in any file under `app/tests/**`. Fixtures that need `Orchestrator` must **lazy-import** inside the fixture body **after** `mock_openrouter_client` has applied the monkeypatch. Rationale: `gm.orchestrator` binds `create_client` at import time (`from gm.openrouter import create_client`); patching only `gm.openrouter.create_client` after `gm.orchestrator` is loaded leaves `Orchestrator.__init__` calling the real client.
- [ ] `orchestrator(app_config, isolated_workspace, mock_openrouter_client)` → workspace-safe construction per **Orchestrator fixture workspace safety** below.

**Authoritative fixture table:** domain spec § Fixture inventory.

#### Orchestrator fixture workspace safety

`Orchestrator.__init__` always runs `GameBridge()` before any test can swap `orchestrator.bridge`. That default resolves to `play/workspace` (`DEFAULT_WORKSPACE` in `play/tomb_gm/config.py`) and opens SQLite + migrations there. `_assert_not_play_workspace` guards session **start**, not bridge construction — so post-init swap alone is **not** sufficient.

**Required fixture behavior (pick one pattern; both must avoid leaving `play/workspace` mutated):**

1. **Preferred:** Before constructing `Orchestrator`, `monkeypatch.setattr("gm.orchestrator.GameBridge", …)` with a factory/wrapper that returns `GameBridge(workspace=isolated_workspace)` when called from `Orchestrator.__init__`, **or** monkeypatch `GameBridge.__init__` only for the orchestrator fixture scope so the default `GameBridge()` in `__init__` targets `isolated_workspace`.
2. **Minimum:** If using stock `Orchestrator(app_config)` after `mock_openrouter_client`: immediately after `__init__`, assign `orchestrator.bridge = GameBridge(workspace=isolated_workspace)` and **close** the default bridge’s DB connection in fixture teardown (the default instance may have already touched `play/workspace` — teardown must not leave connections open; document residual risk in test module docstring).

**Forbidden:** Any orchestrator fixture that calls orchestrator methods (or yields) while `orchestrator.bridge` still points at `play/workspace`.

Long-term constructor injection is out of scope for APP-049 (non-goal).

### R4: Minimal smoke test (included)

**PM decision:** Include `app/tests/test_smoke.py`.

**Rationale:** Empty collection yields pytest exit code 5, which breaks naive “run app tests” gates and gives no signal that path/workspace fixtures work. One bridge-status test is scaffolding validation, not behavioral coverage.

**Acceptance criteria**

- [ ] `test_smoke.py` contains one test (e.g. `test_bridge_status_after_init`) using `bridge` fixture.
- [ ] Asserts `bridge.status()` is a `dict` containing key `roster` (list), proving imports + isolated workspace + `init()`/`status()` path.
- [ ] `python -m pytest app/tests -q` exits 0 with at least one test collected.

### R5: Downstream extension (document only)

- APP-057 adds `test_creation_flow.py` using `orchestrator` fixture; extends conftest only if new shared fixtures are needed — do not fork a second conftest.
- APP-051 adds mock-LLM response helpers / golden-path module under `app/tests/` using existing fixtures.

## Test plan

```bash
# From repo root — primary gate for this ticket
python -m pytest app/tests -q

# Regression: engine suite unchanged
python -m pytest play/tomb_gm/tests -q
```

**Expected after implementation:** `app/tests` collects ≥1 test, exit code 0; no writes under `play/workspace`.

## Human playtest hints (for Stage 7)

- No in-game behavior change. Optional sanity: `cd app && python main.py` still launches (unchanged).
- QA may note in human-test-plan: “pytest scaffold only — skip manual play unless regression paranoia.”

## Affected paths

Must match ticket **Expected files**:

- `app/tests/__init__.py`
- `app/tests/conftest.py`
- `app/tests/helpers.py`
- `app/tests/test_smoke.py`
- `tmp/app-logging-qa-spec.md` (spec draft — this ticket)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM spec draft (APP-049) |
| 2026-05-20 | **R2:** PM spec revision round 2 — QA round 1 fixes: `gm.orchestrator.create_client` patch + import-order rule; orchestrator workspace safety; explicit `parents[2]`; ticket AC aligned |
