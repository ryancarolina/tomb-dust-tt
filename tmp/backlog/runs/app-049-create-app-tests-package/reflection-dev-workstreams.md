# Reflection: Dev — APP-049 workstreams

**Agent:** Dev (workstreams phase)  
**Inputs:** `plan.md`, PASS `spec.md`, ticket, `reflection-dev-plan.md`  
**Deliverable:** `workstreams.md`

## Stream split decision

**Count: 1 (WS1 only).**

APP-049 is greenfield scaffolding under `app/tests/` with a strict dependency chain:

```text
helpers.py → conftest (sys.path + fixtures) → test_smoke.py
```

All four new files live in one package; `conftest.py` must exist before meaningful pytest runs; orchestrator fixtures extend the same `conftest.py` after smoke validates bridge path. No production modules change, so there is no parallel surface (e.g. no independent UI vs bridge work).

Considered but rejected:

| Candidate split | Why not parallel |
|-----------------|------------------|
| WS1 helpers + bridge fixtures / WS2 orchestrator fixtures | Same file (`conftest.py`); second half is ~40 LOC and shares monkeypatch scope |
| WS1 code / WS2 spec sync | Domain spec edit is **release-only** per plan — not an impl workstream |
| WS1 smoke / WS2 fixtures | Smoke is the verification gate for WS1; splitting would block pytest until both merge |

## WS1 file list

| File | Role |
|------|------|
| `app/tests/helpers.py` | Path constants + `make_isolated_workspace` |
| `app/tests/conftest.py` | sys.path, all five fixtures |
| `app/tests/test_smoke.py` | `test_bridge_status_after_init` |
| `app/tests/__init__.py` | Package marker |

**Excluded from WS1 impl:** `tmp/app-logging-qa-spec.md` (ticket close / `release --done`).

## Risks carried into impl

1. **Collection-time orchestrator import** — any module-level import in `conftest.py` or tests binds `create_client` before patch; impl must lazy-import inside fixtures only.
2. **GameBridge patch shape** — patched name on `gm.orchestrator.GameBridge` must be **callable** for `GameBridge()` in `Orchestrator.__init__`.
3. **REPO depth** — single wrong `parents[N]` breaks all imports; plan and WS1 table call out `parents[2]` explicitly.

## Handoff

**Ready for:** single Dev impl dispatch (WS1)  
**Impl agent:** follow `workstreams.md § WS1` order; run both pytest commands; write `reflection-dev-impl-WS1.md`; do not edit domain spec until release.
