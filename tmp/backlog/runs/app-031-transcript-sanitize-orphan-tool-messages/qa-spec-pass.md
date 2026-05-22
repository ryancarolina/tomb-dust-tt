# QA PASS: spec — round 2

**Task:** app-031-transcript-sanitize-orphan-tool-messages  
**backlog_ticket:** APP-031  
**ticket_path:** [tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md](../../app-031-transcript-sanitize-orphan-tool-messages.md)  
**Round:** 2 (re-review after `qa-spec-report-1.md`)  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| TICKET-001 | blocker | **Fixed** | Ticket Expected files: `app/gm/orchestrator.py`, `app/tests/test_transcript_sanitize.py`; run `spec.md` § Affected paths aligned; deferral footnote removed |
| SPEC-001 | major | **Fixed** | R1 safe-prefix fallback algorithm pinned (leading `system` + last `user`, else `[]`); edge cases explicit; `test_tail_invalid_returns_safe_prefix` in run + domain test matrices; domain § Helper contract + Invariants row |
| SPEC-002 | minor | **Fixed** | R1 non-mutating contract (new list, shallow-copy dicts); optional in-place wording removed; `test_sanitize_does_not_mutate_caller_list` in run + domain § Tests |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-llm-orchestrator-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R6, ticket AC, ten pytest rows)
- [x] Code traces unchanged from round 1 (six `chat_completion` sites; APP-028 system-before-tool reorder at ~L2276–2287 / ~L2091–2098)
- [x] AGENTS.md / drift policy — behavior in domain spec; orchestrator-only scope; no canon drift
- [x] Tests/commands listed (`test_transcript_sanitize.py`, full `tests/` regression)
- [x] registry_gap false — LLM orchestrator domain spec owns § Transcript sanitize (APP-031)
- [x] APP-032 boundary clear (031 prevent → 032 recover; shared `sanitize_transcript_messages`; no 400 retry in 031)
- [x] Run spec ↔ domain spec synced (Helper contract, invariants, wire points, test rows, r2 changelog)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| Domain spec present / synced | **PASS** | § Transcript sanitize (APP-031); checklist + r2 changelog |
| Run spec ↔ domain spec | **PASS** | R1 fallback + mutability mirrored |
| AC testability | **PASS** | Ticket AC → R2 invariants + pytest matrix |
| Code traces | **PASS** | Six call sites; no sanitizer today (expected pre-impl) |
| Expected files ⊆ plan scope | **PASS** | TICKET-001 resolved |
| APP-032 boundary | **PASS** | Unchanged from round 1 — clear pairing |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Sanitize transcript: no orphan tool messages without preceding `tool_calls` | R2 invariants; domain § Invariants; R4 wire all six call sites | Yes — unit + mock `_llm_loop` | **PASS** |
| Land tests proving AC | `test_transcript_sanitize.py` (10 rows) | Yes — hooks allow `app/tests/` | **PASS** |
| (Process) spec sync on close | Domain § + changelog 2026-05-22 r2 | Process | **PASS** |

## Adversarial notes (non-blocking)

1. **Holt fixture naming** — Run spec names `test_holt_session_shape`; domain § Tests references Holt fixtures in prose note only. Dev plan should keep the named case; domain table is sufficient for behavior.
2. **Safe-prefix excludes last assistant** — PM r2 explicitly defers including content-only assistant in fallback (APP-032 contract). Acceptable for v1; escalate human only if 032 truncate path needs assistant tail.
3. **R5 observability** — Optional/deferred to APP-034; not a round-1 finding; not blocking spec gate.
4. **Algorithm detail** — Full walk/reorder steps still deferred to Dev impl; invariants + test fixtures are enough for plan phase.

## Summary

Round 1 blocker **TICKET-001** and non-blocking **SPEC-001** / **SPEC-002** are fully addressed in ticket, run `spec.md` (PM r2 changelog), and `tmp/app-llm-orchestrator-spec.md` § Transcript sanitize. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
