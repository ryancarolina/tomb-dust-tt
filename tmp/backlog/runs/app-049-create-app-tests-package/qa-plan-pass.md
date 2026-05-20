# QA PASS: plan

**Task:** APP-049-create-app-tests-package
**backlog_ticket:** APP-049
**ticket_path:** tmp/backlog/app-049-create-app-tests-package.md
**Round:** 1
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec/plan (`tmp/app-logging-qa-spec.md`)
- [x] Acceptance criteria testable (plan § Acceptance mapping ↔ spec R1–R4 ↔ ticket AC)
- [x] Code traces match repo (independent re-trace below)
- [x] AGENTS.md / canon compliance (scaffolding only; no production edits)
- [x] Tests/commands listed (`python -m pytest app/tests -q`, engine regression)
- [x] Plan files ⊆ ticket Expected files (four `app/tests/*` paths + domain spec on close only)
- [x] registry_gap false — plan defers domain spec changelog to release (matches ticket)

## Plan ↔ spec gates

| Gate | Result | Notes |
|------|--------|-------|
| Expected files scope | **PASS** | No planned edits outside ticket list; domain spec marked close-only |
| R1 package layout | **PASS** | `__init__.py`, `helpers.py` with `parents[2]`, `APP`, mirror `make_isolated_workspace` |
| R2 import paths | **PASS** | Inserts `REPO/app`, `REPO/play`, `REPO/build/tools` before `gm.*` / `tomb_gm.*` |
| R3 fixtures | **PASS** | All five fixtures; import-order rule; workspace safety preferred pattern |
| R4 smoke test | **PASS** | `test_bridge_status_after_init`; bridge-only; avoids collection exit 5 |

## Code trace verification (plan claims)

| Claim | Evidence | Match |
|-------|----------|-------|
| Engine `REPO` uses `parents[3]` | `play/tomb_gm/tests/helpers.py:8` | ✓ |
| App tests need `parents[2]` | `app/tests/` is `repo/app/tests` → two parents to repo root | ✓ |
| `main.py` omits `app/` on `sys.path` | `app/main.py:8-10` inserts `play/`, `build/tools/` only | ✓ |
| Patch `gm.orchestrator.create_client` | `app/gm/orchestrator.py:45` import bind; `:82` call in `__init__` | ✓ |
| Default `GameBridge()` → `play/workspace` | `app/gm/orchestrator.py:83`; `play/tomb_gm/config.py:12` `DEFAULT_WORKSPACE` | ✓ |
| Preferred fix: patch `gm.orchestrator.GameBridge` | `Orchestrator` uses module-level `GameBridge` name (`:9`, `:83`) | ✓ |
| Teardown via `ctx.conn.close()` | `app/gm/bridge.py:33` `CommandContext` on `bridge.ctx` | ✓ |
| `bridge.status()` includes `roster` list | `play/tomb_gm/cli/cmd_core.py:88-95` payload shape | ✓ |
| Engine conftest `helpers` import pattern | `play/tomb_gm/tests/conftest.py:16-20` inserts tests dir then `from helpers` | ✓ (plan notes pytest adds `app/tests`; optional explicit insert acceptable) |

## Implementation-step review

| Step | Verdict |
|------|---------|
| `helpers.py` depth + `make_isolated_workspace` copy | Correct; independent of engine import |
| `conftest.py` sys.path before lazy `gm` imports | Correct order |
| `mock_openrouter_client` → `gm.orchestrator.create_client` | Correct patch target |
| `orchestrator` GameBridge factory monkeypatch before lazy `Orchestrator` import | Correct preferred pattern; assert on `isolated_workspace` is sound |
| Minimum swap pattern documented as fallback only | Aligns with spec; residual risk noted |
| `test_smoke.py` bridge-only, no module-level `gm.orchestrator` | Correct |
| Implementation order (helpers → conftest core → smoke → orchestrator fixtures) | Sound; smoke gates before heavier fixtures |

## Findings

_None._

**Notes:** Dev may mirror engine conftest’s explicit `sys.path.insert(0, str(_TESTS_DIR))` before `from helpers import …` if collection ever fails to add `app/tests` — not required for PASS. `app_config` function scope matches domain spec “session or function” allowance.
