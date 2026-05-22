# Drift Check: APP-034-log-tool-chain-on-api-errors

**backlog_ticket:** APP-034  
**Verdict:** PASS (synced)

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § API error logging (APP-034) | was minor (open work still listed APP-034) | **Synced:** removed APP-034 from open-work line; APP-032 § Observability notes `transcript_400_retry` shipped in APP-034 |
| Run [`spec.md`](./spec.md) R1–R6 | no | Verified against `logger.py`, `orchestrator.py`, `test_api_error_logging.py` |
| [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) JSONL table | was minor (missing `api_error` / `transcript_400_retry`) | **Synced:** event rows + changelog entry |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Priority table unchanged; APP-034 behavior owned by orchestrator spec |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| `redact_secrets` — recursive; sk-or / Bearer / secret keys; never raises | `logger.py` L124–149; U1–U3 | yes |
| `summarize_messages_for_log` — previews capped 200/120; non-mutating | L152–202; U4 | yes |
| `extract_tool_chain` — ordered assistant/tool rounds | L205–240; U5 | yes |
| `log_api_error` → JSONL `api_error` with required payload keys | L243–244, `_emit_api_error` L1287–1305; I1–I2, I9 | yes |
| `_chat_completion` canonical intercept — attempt 1 non-retryable + attempt 2 exhaustion | L1331–1369 | yes |
| Malformed 400 retry success → no `api_error`; optional `transcript_400_retry` | L1344–1351; I3 | yes |
| Six `context` call sites + `depth` on tool loops | `narrate_flavor`, `narrate_only`, `creation_llm_loop`, `combat_tools`, `combat_narrate`, `llm_loop` | yes |
| Combat silent-gap fix — `api_error` without caller `log_error` | I6, I7 | yes |
| Duplicate API-path `log_error` removed — wrapper canonical | I8; no `log_error("chat_completion")` in orchestrator | yes |
| Logger IOError swallowed; API exception propagates | `_emit_api_error` try/except; I5 | yes |

## Run spec R1–R6 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | `redact_secrets` never raises | ✓ |
| **R2** | Summarize + extract helpers; preview caps | ✓ |
| **R3** | `log_api_error` required keys | ✓ |
| **R4** | Wire in `_chat_completion`; six contexts; dedupe | ✓ |
| **R5** | Combat wrapper logging | ✓ |
| **R6** | Optional `transcript_400_retry` | ✓ (shipped) |

## Spec test matrix → pytest

| Spec case | Test | Result |
|-----------|------|--------|
| OpenRouter key redaction | `test_redact_secrets_openrouter_key` | ✓ |
| Bearer redaction | `test_redact_secrets_bearer` | ✓ |
| Nested dict redaction | `test_redact_secrets_nested_dict` | ✓ |
| Message summary tool_calls | `test_summarize_messages_tool_calls` | ✓ |
| Multi-round tool chain order | `test_extract_tool_chain_order` | ✓ |
| Unrelated 400 → one `api_error` attempt 1 | `test_log_api_error_on_unrelated_400` | ✓ |
| Malformed 400 ×2 → attempt 2 + truncated | `test_log_api_error_malformed_400_twice` | ✓ |
| Malformed 400 then success → retry marker only | `test_malformed_400_retry_success_no_api_error` | ✓ |
| Context + depth forwarded | `test_chat_completion_passes_context_depth` | ✓ |
| Logger never raises | `test_logger_never_raises` | ✓ |
| Combat tools failure logged | `test_combat_tools_failure_logged` | ✓ |
| Combat narrate failure logged | `test_combat_narrate_failure_logged` | ✓ |
| No duplicate `log_error` on API fail | `test_no_duplicate_log_error_on_llm_loop_fail` | ✓ |
| Tool chain on 400 with tools | `test_tool_chain_on_400_with_tools` | ✓ |
| APP-032 regression | `test_transcript_400_retry.py` (19 tests) | ✓ |
| APP-031 regression | `test_transcript_sanitize.py` (12 tests) | ✓ |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| `_chat_completion` emits JSONL `api_error` on every API failure (after retry exhaustion or non-retryable re-raise) | ✓ |
| Payload includes redacted in-turn tool-chain snapshot (`messages_summary`, `tool_chain`) | ✓ |
| `logger.py` implements `redact_secrets`, summarize/extract helpers — no raw API keys in JSONL | ✓ |
| Combat API failures logged (fixes silent `_combat_llm_loop_inner` gap) | ✓ |
| Optional: `transcript_400_retry` info event when malformed-transcript 400 retry runs | ✓ |

## Tests run

```bash
cd app; python -m pytest tests/test_api_error_logging.py tests/test_transcript_400_retry.py tests/test_transcript_sanitize.py -q
```

**Result:** 45 passed (1.42s)

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [x] Domain spec open-work line synced (APP-034 removed)
- [x] `app-logging-qa-spec.md` JSONL table cross-synced
- [ ] `python tmp/backlog/claim_ticket.py release APP-034 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Pre-drift lag was documentation only: open-work line and logging spec JSONL table lagged checklist/changelog that already marked APP-034 done.
- APP-032 § Observability previously deferred `transcript_400_retry` to APP-034 — now implemented; APP-031 `transcript_sanitized` remains deferred (non-blocking).
- Working tree `orchestrator.py` may include batch hunks (APP-022, APP-026) — out of APP-034 scope; logging intercept verified in isolation.
- Redaction v1 is heuristic regex + preview caps — per domain spec boundary; not full PII scrub.
