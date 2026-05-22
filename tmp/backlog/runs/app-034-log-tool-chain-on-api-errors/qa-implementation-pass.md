# QA PASS: implementation — round 1

**Task:** app-034-log-tool-chain-on-api-errors  
**backlog_ticket:** APP-034  
**ticket_path:** [tmp/backlog/app-034-log-tool-chain-on-api-errors.md](../../app-034-log-tool-chain-on-api-errors.md)  
**Round:** 1  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) § API error logging (APP-034)

## Verdict

**PASS** — `_chat_completion` is the canonical `api_error` intercept with redacted `messages_summary` / `tool_chain`, six `context` call sites, combat silent-gap fix, optional `transcript_400_retry`, and full plan test matrix (U1–U5, I1–I9). Requested pytest green.

## Automated tests

```text
cd app && python -m pytest tests/test_api_error_logging.py tests/test_transcript_400_retry.py -v
33 passed in 1.43s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_api_error_logging.py` | 14 (U1–U5, I1–I9) | ✓ |
| `test_transcript_400_retry.py` | 19 (APP-032 regression) | ✓ |

## Diff scope reviewed

| Path | In ticket Expected files | APP-034-relevant change |
|------|--------------------------|-------------------------|
| `app/gm/logger.py` | ✓ | `REDACTED`, `redact_secrets`, `summarize_messages_for_log`, `extract_tool_chain`, `log_api_error`, `log_transcript_400_retry` |
| `app/gm/orchestrator.py` | ✓ | `_emit_api_error`, extended `_chat_completion` (attempt 1/2 logging + R6 retry info), `context`/`depth` at six sites, removed duplicate API-path `log_error` (4×) |
| `app/tests/test_api_error_logging.py` | ✓ | New module — full spec/plan matrix |

**Batch note:** Working tree `orchestrator.py` also contains **APP-022** (delve entry hint) and **APP-026** (`_gate_pc_attack`) hunks per [batch-board-APP-022-APP-026-APP-034.md](../batch-board-APP-022-APP-026-APP-034.md). Those are **out of APP-034 scope** but do not invalidate APP-034 logging behavior; Stage 7 should commit per ticket or split hunks.

**Close-stage (not impl-blocking):** `tmp/app-logging-qa-spec.md` JSONL table cross-sync for `api_error` / `transcript_400_retry` still pending per spec header.

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| `_chat_completion` emits JSONL `api_error` on every API failure (after retry exhaustion or non-retryable re-raise) | `_chat_completion` L1331–1342 (attempt 1 non-retryable); L1358–1369 (attempt 2 exhaustion); I1, I2, I3 | ✓ |
| Payload includes redacted in-turn tool-chain snapshot (`messages_summary`, `tool_chain`) | `_emit_api_error` L1297–1298; `log_api_error` applies `redact_secrets` on full payload; I9 | ✓ |
| `logger.py` implements `redact_secrets`, summarize/extract helpers — no raw API keys in JSONL | R1 helpers L124–247; U1–U3 | ✓ |
| Combat API failures logged (fixes silent `_combat_llm_loop_inner` gap) | `context="combat_tools"` + `depth` L2362–2368; `context="combat_narrate"` L2445–2449; I6, I7 | ✓ |
| Optional: `transcript_400_retry` when malformed-400 retry runs | L1344–1351 before second attempt; I3 asserts presence on success path | ✓ (R6 shipped) |

## Run spec R1–R6 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | `redact_secrets` never raises; sk-or / Bearer / secret keys | `logger.py` L128–149; U1–U3 | ✓ |
| **R2** | `summarize_messages_for_log`, `extract_tool_chain`; preview caps 200/120 | L152–240; U4, U5 | ✓ |
| **R3** | `log_api_error` → type `api_error` with required keys | L243–244; `_emit_api_error` payload; I1–I2 | ✓ |
| **R4** | Wire in `_chat_completion`; six contexts; dedupe `log_error` | Six sites verified; I8; legacy `log_error("chat_completion")` removed from `_llm_loop` | ✓ |
| **R5** | Combat wrapper logging without caller `log_error` | I6, I7 — no combat API `log_error` added | ✓ |
| **R6** | Optional `transcript_400_retry` | L1344–1351; I3 | ✓ |

## Plan test matrix → pytest

| Test ID | Name | Result |
|---------|------|--------|
| U1 | `test_redact_secrets_openrouter_key` | ✓ |
| U2 | `test_redact_secrets_bearer` | ✓ |
| U3 | `test_redact_secrets_nested_dict` | ✓ |
| U4 | `test_summarize_messages_tool_calls` | ✓ |
| U5 | `test_extract_tool_chain_order` | ✓ |
| I1 | `test_log_api_error_on_unrelated_400` | ✓ |
| I2 | `test_log_api_error_malformed_400_twice` | ✓ |
| I3 | `test_malformed_400_retry_success_no_api_error` | ✓ |
| I4 | `test_chat_completion_passes_context_depth` | ✓ |
| I5 | `test_logger_never_raises` | ✓ |
| I6 | `test_combat_tools_failure_logged` | ✓ |
| I7 | `test_combat_narrate_failure_logged` | ✓ |
| I8 | `test_no_duplicate_log_error_on_llm_loop_fail` | ✓ |
| I9 | `test_tool_chain_on_400_with_tools` | ✓ |

## QA spec adversarial notes — resolution

| Note (spec round 1) | Impl round 1 |
|---------------------|--------------|
| Missing `combat_narrate` test | **Resolved** — I7 `test_combat_narrate_failure_logged` |
| Duplicate `log_error` removal not enumerated | **Resolved** — four API-path removals; I8 guards `chat_completion` context |
| `app-logging-qa-spec.md` JSONL table | **Deferred** — Stage 6 drift / close |

## Adversarial notes (non-blocking)

1. **`_emit_api_error` double guard** — try/except around `log_api_error` in addition to `log_entry` swallow; defensive vs plan I5 (patch `log_entry` only) — acceptable.
2. **Batch orchestrator diff** — APP-022/026 hunks coexist; APP-034 review isolated to logging intercept + call-site kwargs; sequential Stage 7 commits recommended.
3. **Ticket / domain close** — Domain spec changelog marks APP-034 done; backlog ticket still `in_progress` and AC checkboxes unchecked until `release APP-034 --done`.
4. **Redaction v1 limits** — heuristic regex only; full tool payloads not logged (preview caps) — per spec.

## Handoff

**Ready for:** Stage 6 drift check + `release APP-034 --done` (ticket AC checkboxes, `app-logging-qa-spec.md` cross-sync).  
**Batch:** Coordinate APP-022 / APP-026 impl QA and per-ticket commits on shared `orchestrator.py`.
