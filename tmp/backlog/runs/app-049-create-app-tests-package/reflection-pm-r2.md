# Reflection: PM — APP-049 spec revision round 2

**Agent:** PM  
**Round:** 2 (QA spec round 1 remediation)  
**Inputs:** `qa-spec-report-1.md` (FAIL — TICKET-001, SPEC-001–003)  
**Deliverables:** `spec.md`, `tmp/backlog/app-049-create-app-tests-package.md`, `tmp/app-logging-qa-spec.md`, `reflection-pm-r2.md`

## Findings addressed

| ID | Fix |
|----|-----|
| **TICKET-001** | Expanded ticket AC into R1–R4 bullets mirroring run spec; Expected files lists `helpers.py`, `conftest.py`, `test_smoke.py`, domain spec; traceability link to `spec.md` |
| **SPEC-001** | `mock_openrouter_client` patches `gm.orchestrator.create_client`; mandatory import-order rule (no module-level Orchestrator import; lazy import after patch) in run spec R3 + domain spec |
| **SPEC-002** | New § Orchestrator fixture workspace safety in run spec; domain spec § Workspace safety + fixture row; preferred `monkeypatch` on `gm.orchestrator.GameBridge`, minimum swap+close teardown |
| **SPEC-003** | Explicit `REPO = Path(__file__).resolve().parents[2]` and `APP = REPO / "app"` in R1, ticket R1, helpers table row (contrast engine `parents[3]`) |

## Decisions retained

- Smoke test (`test_smoke.py`) remains in scope — ticket R4 now explicit.
- `helpers.py` required in ticket Expected files (was “optional/preferred” in R1 round 1).
- No `Orchestrator` constructor change (non-goal unchanged).

## Residual risk (documented, not blocking spec)

- Minimum orchestrator pattern (swap after `__init__`) may still briefly open `play/workspace` before teardown; Dev should prefer GameBridge monkeypatch when practical.
- Stub `OpenAI` response shape still behavior-level — Dev aligns with SDK objects; QA implementation pass should verify patch before `create_client()` in `__init__`.

## Handoff

**Ready for:** QA spec review round 2  
**Re-review focus:** per `qa-spec-report-1.md` § Re-review focus (ticket AC vs R1–R4, patch path, workspace wording, `parents[2]`)
