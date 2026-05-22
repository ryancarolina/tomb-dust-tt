# Dev reflection — APP-032 implementation (ws1)

**backlog_ticket:** APP-032  
**Round:** implementation  
**Date:** 2026-05-22

## What shipped

- Module-level `is_malformed_transcript_400` + `_MALFORMED_TRANSCRIPT_MARKERS` in `app/gm/orchestrator.py` (placed after `sanitize_transcript_messages`, before `Orchestrator`).
- `Orchestrator._chat_completion` wrapped: proactive sanitize → attempt 1; on narrow malformed-transcript 400 → `_safe_prefix_fallback(caller messages)` → sanitize → attempt 2; unrelated/non-400 exceptions re-raise immediately.
- OpenAI imports: `BadRequestError`, `APIStatusError`.
- New test module `app/tests/test_transcript_400_retry.py` — full R1–R7 matrix; reuses `assert_transcript_invariants`, `_tool_call` from `test_transcript_sanitize.py`.

## Test results

```text
python -m pytest app/tests/test_transcript_400_retry.py app/tests/test_transcript_sanitize.py -v
31 passed in 0.90s
```

## Deviations / notes

- None from plan. `cc_kwargs` built once; second attempt overrides `messages` only (preserves positional `self.client` delegate shape).
- R1 includes one `APIStatusError` positive row per QA plan note #1.
- R5 `transcript_400_retry` JSONL deferred to APP-034 (per spec).
- Domain spec checklist marked done; changelog entry appended.

## v1 limits (documented)

- Caller `messages` list is **not repaired** after successful retry — loops keep appending to the original mutable array; depth N+1 may 400 again with an independent per-call retry budget.
- Truncate floor is leading `system` + last `user` only — drops entire in-turn tool chain (acceptable v1 vs hard fail).

## Risks

- Detection relies on provider error substring heuristics — false positive would truncate context; mitigated by narrow marker list + negative fixtures (invalid model, context_length, tool result messages without tool_call tokens).
- False negative leaves pre-APP-032 behavior (GM falters fallback) — unchanged from baseline.

## APP-031 pairing

- Attempt 1 still runs APP-031 proactive sanitize.
- Retry truncate uses **caller's original** array (not attempt-1 `clean`), then re-sanitizes — same primitives, no forked invariant logic.
