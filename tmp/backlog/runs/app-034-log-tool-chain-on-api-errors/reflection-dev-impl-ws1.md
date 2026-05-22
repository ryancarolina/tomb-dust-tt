# Dev reflection — APP-034 implementation (ws1)

**backlog_ticket:** APP-034  
**Round:** implementation  
**Date:** 2026-05-22

## What shipped

- **`app/gm/logger.py`:** `REDACTED`, `redact_secrets`, `summarize_messages_for_log`, `extract_tool_chain`, `log_api_error`, `log_transcript_400_retry` (R1–R3, R6).
- **`app/gm/orchestrator.py`:** `Orchestrator._emit_api_error` (instance method; try/except around `log_api_error` so logging never masks API re-raise); extended `_chat_completion` with `context`/`depth` kwargs and failure intercept on both attempt 1 (non-retryable) and attempt 2 (retry exhaustion).
- **Six call sites wired:** `narrate_flavor`, `narrate_only`, `creation_llm_loop`, `combat_tools`, `combat_narrate`, `llm_loop`.
- **Removed duplicate caller `log_error`** on API failure paths: `narrate_flavor`, `narrate_only`, `creation_llm_loop`, legacy `chat_completion` in `_llm_loop`.
- **New tests:** `app/tests/test_api_error_logging.py` — U1–U5 unit + I1–I9 integration matrix (14 cases).

## Test results

```text
python -m pytest app/tests/test_api_error_logging.py -v
14 passed in 0.91s

python -m pytest app/tests/test_transcript_sanitize.py app/tests/test_transcript_400_retry.py -q
31 passed in 0.90s
```

## Deviations / notes

- **`_emit_api_error` defensive try/except:** Plan I5 patches `log_entry` to raise; wrap ensures `BadRequestError` still propagates even if logging infrastructure fails outside `log_entry`'s normal swallow.
- **R6 shipped:** `transcript_400_retry` emitted on malformed-400 retry entry (I3 asserts presence on success path).
- **I7 combat narrate:** Required stubs for `_execute_combat_action`, `_combat_auto_chain`, `_sync_combat_from_status` so narrate pass runs after successful tool dispatch — same pattern as `test_combat_failure_narration.py`.
- Domain spec checklist marked done; changelog entry appended.

## v1 limits

- Preview caps: 200 chars content, 120 chars tool arguments — full payloads not logged.
- `extract_tool_chain` orphan `tool` rows (no preceding assistant round) are skipped silently.
- `context` defaults to `"unknown"` when omitted — prod call sites now pass explicit values.

## Risks

- Log volume on repeated API failures — mitigated by preview caps and single `api_error` per failed `_chat_completion` invocation.
- Redaction regex heuristics may miss novel secret formats — OpenRouter key + Bearer + common dict keys only.

## APP-031/032 pairing

- Logs **`clean`** on attempt 1 and **`retry_clean`** on attempt 2 (what the provider rejected).
- Retry success emits optional `transcript_400_retry` only — no `api_error`.
- APP-032 retry mechanics unchanged; logging is side-effect only (regression green).
