# Workstreams: APP-049-create-app-tests-package

**backlog_ticket:** APP-049

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | app/tests pytest scaffold | — | `app/tests/__init__.py`, `app/tests/helpers.py`, `app/tests/conftest.py`, `app/tests/test_smoke.py` | `python -m pytest app/tests -q` exit 0; engine regression green; no `play/workspace` writes |

**Stream count:** 1 — single sequential stream (greenfield package; fixtures depend on helpers; smoke validates bridge before orchestrator fixtures are exercised by downstream tickets).

---

## WS1 — app/tests pytest scaffold

**Scope:** Create the full `app/tests/` pytest package per `plan.md`: path helpers, centralized `sys.path`, five fixtures (`isolated_workspace`, `bridge`, `app_config`, `mock_openrouter_client`, `orchestrator`), and one smoke test. No production code changes. No domain spec edit until ticket release.

**Requirements covered:** spec R1–R4 (ticket AC).

### Implementation order (within stream)

1. **`app/tests/helpers.py`** — `REPO = parents[2]`, `APP`, `PLAY`, `BUILD`, `make_isolated_workspace` (mirror engine contract; do not import engine helpers).
2. **`app/tests/conftest.py`** (core) — module-level `sys.path` inserts; `isolated_workspace`, `bridge`, `app_config` fixtures.
3. **`app/tests/test_smoke.py`** — `test_bridge_status_after_init` using `bridge` only; no module-level `gm.orchestrator` imports.
4. **`app/tests/conftest.py`** (orchestrator) — add `mock_openrouter_client` (patch `gm.orchestrator.create_client`) and `orchestrator` (preferred `GameBridge` factory monkeypatch on `gm.orchestrator.GameBridge`; lazy-import `Orchestrator` inside fixture).
5. **`app/tests/__init__.py`** — empty package marker.
6. **Verify** — run gates below; confirm `play/workspace` unchanged.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Path depth | `REPO = Path(__file__).resolve().parents[2]` — **not** engine `parents[3]` |
| sys.path | Insert `REPO/app`, `REPO/play`, `REPO/build/tools` at conftest module import |
| OpenRouter patch | Patch **`gm.orchestrator.create_client`**, not `gm.openrouter.create_client` alone |
| Import order | No module-level `from gm.orchestrator import Orchestrator` anywhere under `app/tests/**` |
| Workspace safety | Orchestrator fixture must not yield while `orchestrator.bridge` points at `play/workspace` |
| Teardown | `bridge` and `orchestrator` fixtures close `ctx.conn` on teardown |
| Out of scope | No edits to `app/gm/*`, no `pytest.ini`/CI pin, no behavioral tests |

### Test gates (WS1 done when all pass)

```bash
# From repo root — primary
python -m pytest app/tests -q

# Regression — engine suite unchanged
python -m pytest play/tomb_gm/tests -q

# Workspace pollution check (manual)
git status -- play/workspace
```

**Expected:** ≥1 test collected, exit 0; no new files under `play/workspace`.

### Post-impl (not WS1 — ticket release step)

- `tmp/app-logging-qa-spec.md` — checklist + changelog on `release APP-049 --done` only.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-049
ticket: tmp/backlog/app-049-create-app-tests-package.md
run-folder: tmp/backlog/runs/app-049-create-app-tests-package/
spec: spec.md | plan: plan.md | domain spec: tmp/app-logging-qa-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only. Follow plan.md implementation order. AGENTS.md: no ticket drift; do not edit domain spec during impl.
Run: python -m pytest app/tests -q && python -m pytest play/tomb_gm/tests -q from repo root.
Write reflection-dev-impl-WS1.md before return.
```
