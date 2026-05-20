# QA Report: spec — round 1

**Task:** APP-071-friendly-load-no-save
**backlog_ticket:** APP-071
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` R1 (require `_emit_narration`); R2/R3 footers (`[Awaiting: new game]`, `[Awaiting: new game | continue creation]`); domain spec § Resume failure table; `tmp/app-logging-qa-spec.md` § `creation_drift`
- **Issue:** R1 mandates `_emit_narration(message)` on resume failure. `_emit_narration` always calls `_check_creation_drift` (`orchestrator.py` 286–288). Mid-creation failures fall under `_creation_drift_scope()` (`creation.active` or engine `CHARACTER_CREATION` + empty roster). Proposed chip footers use human phrases (`new game`, `continue creation`) that `parse_narration_status_line` will read as `Awaiting:` values, which **do not** match `CREATION_STATUS_LABELS[creation.step]` — logging spec expects `awaiting_mismatch` in that situation.
- **Implementation gap:** Implementing the spec as written will emit spurious `creation_drift` on every mid-creation `load game` failure, contradicting logging spec “Healthy golden path: No `creation_drift` on every turn solely because granular footer differs from engine `CHARACTER_CREATION`.”
- **Suggested fix:** Pick one explicit pattern in `spec.md` + domain § Resume failure:
  1. **Recovery emit helper:** e.g. `_emit_recovery_narration(msg)` → `log_gm_narration` only (no drift), still return `msg` to UI; **or**
  2. **R3 footer:** use `format_creation_status(self.creation)` inside brackets for chips (`[Awaiting: RACE_INPUT]` style) and put “type `new game` to wipe” in prose only; **or**
  3. **R5 fallback:** orchestrator prose without `Awaiting:` tokens + UI queues `("suggestions", ["new game", …])` on resume-failure (update ticket Expected files if required).
  Document branch: cold path may use `[Awaiting: new game]` when `_creation_drift_scope()` is false.

### SPEC-002 — major

- **Location:** `spec.md` R2 vs R3; no “evaluate R3 before R2” rule
- **Issue:** Overlapping predicates (`creation.active`, engine `CHARACTER_CREATION`, `creation.step`, `session_state.json`) without ordered decision tree. Dev could emit cold-path copy while `creation.active` is true or miss R3 when only engine status signals mid-creation.
- **Implementation gap:** AC “message distinguishes no save file vs unsaved in-progress creation” becomes flaky across desync cases.
- **Suggested fix:** Add § Message selection: test R3 signals first (any true → variant B), else R2. Mirror one row in domain spec table.

### TICKET-001 — major (non-blocking for spec gate if SPEC-001 fixed)

- **Location:** Ticket § Acceptance criteria item 4 vs `spec.md` R4 / Non-goals
- **Issue:** Ticket AC: “Extend APP-019 acceptance **or close together** with surfaced errors in **UI toast**.” Spec closes APP-071 via narration only and leaves APP-019 open (no toast). Reasonable PM interpretation, but ticket checkbox is not traceable to a closure criterion.
- **Suggested fix:** Add ticket note or AC bullet: “APP-071: narration + `gm_narration`; APP-019: toast channel — not bundled.” Or extend APP-019 AC with cross-reference only.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P1 bug; `in_progress`; domain spec matches ticket |
| registry_gap | **PASS** | false — session-persistence spec owns behavior |
| AC testability (R1–R3 core) | **PASS** | T1–T3 / T3a–T3c mappable |
| Drift / logging alignment | **FAIL** | SPEC-001 — `_emit_narration` + recovery footers |
| Code traces | **PASS** | Failure branch 444–448; `_emit_narration` 286–288; UI `narration_text` 300; `_extract_suggestions` 342–350 |
| Domain spec sync | **PASS** (content) | Mirrors run spec; shares SPEC-001 footer issue |
| Tests in Expected files | **WARN** | `test_session_resume_failure.py` recommended but not in ticket Expected files — extend before impl (PM noted) |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Player-facing narration; not silent | R1, R2, R3; domain § Resume failure | T1/T2, manual TC-A/B | **PASS** (intent) |
| JSONL `error` retained; optional player log | R1 → `_emit_narration` / `log_gm_narration`; no `log_player_message` | T3 | **FAIL** until SPEC-001 resolved |
| Distinguish no save vs mid-creation | R2 vs R3 | T2 vs T1 | **PASS** (intent); **WARN** branch order (SPEC-002) |
| APP-019 / toast | R4 non-goals | N/A for APP-071 | **WARN** TICKET-001 |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| Resume failure: `log_error` only, no `_emit_narration` | `orchestrator.py` 446–448 |
| Return still reaches panel | `ui/app.py` 292–300 |
| `_emit_narration` → drift | `orchestrator.py` 286–288, `_check_creation_drift` 201+ |
| Drift scope includes mid-creation | `orchestrator.py` 189–199 |
| Chips need bracket `Awaiting:` | `ui/app.py` 342–350 |
| `log_player_message` absent | `app/gm/logger.py` — no symbol |

## Summary

**FAIL** — fix **SPEC-001** (recovery narration vs `creation_drift`) before Dev plan. Address **SPEC-002** (R3-before-R2) and **TICKET-001** (APP-019/toast traceability) in the same PM revision. Re-review: updated R1 emit pattern, footer rules per variant, domain spec table, drift-free test assertion for T2.

## Re-review focus

- R1: explicit emit helper or drift-safe footer rules per R2/R3
- Ordered variant selection (R3 first)
- Domain spec + `spec.md` footers aligned with `app-logging-qa-spec.md` § `creation_drift`
- Optional: add `app/tests/test_session_resume_failure.py` to ticket Expected files
