# QA Report: spec — round 1

**Task:** APP-049-create-app-tests-package
**backlog_ticket:** APP-049
**ticket_path:** tmp/backlog/app-049-create-app-tests-package.md
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)
**domain_spec_creation:** not_needed (registry_gap false; domain spec draft present)

## Findings

### TICKET-001 — blocker

- **Location:** `tmp/backlog/app-049-create-app-tests-package.md` § Acceptance criteria vs `spec.md` R1–R4
- **Issue:** Ticket AC is only “Create `app/tests/` package + conftest.” Spec adds mandatory `helpers.py`, `test_smoke.py`, and five fixtures (`bridge`, `app_config`, `mock_openrouter_client`, `orchestrator`, etc.). No traceability matrix or ticket update; a dev closing against the ticket alone can omit smoke test (pytest exit code 5) and downstream fixtures APP-057/APP-051 depend on.
- **Implementation gap:** Backlog gate “spec AC maps to ticket acceptance criteria” fails; drift between ticket checklist and domain spec / run spec.
- **Suggested fix:** Expand ticket AC bullets to match R1–R4 (or add “see domain spec § App test package”) and check off smoke + fixture inventory explicitly.

### SPEC-001 — blocker

- **Location:** `spec.md` R3 (`mock_openrouter_client`); `tmp/app-logging-qa-spec.md` § Fixture inventory (`mock_openrouter_client` row)
- **Issue:** Spec requires patching `gm.openrouter.create_client`, but `app/gm/orchestrator.py` binds at import time:

```45:45:app/gm/orchestrator.py
from gm.openrouter import create_client, chat_completion
```

```82:83:app/gm/orchestrator.py
        self.client = create_client()
        self.bridge = GameBridge()
```

  Patching only `gm.openrouter.create_client` does not affect `gm.orchestrator.create_client` after `gm.orchestrator` is imported. Any test module with top-level `from gm.orchestrator import Orchestrator` will still call the real client and raise without `OPENROUTER_API_KEY`.
- **Implementation gap:** `orchestrator` fixture requirement is untestable / flaky as written.
- **Suggested fix:** Require `monkeypatch.setattr("gm.orchestrator.create_client", …)` **or** mandate lazy import of `Orchestrator` inside the fixture after patch **and** forbid module-level orchestrator imports in `app/tests/**`. Document in domain spec fixture table.

### SPEC-002 — blocker

- **Location:** `spec.md` R3 (`orchestrator` fixture); research-brief “Workspace safety”
- **Issue:** Spec says post-init `orchestrator.bridge = GameBridge(workspace=isolated_workspace)` but omits that `Orchestrator.__init__` always runs `GameBridge()` first, which resolves to `play/workspace` (`play/tomb_gm/config.py` `DEFAULT_WORKSPACE`). `GameBridge.__init__` opens SQLite and runs migrations on that path; `_assert_not_play_workspace` only guards session **start**, not bridge construction.
- **Implementation gap:** Orchestrator fixture can touch player save DB before swap; contradicts “never uses `play/workspace`” (R3 / domain spec § Workspace safety).
- **Suggested fix:** Document in spec: (1) swap bridge immediately after construct before any orchestrator method; (2) optional teardown closes default bridge connection; (3) long-term constructor injection out of scope but note residual risk. Consider `monkeypatch` on `gm.orchestrator.GameBridge` for `__init__` only in orchestrator fixture (if in scope).

### SPEC-003 — major

- **Location:** `spec.md` R1 (helpers mirror); `play/tomb_gm/tests/helpers.py` vs proposed `app/tests/helpers.py`
- **Issue:** Engine helpers use `REPO = Path(__file__).resolve().parents[3]` (`play/tomb_gm/tests/helpers.py:8`). App tree is one level shallower; `app/tests/helpers.py` must use `parents[2]`. Spec says “mirror” but does not state depth — copy-paste yields wrong `REPO` and broken `make_isolated_workspace` content_root.
- **Implementation gap:** Silent wrong paths if Dev copies engine file verbatim.
- **Suggested fix:** Add explicit line in R1/R2: `REPO = Path(__file__).resolve().parents[2]` for `app/tests/*`; `APP = REPO / "app"`.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **FAIL** | TICKET-001 — AC / spec mismatch |
| Registry/drift | **PASS** | `registry_gap: false`; domain spec § App test package + fixture inventory drafted; no orphan spec |
| Adversarial | **FAIL** | SPEC-001–003 — mock target, workspace leak, REPO depth |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| `main.py` adds `play/` + `build/tools/`, not `app/` | `app/main.py:8-10` |
| `GameBridge(workspace=…)` + `status()` → `roster` list | `app/gm/bridge.py:28-37`; `play/tomb_gm/cli/cmd_core.py:95` |
| `create_client()` requires API key | `app/gm/openrouter.py:11-14` |
| Isolated workspace pattern exists | `play/tomb_gm/tests/helpers.py:18-29`, `conftest.py:23-25` |
| `app/tests/` absent | glob 0 files |

## Summary

Fix **TICKET-001** (align ticket AC with spec scope) and **SPEC-001** (monkeypatch target / import discipline) before Dev plan. Address **SPEC-002** (orchestrator default workspace) and **SPEC-003** (REPO `parents[2]`) in spec + domain spec fixture section.

## Re-review focus

- Updated ticket AC bullets vs R1–R4 checkboxes
- `mock_openrouter_client` patch path and import-order rule
- Orchestrator fixture workspace safety wording
- Explicit `parents[2]` for `app/tests/helpers.py`
