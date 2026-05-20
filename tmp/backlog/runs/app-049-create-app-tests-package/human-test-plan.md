# Human Playtest Plan: APP-049-create-app-tests-package

**backlog_ticket:** APP-049  
**Commit:** `dd28447` (or latest with APP-049 in message if rebased)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** Pytest scaffold only — no in-game behavior change. Manual play is optional regression sanity; **pytest from repo root is the primary gate.**

## Prerequisites

- [ ] Python 3.11+ with project deps installed (`pip install -r app/requirements.txt`; pytest available)
- [ ] Shell cwd = **repo root** (`ttTomb-Dust/`), not `app/`
- [ ] No API key required for pytest (tests use isolated `tmp_path` workspaces)
- [ ] Optional app launch: OpenRouter key in `app/.env` if exercising TC-3

## Test cases

### TC-1: App test suite runs from repo root (maps to R4)

**Goal:** `app/tests/` collects ≥1 test and exits 0 (avoids empty-collection exit code 5).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests -q` | Exit code **0**; at least **1 passed** | [ ] |
| 2 | Inspect output | Shows `test_smoke.py::test_bridge_status_after_init` (or equivalent smoke test) | [ ] |

**Failure signals:** Exit code 5 (no tests collected); import errors for `gm.*` or `tomb_gm.*`; traceback mentioning `play/workspace`.

### TC-2: Collection and import paths (maps to R1, R2)

**Goal:** Package layout and `conftest.py` sys.path setup work without `cd app`.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests --collect-only -q` | Exit code **0**; **1 test collected** | [ ] |
| 2 | Confirm files exist: `app/tests/__init__.py`, `helpers.py`, `conftest.py`, `test_smoke.py` | All four present | [ ] |
| 3 | (Optional) `python -c "import sys; sys.path.insert(0,'app/tests'); import conftest; import gm.bridge; import tomb_gm.config"` from repo root | No ImportError | [ ] |

**Failure signals:** `ModuleNotFoundError: gm` or `tomb_gm`; conftest not loading; `helpers.py` using wrong `parents[3]` depth.

### TC-3: Smoke test fixture contract (maps to R3, R4)

**Goal:** `bridge` fixture exercises isolated workspace + `GameBridge.init()` + `status()` shape.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_smoke.py -v` | `test_bridge_status_after_init` **PASSED** | [ ] |
| 2 | After run: `git status -- play/workspace` | No new/modified files under `play/workspace` from this test run | [ ] |

**Failure signals:** SQLite errors pointing at `play/workspace`; test fails on missing `roster` key in status dict.

### TC-4: Optional — PyGame app still launches (regression sanity)

**Goal:** Scaffold did not break the canonical player entry point.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback on startup | [ ] |
| 2 | Close window (Escape or quit) | Clean exit | [ ] |

**Failure signals:** Import/path errors at startup; crash before UI renders. **Skip if offline-only QA — not required for APP-049 sign-off.**

## Acceptance criteria sign-off

| AC | Criterion | Verified by | Pass |
|----|-----------|-------------|------|
| R1 | Package layout (`__init__.py`, `helpers.py`, `conftest` loads) | TC-2 | [ ] |
| R2 | Import paths from repo root (`gm.*`, `tomb_gm.*`) | TC-1, TC-2 | [ ] |
| R3 | Fixtures in `conftest.py` (isolated workspace, bridge, config, mocks) | TC-3 (smoke); full fixture set covered by pytest impl QA | [ ] |
| R4 | Smoke test + `pytest app/tests -q` exit 0 | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- APP-051 / APP-057 should add behavioral tests using `orchestrator` and `mock_openrouter_client` fixtures — no second conftest.
- Engine suite (`python -m pytest play/tomb_gm/tests -q`) is out of scope for APP-049 human gate; run separately if checking full repo health.
- CI gate (APP-050) will wire `python -m pytest app/tests -q` into documented local/CI workflow.
