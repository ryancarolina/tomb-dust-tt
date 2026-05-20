# QA PASS: spec

**Task:** APP-049-create-app-tests-package
**backlog_ticket:** APP-049
**ticket_path:** tmp/backlog/app-049-create-app-tests-package.md
**Round:** 2
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-logging-qa-spec.md`)
- [x] Acceptance criteria testable (R1–R4 mapped ticket ↔ run spec ↔ domain spec)
- [x] registry_gap false — domain spec § App test package + § Fixture inventory present; no orphan spec
- [x] Tests/commands listed (`python -m pytest app/tests -q`, engine regression)
- [x] Round 1 remediations verified in actual files (see below)

## Round 1 remediation verification

| ID | Severity (R1) | Status | Evidence |
|----|---------------|--------|----------|
| **TICKET-001** | blocker | **Fixed** | Ticket AC expanded to R1–R4 with traceability link to `spec.md`; Expected files lists `helpers.py`, `conftest.py`, `test_smoke.py`, domain spec |
| **SPEC-001** | blocker | **Fixed** | `spec.md` R3 + domain spec § OpenRouter mock: patch `gm.orchestrator.create_client`; mandatory lazy-import / no module-level Orchestrator import |
| **SPEC-002** | blocker | **Fixed** | `spec.md` § Orchestrator fixture workspace safety + domain spec § Orchestrator fixture workspace safety: preferred GameBridge monkeypatch; minimum swap+close; forbidden yield on `play/workspace` |
| **SPEC-003** | major | **Fixed** | Explicit `REPO = Path(__file__).resolve().parents[2]` + `APP = REPO / "app"` in `spec.md` R1/R2, ticket R1/R2, domain spec helpers row |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Ticket AC ↔ run spec R1–R4 aligned |
| Registry/drift | **PASS** | `registry_gap: false`; domain spec draft synced |
| Adversarial | **PASS** | No new blockers; round 1 issues addressed |

## Code evidence (unchanged, re-confirmed)

| Claim | Evidence |
|-------|----------|
| `main.py` adds `play/` + `build/tools/`, not `app/` | `app/main.py:8-10` |
| `Orchestrator.__init__` binds `create_client` at import | `app/gm/orchestrator.py:45`, `:82` |
| Default `GameBridge()` in orchestrator | `app/gm/orchestrator.py:83` |
| Engine helpers use `parents[3]` | `play/tomb_gm/tests/helpers.py:8` |
| `app/tests/` absent (implementation pending) | glob 0 files |
| `_assert_not_play_workspace` exists | `play/tomb_gm/domain/session.py:52` |

## Findings (round 2)

_None._

**Notes:** Residual risk on minimum orchestrator pattern (brief `play/workspace` open before swap) is documented in run spec and PM reflection — acceptable for scaffolding; Dev should prefer GameBridge monkeypatch. `orchestrator` fixture may need explicit `monkeypatch` param if implementing preferred pattern (implementation detail, not spec blocker).
