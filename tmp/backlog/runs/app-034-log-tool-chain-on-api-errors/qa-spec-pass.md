# QA PASS: spec

**Task:** app-034-log-tool-chain-on-api-errors  
**backlog_ticket:** APP-034  
**ticket_path:** [tmp/backlog/app-034-log-tool-chain-on-api-errors.md](../../app-034-log-tool-chain-on-api-errors.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-llm-orchestrator-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (includes `test_api_error_logging.py` — no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R5 blocking; R6 optional; ticket AC → pytest matrix)
- [x] Code traces match repo (`_chat_completion` L1208–1236 APP-032 retry; six call sites; combat silent gap L2234–2235 / L2310–2313)
- [x] AGENTS.md / drift policy — behavior in domain spec; orchestrator + logger scope; no canon drift
- [x] Tests/commands listed (`test_api_error_logging.py`, APP-031/032 regression suite, full `tests/`)
- [x] registry_gap false — LLM orchestrator domain spec owns § API error logging (APP-034)
- [x] APP-031/032 pairing clear (sanitize + retry reduce failures; APP-034 observes residual + retry outcomes)
- [x] Run spec ↔ domain spec synced (helpers, payload schema, context enum, wire flow, test table, changelog 2026-05-22)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P2 feature; in_progress |
| registry_gap | **PASS** | false — orchestrator spec; logging-qa cross-sync on close noted |
| Domain spec present / synced | **PASS** | § API error logging (APP-034); checklist open item + changelog |
| Run spec ↔ domain spec | **PASS** | R1–R5 mirrored in domain § Redaction, `log_api_error`, Wire point, Tests |
| AC testability | **PASS** | Ticket AC → R1–R5 + 11 pytest rows |
| Code traces | **PASS** | Single intercept; six `_chat_completion` sites; combat no `log_error` on API fail |
| Expected files ⊆ plan scope | **PASS** | `orchestrator.py`, `logger.py`, `test_api_error_logging.py` |
| APP-031/032 boundary | **PASS** | Non-goals exclude sanitize/retry duplication; optional R6 consolidates APP-032 deferral |
| TurnTruth / narration gate | **PASS** | N/A — JSONL observability only; player fallbacks unchanged |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| `_chat_completion` emits JSONL `api_error` on every API failure (after retry exhaustion or non-retryable re-raise) | R3 `log_api_error`; R4 wire point; domain § Wire point | Yes — `test_log_api_error_on_unrelated_400`, malformed ×2, retry success | **PASS** |
| Payload includes redacted in-turn tool-chain snapshot (`messages_summary`, `tool_chain`) | R2 summarize/extract; R3 required keys; domain § Redaction | Yes — summarize/chain unit tests + 400 integration | **PASS** |
| `logger.py` implements `redact_secrets`, summarize/extract helpers — no raw API keys in JSONL | R1 redaction; R2 helpers | Yes — three redaction tests + `test_logger_never_raises` | **PASS** |
| Combat API failures logged (fixes silent `_combat_llm_loop_inner` gap) | R5; domain context `combat_tools` / `combat_narrate` | Yes — `test_combat_tools_failure_logged` | **PASS** |
| Optional: `transcript_400_retry` info when APP-032 retry runs | R6 non-blocking | Yes — `test_malformed_400_retry_success_no_api_error` | **PASS** |
| (Process) spec sync on close | Domain § + changelog; ticket § Spec sync; `app-logging-qa-spec.md` cross-sync | Process | **PASS** |

## Scope gate

Run `spec.md` § Affected paths vs ticket **Expected files**:

| Path | Ticket | Run spec |
|------|--------|----------|
| `app/gm/orchestrator.py` | ✓ | ✓ |
| `app/gm/logger.py` | ✓ | ✓ |
| `app/tests/test_api_error_logging.py` | ✓ | ✓ |
| `tmp/app-llm-orchestrator-spec.md` | close sync only | ✓ (exempt from hooks) |
| `tmp/app-logging-qa-spec.md` | close cross-sync | noted in spec header |

## Adversarial notes (non-blocking)

1. **`combat_narrate` test gap** — R5 requires `context="combat_narrate"` on narrate-only second pass failure; pytest matrix lists `test_combat_tools_failure_logged` only. Dev plan should add one row or parametrize combat contexts.
2. **Redaction regex detail** — R1 names patterns (`sk-or-`, `Bearer`, api_key keys) but not exact regex; test plan golden fixtures are sufficient for v1; Dev should not widen to full PII scrub without ticket amendment.
3. **Duplicate `log_error` removal** — R4 canonical-wrapper policy does not enumerate which three exploration/creation/narration call sites drop duplicate rows; Dev plan should list them explicitly to avoid double JSONL noise.
4. **`app-logging-qa-spec.md` JSONL table** — `api_error` / `transcript_400_retry` absent until close; spec documents cross-sync; drift gate owns verification at Stage 6.
5. **Context rename** — exploration will use `context="llm_loop"` (not legacy `log_error("chat_completion")`); intentional; tests should assert new enum values.

## Summary

Run `spec.md` and domain § API error logging (APP-034) are **implementation-ready**: redaction + serialization helpers in `logger.py`, canonical `_chat_completion` intercept with APP-032 retry-aware attempt numbering, combat silent-gap fix, concrete pytest matrix, and ticket Expected files include the test module (APP-031 round-1 blocker avoided). Proceed to Dev plan + QA plan gates.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
