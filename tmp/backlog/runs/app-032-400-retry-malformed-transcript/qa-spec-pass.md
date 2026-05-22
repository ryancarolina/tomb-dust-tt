# QA PASS: spec

**Task:** app-032-400-retry-malformed-transcript  
**backlog_ticket:** APP-032  
**ticket_path:** [tmp/backlog/app-032-400-retry-on-malformed-transcript.md](../../app-032-400-retry-on-malformed-transcript.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-llm-orchestrator-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R5, ticket AC, seven pytest rows + APP-031 regression)
- [x] Code traces match repo (`_chat_completion` L1174–1192 sanitize-only; six call sites; no `is_malformed_transcript_400` / retry yet)
- [x] AGENTS.md / drift policy — behavior in domain spec; orchestrator-only scope; no canon drift
- [x] Tests/commands listed (`test_transcript_400_retry.py`, `test_transcript_sanitize.py`, full `tests/`)
- [x] registry_gap false — LLM orchestrator domain spec owns § Reactive 400 retry (APP-032)
- [x] APP-031 pairing clear (031 prevent → 032 recover; shared `sanitize_transcript_messages` + `_safe_prefix_fallback`)
- [x] Run spec ↔ domain spec synced (detection, retry pipeline, wire point, test matrix, changelog 2026-05-22)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| Domain spec present / synced | **PASS** | § Reactive 400 retry (APP-032); checklist open item + changelog |
| Run spec ↔ domain spec | **PASS** | R1–R4 mirrored in domain § Detection, Retry pipeline, Tests |
| AC testability | **PASS** | Ticket AC → R2 retry pipeline + pytest matrix |
| Code traces | **PASS** | `_chat_completion` intercept; `_llm_loop` GM-falters fallback at L2343–2347 |
| Expected files ⊆ plan scope | **PASS** | Ticket lists `orchestrator.py` + `test_transcript_400_retry.py` |
| APP-031 boundary | **PASS** | Non-goals exclude proactive sanitize duplication; shared primitives only |
| TurnTruth / narration gate | **PASS** | N/A — API transcript layer only |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| On malformed transcript 400, repair/truncate history and retry once | R1 detection; R2 truncate via `_safe_prefix_fallback` → sanitize → one retry; domain § Retry pipeline | Yes — unit + `_llm_loop` integration | **PASS** |
| Land tests proving AC | `test_transcript_400_retry.py` (7 rows) | Yes — in ticket Expected files | **PASS** |
| (Process) spec sync on close | Domain § + changelog; ticket § Spec sync | Process | **PASS** |

## Scope gate

Run `spec.md` § Affected paths vs ticket **Expected files**:

| Path | Ticket | Run spec |
|------|--------|----------|
| `app/gm/orchestrator.py` | ✓ | ✓ |
| `app/tests/test_transcript_400_retry.py` | ✓ | ✓ |
| `tmp/app-llm-orchestrator-spec.md` | close sync only | ✓ (exempt from hooks) |

## Adversarial notes (non-blocking)

1. **Caller list not repaired in-place** — R2/R4 and domain § Non-mutating preserve APP-031 contract; research flags depth N+1 may re-400 if malformed tail remains. Acceptable v1 safety net vs hard fail; Dev plan should not widen scope without PM ticket.
2. **Detection heuristic brittleness** — R1 substring list may miss novel provider wordings; negative 400 fixtures + APP-034 telemetry deferral are sufficient for spec stage.
3. **R5 observability** — `transcript_400_retry` JSONL optional/deferred to APP-034; not blocking close.
4. **Third substring wording** — R1 “`tool_call` / `tool_calls` in message” applies to `str(exc)` per domain § Detection; Dev may add parametrize fixture with/without those tokens in exception text.

## Summary

Run `spec.md` and domain § Reactive 400 retry (APP-032) are **implementation-ready**: narrow 400 detection, single intercept in `_chat_completion`, once-per-call retry budget, APP-031 primitive reuse, six wire points inherited, and a concrete pytest matrix. Ticket Expected files include the test module (APP-031 round-1 blocker avoided). Proceed to Dev plan + QA plan gates.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
