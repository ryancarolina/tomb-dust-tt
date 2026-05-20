# Research Brief: APP-049-create-app-tests-package

**Date:** 2026-05-20
**Question:** What scaffolding does `app/tests/` need so downstream app pytest tickets (APP-051, APP-057, APP-054) can run headless from repo root?

**backlog_ticket:** APP-049
**ticket_path:** tmp/backlog/app-049-create-app-tests-package.md
**domain_spec:** tmp/app-logging-qa-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) explicitly owns `app/gm/logger.py`, `app/logs/`, and **`app/tests/`** (file map line 74). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row "Logging & QA" matches. APP-049 is chore scaffolding under that owner — no new domain spec.

## Summary

`app/tests/` is absent. The logging-qa spec already defines the gate: `python -m pytest app/tests -q` plus tomb_gm and `validate_content.py`. There is no repo-level pytest config; `app/main.py` only prepends `play/` and `build/tools/` to `sys.path`, while `gm.*` imports require `app/` on the path. The engine's pytest guard refuses mutations to default `play/workspace`, so app tests must use an isolated tmp workspace like `play/tomb_gm/tests/conftest.py`. `Orchestrator` always constructs `GameBridge()` without a workspace arg and calls `create_client()` at init, so conftest must inject an isolated bridge and mock OpenRouter for any orchestrator-based test. APP-049 should deliver package + conftest only; behavioral tests belong to APP-057 (creation flow) and APP-051 (mock LLM golden path).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| App entry / path | `app/main.py` | Adds `ROOT/play`, `ROOT/build/tools`; `gm` via cwd `app/` |
| GameBridge | `app/gm/bridge.py` | `GameBridge(workspace=None)` → `resolve_workspace` → `play/workspace` |
| Orchestrator | `app/gm/orchestrator.py` | `create_client()` in `__init__`; `setup_new_game()` wipes via bridge |
| OpenRouter | `app/gm/openrouter.py` | Raises without `OPENROUTER_API_KEY` |
| JSONL logger | `app/gm/logger.py` | Writes `app/logs/session-YYYY-MM-DD.jsonl` |
| Engine workspace guard | `play/tomb_gm/domain/session.py` | `_assert_not_play_workspace` when `pytest` loaded |
| Engine test patterns | `play/tomb_gm/tests/conftest.py`, `helpers.py` | `isolated_workspace`, `make_isolated_workspace`, CLI fixtures |
| Creation unit tests (engine tree) | `play/tomb_gm/tests/test_creation_gating.py` | Imports `gm.creation` — needs `app/` on path |
| Domain spec gate | `tmp/app-logging-qa-spec.md` | Owns `app/tests/` + pytest commands |
| Downstream tickets | `tmp/backlog/app-057-*.md`, `app-051-*.md`, `app-054-*.md` | Tests/fixtures expected under `app/tests/` |

## Code-path traces

### Pytest discovery from repo root

1. Entry: `python -m pytest app/tests -q` (cwd = repo root)
2. Pytest loads `app/tests/conftest.py` (to be created) before collection
3. Conftest must insert `REPO/app`, `REPO/play`, `REPO/build/tools` into `sys.path` (mirror `main.py` + explicit `app/`)
4. Tests import `gm.*` and `tomb_gm.*` without `cd app`

### Safe bridge smoke (fixture target)

1. Entry: `isolated_workspace` fixture → `make_isolated_workspace(tmp_path)` (same pattern as `play/tomb_gm/tests/helpers.py`)
2. `GameBridge(workspace=isolated_workspace)` → `load_config` + SQLite in tmp `.local/memory.db`
3. `bridge.init()` / `bridge.status()` — no `play/workspace` touch; guard passes

### Orchestrator in tests (APP-057 / APP-051)

1. Entry: `Orchestrator(app_config)` — **blocked** without mock: `create_client()` needs API key
2. Conftest: `monkeypatch` `gm.openrouter.create_client` → dummy client
3. Conftest: after construct, `orchestrator.bridge = GameBridge(workspace=isolated_workspace)` (Orchestrator does not accept workspace today)
4. `process_turn("new game")` → `setup_new_game()` → `_creation_turn` → code-first FSM; `_narrate_flavor` calls `chat_completion` (mock or fallback string on error)
5. Exit: `bridge.status()["roster"]` non-empty after finalize (APP-057 AC)

## Existing specs & docs

- Ticket domain spec: `tmp/app-logging-qa-spec.md` — QA suite lists orchestrator, creation flow, bridge smoke, mock LLM golden path; gate commands at § Tests
- `tmp/app-character-creation-spec.md` — `python -m pytest app/tests/test_creation_flow.py -q` (when added)
- `tmp/app-llm-orchestrator-spec.md` — `app/tests/test_orchestrator.py` (when added)
- `tmp/app-gamebridge-spec.md` — golden JSON fixtures in `test_bridge.py` (when added)
- Prior runs note missing package: `app-002`, `app-003` research briefs

## Tests & commands

```bash
# After APP-049 (scaffold only — may collect 0 tests)
python -m pytest app/tests -q

# Full logging-qa gate (spec)
python -m pytest app/tests -q
python -m pytest play/tomb_gm/tests -q
python build/tools/validate_content.py

# Engine creation parsers (already exist; needs app on PYTHONPATH)
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

## Risks & unknowns

- `Orchestrator` hardcodes `GameBridge()` — injection via fixture is required until a constructor param lands (out of APP-049 scope if ticket stays `app/tests/` only).
- `play/tomb_gm/tests/test_creation_gating.py` imports `gm.*` — may fail from repo root unless developers always set path; app `conftest` could document exporting `PYTHONPATH=app:play` for engine tests (optional).
- `pytest` with zero tests exits code 5 — APP-054 may require at least one smoke test (`test_bridge_status`); APP-049 AC is only package + conftest.
- JSONL logger appends to real `app/logs/` during tests — consider `monkeypatch` `LOG_DIR` in later tickets if log pollution matters.
- `session_state.json` under `app/` — `setup_new_game` deletes it; isolated tests should not rely on developer save files.
- `pytest` not listed in `app/requirements.txt` — dev/CI dependency undocumented until APP-050.

## Raw notes

- Glob: 0 files under `app/tests/**`
- Glob: 0 `pytest.ini` / `pyproject.toml` at repo root
- Glob: 0 `.github/workflows/**`
- `DEFAULT_WORKSPACE` = `play/workspace` in `play/tomb_gm/config.py`
- `test_workspace_guard.py` asserts session start refuses `play/workspace` under pytest
- APP-057 Expected files include `conftest.py` — extend APP-049 conftest, do not fork
- APP-051 Expected files: `app/tests/` only (fixture module)
- APP-054: green suite gate on master spec release table
