# Drift check: APP-049 — app/tests package

**Date:** 2026-05-20  
**QA agent:** drift check + ticket close prep  
**Sources:** `app/tests/**`, [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md), ticket + run [`spec.md`](spec.md)

## Verdict

**No spec ↔ code drift.** Implementation matches domain spec § App test package, § Fixture inventory, and run spec R1–R4. No code or spec edits required beyond changelog / ticket close metadata.

## Gate run

```text
python -m pytest app/tests -q
.                                                                        [100%]
1 passed in 0.08s
```

Ad-hoc (repo root, cwd unchanged): `import gm.bridge` and `import tomb_gm.config` succeed with `REPO/app`, `REPO/play`, `REPO/build/tools` on `sys.path`.

## Requirement traceability

| Req | Spec / ticket | Code | Status |
|-----|---------------|------|--------|
| R1 | Package layout | `__init__.py`, `helpers.py`, `conftest.py` | PASS |
| R1a | `REPO = parents[2]`, `APP`, `PLAY`, `BUILD` | `helpers.py` L9–12 | PASS |
| R1b | `make_isolated_workspace` mirrors engine contract | `helpers.py` L15–24 (same `config.yaml` shape as engine) | PASS |
| R1c | `conftest` loads before collection | Module-level `sys.path` + fixture registration | PASS |
| R2 | Import paths at module level | `conftest.py` L18–21 (`APP`, `PLAY`, `BUILD/tools`) | PASS |
| R2b | `gm.bridge`, `tomb_gm.config` from repo root | Smoke test + ad-hoc import | PASS |
| R3 | `isolated_workspace` → `make_isolated_workspace(tmp_path)` | `conftest.py` L24–26 | PASS |
| R3 | `bridge` init + teardown close | `conftest.py` L28–36 | PASS |
| R3 | `app_config` loads `app/config.yaml` | `conftest.py` L39–42 (same as `main.load_config`) | PASS |
| R3 | `mock_openrouter_client` patches `gm.orchestrator.create_client` | `conftest.py` L69 | PASS |
| R3 | No module-level `Orchestrator` import in `app/tests/**` | Only lazy import inside `orchestrator` fixture L86 | PASS |
| R3 | `orchestrator` workspace-safe (GameBridge monkeypatch) | `conftest.py` L74–91 (preferred pattern) | PASS |
| R4 | Smoke test `test_bridge_status_after_init` | `test_smoke.py` | PASS |
| R4 | `status()` dict with `roster` list | `test_smoke.py` L7–9 | PASS |
| R4 | ≥1 test, exit 0 | pytest gate above | PASS |

## Non-blocking notes (not drift)

| Item | Note |
|------|------|
| `__init__.py` | One-line package comment; spec allows empty marker — acceptable. |
| `app_config` scope | Function-scoped; domain spec allows session or function. |
| `conftest` local `helpers` import | Inserts `app/tests` on `sys.path` so `from helpers import …` works; behavior matches spec paths. |
| `orchestrator` fixture | Not exercised by committed tests; fixture code reviewed + prior impl QA ephemeral run. APP-057 owns behavioral coverage. |
| Engine pytest | `play/tomb_gm/tests` may have unrelated failures; out of APP-049 AC. |

## Files updated by this drift pass

| File | Change |
|------|--------|
| `tmp/app-logging-qa-spec.md` | Changelog + task checklist APP-049 marked done |
| `tmp/backlog/app-049-create-app-tests-package.md` | AC `[x]`, Status `done`, Closed 2026-05-20 |
| `drift-check.md` | Created (this file) |
| `reflection-qa-drift.md` | Created |

**Not done here (orchestrator):** `python tmp/backlog/claim_ticket.py release APP-049 --done`

## app-master-spec.md

No registry or priority-table change required — APP-049 adds test scaffolding only; no new domain spec file or cross-spec behavior change.
