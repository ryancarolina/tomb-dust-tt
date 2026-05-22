# QA PASS: spec — round 2

**Task:** app-027-validate-monster-id-combat  
**backlog_ticket:** APP-027  
**ticket_path:** [tmp/backlog/app-027-validate-monster-id-at-combat-start.md](../../app-027-validate-monster-id-at-combat-start.md)  
**Round:** 2 (re-review after `qa-spec-report-1.md`)  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| TICKET-001 | blocker | **Fixed** | Ticket Expected files L24: `app/tests/test_combat_monster_validation.py`; run `spec.md` § Affected paths L77–78 mirrors; hooks allow V1–V8 |
| SPEC-001 | blocker | **Fixed** | V5 uses `_dispatch_like_llm_loop` (APP-080); domain § Validation layers L288, R3 L339: `validate_tool_args` in `_llm_loop` **before** `_execute_tool`; V6 intentionally uses `_execute_tool` for bridge R1 only |
| SPEC-002 | minor | **Fixed** | R1 engine-only: `spec.md` L41; domain § R1 L296–297 — import from `tomb_gm.services.simulation.combat`; no duplicate regex in `app/gm/` |
| SPEC-003 | minor | **Fixed** | V8 L382: unmocked `_llm_loop` integration with real `content_root`, `hollow-knight:1`; explicitly not satisfied by APP-028 T3 mocks |
| SPEC-004 | minor | **Fixed** | V9 → `play/tomb_gm/tests/test_validate_monster_specs.py`; CLI `test_simulation.py -k unknown_monster` demoted to optional regression (domain L392, run spec L62–63) |

**Blocker count (round 2):** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-combat-play-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (`app/gm/`, `play/tomb_gm/`, `app/tests/test_combat_monster_validation.py`)
- [x] Acceptance criteria testable (R1–R6; V1–V9; pytest commands in run spec + domain § Tests)
- [x] Code traces match repo (`validate_tool_args` absent for `start_combat` in `tool_args.py`; exploration `_llm_loop` L2573–2576; `_execute_tool("start_combat")` L2684–2685 direct bridge; `_dispatch_like_llm_loop` in `test_tool_args.py` L33–39; engine `load_monster_json` L30–33 error substring)
- [x] AGENTS.md / canon compliance (engine validation; bridge contract; no canon edits; APP-028 substring stability)
- [x] Tests/commands listed (three required pytest modules + optional CLI)
- [x] registry_gap false — combat-play domain spec owns § Monster id validation at combat start (APP-027)
- [x] Domain spec sync — § APP-027 mirrors run spec R1–R6, V1–V9; r2 changelog dated 2026-05-22

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | V5 wire + V8 integration defined |
| Code traces | **PASS** | Validation-layer table matches orchestrator architecture |
| Expected files ⊆ plan scope | **PASS** | TICKET-001 resolved; V9 covered by `play/tomb_gm/` glob |
| Wire / test design | **PASS** | SPEC-001 resolved — APP-080 dispatch pattern |
| Domain spec sync | **PASS** | PM r2 changelog; layered R1–R3 + tests V1–V9 |
| AGENTS.md drift policy | **PASS** | Behavior in domain spec; ticket AC minimal |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Validate monster specs at `start_combat` | R1–R4; V1–V5, V9 | pytest | **PASS** |
| Clear error (no fiction on unknown id) | R5 + APP-028 §; V1, V6–V8 | pytest + playtest hints | **PASS** |
| Spec sync on close | Ticket § Spec sync; domain § + changelog | process | **PASS** (draft stage) |

## Adversarial notes (non-blocking)

1. **Empty-list error string** — R1 step 1 allows `"monster_specs required"` or `"monster_specs must be non-empty"`; R3/V5 standardize on `monster_specs required`. Dev should use one stable string in both R1 and R3 for V3/V5 consistency.
2. **Domain § Tests intro** — L369 still mentions “or extend `test_combat_failure_narration.py`”; ticket and run spec mandate dedicated module — follow dedicated module.
3. **Optional `test_tool_args.py`** — Not in ticket Expected files; spec marks unit test optional and superseded by V5. Do not add unless ticket expanded.
4. **V4 happy path** — Deferrable to APP-030 per spec; AC does not require success-path test.
5. **`app-llm-orchestrator-spec.md`** — Cross-ref deferred per PM r2; combat-play spec is authoritative for APP-027.

## Summary

Round 1 blockers **TICKET-001** and **SPEC-001** and minors **SPEC-002**–**SPEC-004** are fully addressed in ticket Expected files, `spec.md` (PM r2), and `tmp/app-combat-play-spec.md`. Layered validation (R3 tool args → R2 bridge → engine defense-in-depth), test wiring via `_dispatch_like_llm_loop`, and V8/V9 split are implementation-ready. Proceed to Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
