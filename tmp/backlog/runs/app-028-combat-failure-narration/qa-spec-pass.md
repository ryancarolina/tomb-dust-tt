# QA PASS: spec — round 2

**Task:** app-028-combat-failure-narration  
**backlog_ticket:** APP-028  
**ticket_path:** [tmp/backlog/app-028-combat-tool-failure-narration.md](../../app-028-combat-tool-failure-narration.md)  
**Round:** 2 (re-review after `qa-spec-report-1.md`)  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| TICKET-001 | blocker | **Fixed** | Ticket Expected files: `orchestrator.py`, `app/tests/test_combat_failure_narration.py`, `tmp/app-combat-play-spec.md`; `spec.md` § Affected paths matches |
| SPEC-001 | blocker | **Fixed** | § R1 propagation contract: `_handle_combat_trigger` → `str \| None`, `_beat_combat_start_failure`, `_llm_loop` same-turn short-circuit; T1 unit + T2 E2E (`no second chat_completion`, player return only) |
| SPEC-002 | blocker | **Fixed** | T3–T7 cover all five exploration tools with per-tool `error` + banned fiction; domain § Tests T3–T7 mirror; parametrization note |
| SPEC-003 | blocker | **Fixed** | R4 requirement + T10 partial-failure `TOOL FAILED (combat_action)` before tool result; domain T10 |
| SPEC-004 | major | **Fixed** | Dual-channel explicit (tool JSON may stay `ok: true`; player channel = short-circuit return); T2 dual-channel note; domain § Beat-trigger L63–64 |
| SPEC-005 | minor | **Fixed** | Optional `test_all_failed_or_beat_failure_logs` / domain T11 for R8 `log_error` |

**Blocker count (round 2):** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-combat-play-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R8; T1–T10 required, T11 optional)
- [x] Code traces match repo (silent `_handle_combat_trigger` `-> None` L1906; `all_failed` + content append L1848–1854, L1999–2006 — spec defines target behavior)
- [x] AGENTS.md / canon compliance (orchestrator narration only; no mechanics drift)
- [x] Tests/commands listed (`app/tests/test_combat_failure_narration.py`, engine regression pair)
- [x] registry_gap false — combat-play domain spec owns § Combat tool failure narration
- [x] Ticket AC “all combat tools” mapped: exploration five (T3–T7) + combat inner `combat_action` / wrong tool (T8–T9)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability (all combat tools) | **PASS** | SPEC-002 resolved |
| Beat-trigger / grave-ghoul testability | **PASS** | SPEC-001, SPEC-004 resolved |
| Scope ⊆ Expected files | **PASS** | TICKET-001 resolved |
| Domain spec sync | **PASS** | r2 changelog; § APP-028 mirrors run spec R1–R8 + T1–T11 |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Enforce failure narration for **all** combat tools | R5 table; T3–T7 + T8–T9 | pytest | **PASS** |
| No success fiction on `ok: false` | R1–R6; T1–T10 | pytest + playtest hints | **PASS** |
| Spec sync on close | Expected files + changelog | process | **PASS** (intent) |

## Adversarial notes (non-blocking)

1. **Same-batch tool order** — Short-circuit runs after the full tool batch; a rare same-turn `process_beat` + `combat_attack` pair could execute `combat_attack` before return. Grave-ghoul path is typically beat-only; acceptable for APP-028 scope.
2. **`_beat_combat_start_failure` naming** — Illustrative per PM r2; observable contract is what tests assert (T2).
3. **T10 setup** — Partial ok vs depth-1 retry left flexible; pass criteria (`TOOL FAILED` system line before tool result) are sufficient for R4.
4. **`app-llm-orchestrator-spec.md`** — Cross-ref pointer only; not in Expected files (same defer as r1).
5. **Live code** — `_handle_combat_trigger` still `-> None` with silent failure; spec correctly describes **target** behavior for Dev impl.

## Summary

Round 1 blockers **TICKET-001**, **SPEC-001**, **SPEC-002**, and **SPEC-003** are fully addressed in ticket, `spec.md` (r2), and `tmp/app-combat-play-spec.md`. Majors/minors **SPEC-004** / **SPEC-005** included. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
