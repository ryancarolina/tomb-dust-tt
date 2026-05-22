# APP-034: Log tool chain on API errors

| Field | Value |
|-------|-------|
| **ID** | APP-034 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-20 |

## Summary

API errors hard to debug without tool call context.

## Acceptance criteria

- [x] `_chat_completion` emits JSONL `api_error` on every API failure (after APP-032 retry exhaustion or non-retryable re-raise).
- [x] Payload includes redacted in-turn tool-chain snapshot (`messages_summary`, `tool_chain`) for the failing attempt.
- [x] `logger.py` implements `redact_secrets`, summarize/extract helpers — no raw API keys in JSONL.
- [x] Combat API failures logged (fixes silent `_combat_llm_loop_inner` gap).
- [x] Optional: `transcript_400_retry` info event when malformed-transcript 400 retry runs (APP-032 deferral).

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/logger.py`
- `app/tests/test_api_error_logging.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-034-log-tool-chain-on-api-errors`

_Add implementation notes, blockers, or PR links here._
