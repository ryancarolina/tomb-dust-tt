# QA PASS: plan — round 1

**Task:** app-034-log-tool-chain-on-api-errors  
**backlog_ticket:** APP-034  
**ticket_path:** [tmp/backlog/app-034-log-tool-chain-on-api-errors.md](../../app-034-log-tool-chain-on-api-errors.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; domain § API error logging APP-034)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-llm-orchestrator-spec.md`
- [x] Plan impl scope ⊆ ticket Expected files (`orchestrator.py`, `logger.py`, `test_api_error_logging.py`); domain/logging spec sync deferred to close stage only
- [x] Acceptance criteria testable — ticket AC + spec R1–R6 mapped in architecture, helper contracts, call-site table, test matrix (U1–U5, I1–I9), and AC mapping table
- [x] Code traces match repo — independently spot-checked:
  - `_chat_completion` L1208–1236 (APP-032 sanitize + retry; **no** failure logging today; retry re-raise unlogged)
  - Six `_chat_completion(` call sites: L1242, L1866, L1886, L2229, L2310, L2383
  - Combat silent gap: L2234–2235 (tool pass), L2310–2313 (narrate pass bare `except`)
  - Four duplicate `log_error` rows to remove: L1248 `narrate_flavor`, L1868 `narrate_only`, L1892 `creation_llm_loop`, L2388 `chat_completion`
  - Non-duplicate `log_error` retention enumerated (depth limit L2374, all-tools-failed L2289, etc.)
- [x] AGENTS.md / canon compliance — orchestrator + logger only; no `openrouter.py`; TurnTruth N/A (JSONL observability)
- [x] Tests/commands listed — 12 pytest rows + APP-031/032 regression + full `tests/` suite
- [x] `qa-spec-pass.md` adversarial notes addressed in plan (combat_narrate I7, duplicate `log_error` table I8, context enum rename to `llm_loop`)
- [x] APP-031/032 boundary — observe failing `clean` / `retry_clean`; no sanitize/retry logic changes

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/logger.py` — R1–R3 (+ optional R6) helpers | Yes |
| `app/gm/orchestrator.py` — `_emit_api_error`, extended `_chat_completion`, six site kwargs, dedupe `log_error` | Yes |
| `app/tests/test_api_error_logging.py` (new) | Yes |
| `tmp/app-llm-orchestrator-spec.md` — checklist + changelog on close | Process (Spec sync on close) |
| `tmp/app-logging-qa-spec.md` — JSONL table cross-sync on close | Process (noted in spec header) |

**Out of scope (explicit):** `openrouter.py`; APP-031/032 repair changes; success-path tool logging; `tool_arg_coerced` / proactive `transcript_sanitized` — aligned with run `spec.md` non-goals.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 `redact_secrets` | § `logger.py` — R1 redaction | U1–U3 |
| R2 summarize / extract | § R2 serialization | U4, U5, I9 |
| R3 `log_api_error` | § R3 event emitters; `_emit_api_error` wire | I1, I2, I4 |
| R4 `_chat_completion` intercept + six contexts | § Architecture flowchart; § R4 call-site table | I1–I4, I8 |
| R5 combat silent-path fix | § R5; contexts `combat_tools` / `combat_narrate` | I6, I7 |
| R6 `transcript_400_retry` (optional) | § R6; non-blocking close | I3 |
| Ticket: no raw keys in JSONL | R1 applied inside `log_api_error` | U1–U3, I9 |
| Ticket: combat failures logged | R5 via wrapper kwargs only | I6, I7 |
| Ticket: no duplicate noisy JSONL | Remove 4× caller `log_error`; canonical wrapper | I8 + call-site table |
| Logger never breaks gameplay | `log_entry` swallow unchanged | I5 |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-034 `in_progress`, P2 |
| Plan ⊆ Expected files | **PASS** | No unauthorized impl paths |
| Spec R1–R6 in plan | **PASS** | Helper contracts + intercept flow sufficient for impl |
| Code traces | **PASS** | Line refs verified against live `orchestrator.py` / `logger.py` |
| Test plan vs spec / `qa-spec-pass` | **PASS** | Exceeds domain spec minimum (adds I7 narrate, I8 dedupe, I9 tool_chain) |
| APP-031/032 boundaries | **PASS** | Retry branch adds logging only; fixtures reuse `test_transcript_400_retry` exports |
| TurnTruth / narration gate | **PASS** | Player fallbacks unchanged; no verify-path edits |

## Notes (non-blocking — implementation QA)

1. **I7 combat narrate fixture** — Plan sketch requires mock tool-pass success + narrate-pass failure; impl may need minimal combat message fixture and stubs for `_execute_combat_action` / auto-chain — dev reflection flags this; not a plan blocker.
2. **R6 wire sketch** — `log_transcript_400_retry` pseudocode calls `_safe_prefix_fallback` before assigning `truncated`; impl should call once and reuse `len(truncated)`.
3. **`extract_tool_chain` orphan `tool` rows** — Plan states malformed tolerance; consider one unit fixture with orphan tool message if round-boundary behavior is ambiguous during impl.
4. **APP-032 test side effects** — New `_chat_completion` logging is side-effect-only for existing retry tests; plan open Q5 correctly defers APP-032 test edits — impl QA should still run full regression.
5. **Legacy `log_error("chat_completion")` retirement** — I8 asserts zero `chat_completion` context in `log_error`; new canonical context is `llm_loop` in `api_error` — intentional per plan and domain spec context table.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
