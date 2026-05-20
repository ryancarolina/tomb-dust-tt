# Dev reflection: APP-049 WS1 implementation

**Ticket:** APP-049  
**Stream:** WS1 — app/tests pytest scaffold  
**Date:** 2026-05-20

## Files created

| File | Purpose |
|------|---------|
| `app/tests/__init__.py` | Package marker |
| `app/tests/helpers.py` | `REPO = parents[2]`, `APP`/`PLAY`/`BUILD`, `make_isolated_workspace` |
| `app/tests/conftest.py` | sys.path setup + five fixtures |
| `app/tests/test_smoke.py` | `test_bridge_status_after_init` |

## Implementation notes

1. **`helpers.py` path depth:** Used `parents[2]` (not engine `parents[3]`). Added `APP = REPO / "app"` per spec.

2. **`conftest.py` sys.path:** Inserted `_TESTS_DIR` first (same pattern as engine conftest) so `from helpers import …` resolves when pytest cwd is repo root. Then inserted `REPO/app`, `REPO/play`, `REPO/build/tools`.

3. **Fixtures delivered:** `isolated_workspace`, `bridge` (init + conn close), `app_config` (yaml from `app/config.yaml`), `mock_openrouter_client` (patches `gm.orchestrator.create_client`), `orchestrator` (GameBridge factory monkeypatch + lazy Orchestrator import + workspace assert + teardown close).

4. **Import-order rule:** No module-level `gm.orchestrator` imports in any test file; Orchestrator imported only inside `orchestrator` fixture body after patches.

5. **Deviation:** Added `_TESTS_DIR` to `sys.path` before `helpers` import — required for collection (engine conftest does the same). Not explicitly in plan text but implied by R2 “conftest loads before collection.”

## Pytest results

```text
python -m pytest app/tests -q
→ 1 passed in 0.09s — PASS

python -m pytest play/tomb_gm/tests -q
→ 134 passed, 1 skipped, 1 failed — FAIL (pre-existing)
```

**Engine failure (unrelated to APP-049):** `play/tomb_gm/tests/test_foundation.py::test_init_status_check_suggest` — expects `check` to fail in SETUP (`expect_ok=False`) but CLI now returns `{'ok': True, 'blocked': False, ...}`. Reproduces in isolation; no `app/tests` or production code touched by this ticket.

**Workspace pollution:** `git status -- play/workspace` unchanged by app/tests run.

## Self-check vs acceptance

| Req | Status |
|-----|--------|
| R1 Package layout | Done |
| R2 sys.path from repo root | Done (verified via smoke test imports) |
| R3 All five fixtures + import-order + workspace safety | Done |
| R4 Smoke test + pytest exit 0 for app/tests | Done |
| Engine regression green | **Blocked by pre-existing foundation test failure** |

## Handoff

- APP-057 can add `test_creation_flow.py` using `orchestrator` fixture.
- APP-051 can extend mock LLM stub helpers.
- Domain spec changelog deferred to ticket release per plan.
