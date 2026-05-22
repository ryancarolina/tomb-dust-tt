# QA PASS: implementation — round 1

**Task:** app-032-400-retry-malformed-transcript  
**backlog_ticket:** APP-032  
**ticket_path:** [tmp/backlog/app-032-400-retry-on-malformed-transcript.md](../../app-032-400-retry-on-malformed-transcript.md)  
**Round:** 1  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) § Reactive 400 retry (APP-032)

## Verdict

**PASS** — `is_malformed_transcript_400` and `_chat_completion` retry wrapper match ticket AC, run `spec.md` R1–R5, and plan test matrix R1–R7. Targeted pytest (APP-032 + APP-031 regression) green.

## Automated tests

```text
python -m pytest app/tests/test_transcript_400_retry.py app/tests/test_transcript_sanitize.py -v
31 passed in 0.93s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_transcript_400_retry.py` | 19 (R1–R7 matrix) | ✓ |
| `test_transcript_sanitize.py` | 12 (APP-031 regression) | ✓ |

## Diff scope reviewed

| Path | In ticket Expected files | Change |
|------|--------------------------|--------|
| `app/gm/orchestrator.py` | ✓ | `is_malformed_transcript_400`, `_MALFORMED_TRANSCRIPT_MARKERS`, `_chat_completion` try/retry wrapper |
| `app/tests/test_transcript_400_retry.py` | ✓ | New module — full R1–R7 matrix |

**Out of scope (confirmed):** No edits to `openrouter.py`, caller loops, or in-place caller `messages` repair. No `transcript_400_retry` JSONL (R5 deferred to APP-034).

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| On malformed transcript 400, repair/truncate history and retry once | `_chat_completion` L1219–1228: malformed 400 → `_safe_prefix_fallback(messages)` (caller original) → `sanitize_transcript_messages` → second `chat_completion`; exactly one retry budget | ✓ |
| Land tests proving AC | `test_transcript_400_retry.py` — 7 named scenarios + 12 R1 parametrize cases | ✓ |

## Run spec R1–R5 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Narrow `is_malformed_transcript_400`; never raises | L314–336: `BadRequestError` / `APIStatusError` + `status_code == 400`; marker tuple + compound third substring; broad `except` → `False` | ✓ |
| **R2** | Retry pipeline in `_chat_completion` | Proactive sanitize first (L1210); re-raise unrelated exceptions (L1222–1223); truncate from **caller** `messages` not `clean` (L1224); kwargs preserved via `cc_kwargs` merge (L1226–1228) | ✓ |
| **R3** | APP-031 pairing — no duplicate repair | Reuses `sanitize_transcript_messages` + `_safe_prefix_fallback`; no forked copies | ✓ |
| **R4** | Caller behavior unchanged | No edits at six call sites; successful retry returns normal dict; double-400 propagates to existing fallbacks (`test_malformed_400_twice_propagates`, `test_llm_loop_depth1_retry_integration`) | ✓ |
| **R5** | Optional `transcript_400_retry` JSONL | Not implemented — deferred to APP-034 per spec/plan | deferred |

## Plan test matrix → pytest

| Test ID | Name | Result |
|---------|------|--------|
| R1 | `test_is_malformed_transcript_400_cases` (12 parametrize) | ✓ |
| R2 | `test_malformed_400_then_success` | ✓ |
| R3 | `test_unrelated_400_no_retry` | ✓ |
| R4 | `test_malformed_400_twice_propagates` | ✓ |
| R5 | `test_non_400_no_retry` (429 + connection) | ✓ |
| R6 | `test_caller_messages_unchanged_after_retry` | ✓ |
| R7 | `test_llm_loop_depth1_retry_integration` | ✓ |

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| Malformed 400 → safe prefix retry | Holt-shaped array: 1st call sanitized full chain 400s; 2nd call gets system+user only via `_safe_prefix_fallback` + sanitize | R2 |
| Unrelated 400 fast-fail | `invalid model` → single attempt, re-raise | R3 |
| Non-400 no retry | `RateLimitError`, `APIConnectionError` → single attempt | R5 |
| Non-mutating contract | Caller list length, dict identity, inner `tool_calls` unchanged after successful retry | R6 |
| Exploration turn recovery | `_llm_loop` depth ≥1: tool call → malformed 400 → retry → `"Narration."` without `"The GM falters"` | R7 |
| APP-031 regression | All 12 `test_transcript_sanitize.py` cases still pass | ✓ |

## Adversarial notes (non-blocking)

1. **R5 observability** — No `transcript_400_retry` JSONL; explicitly deferred to APP-034.
2. **Caller list not repaired in-place** — Documented v1 limit; depth N+1 may re-400 with independent per-call retry budget. Matches spec non-goals.
3. **Detection heuristic brittleness** — Substring list may miss novel provider wordings; negative fixtures + narrow scope acceptable for v1.
4. **Import placement** — `BadRequestError` / `APIStatusError` import inserted mid-block in `orchestrator.py` (style only; no behavior impact).
5. **Ticket close pending** — Domain spec changelog already drafts “APP-032 done”; ticket still `in_progress` until Stage 6 drift + `release APP-032 --done`.

## Handoff

**Ready for:** Stage 6 drift check + `release APP-032 --done` (ticket AC checkbox, Closed date, confirm domain spec checklist).  
**Adjacent:** APP-034 may add `transcript_400_retry` / `transcript_sanitized` JSONL on retry path.
