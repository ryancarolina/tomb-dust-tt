# Spec: APP-034-log-tool-chain-on-api-errors

**Status:** draft  
**backlog_ticket:** APP-034  
**ticket_path:** [tmp/backlog/app-034-log-tool-chain-on-api-errors.md](../../app-034-log-tool-chain-on-api-errors.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-llm-orchestrator-spec.md` (on close: cross-sync row in `tmp/app-logging-qa-spec.md` § JSONL)

## Problem

APP-031 and APP-032 repair in-turn tool transcripts proactively and reactively, but when `chat_completion` still fails operators cannot reconstruct **why**. Failures today surface as flat JSONL `error` rows (`{context, error}` string only) at some call sites — and **not at all** in combat (`_combat_llm_loop_inner` tool pass and narrate pass swallow API errors silently).

`log_llm_request` records message **count** and `depth`; `log_tool_call` fires only **after** successful parse+dispatch. A provider 400 on depth ≥1 often means the failing request included assistant `tool_calls` + `tool` rows that never produced per-tool log lines. Without a redacted snapshot of the in-turn chain, debugging Google/OpenRouter transcript rejects, auth failures, and residual sanitizer gaps requires reproducing live sessions.

## Goals

- **Single intercept:** extend `Orchestrator._chat_completion` to emit one structured JSONL event on **every** API failure (after APP-032 retry exhaustion or immediate re-raise for non-retryable errors).
- **Tool-chain payload:** serialize the in-turn `messages` array sent on the **failing attempt** — roles, `tool_calls` (id, name, arguments preview), `tool_call_id` linkage, content lengths/previews — so APP-031/032 incidents are actionable from logs alone.
- **Secret redaction:** implement recursive redaction helpers in `app/gm/logger.py` before JSONL write (ticket AC: “redact keys”).
- **Combat gap:** wrapper logging covers combat paths without separate caller `log_error` (fixes silent failure).
- **Optional (same ticket, non-blocking):** emit deferred `transcript_400_retry` info event when APP-032 retry path runs (success or failure).

## Non-goals

| Deferred | Owner |
|----------|-------|
| Proactive sanitize / 400 retry logic | **APP-031** / **APP-032** (done) |
| Retry on 429/5xx/network | Out of scope |
| Logging successful multi-tool chains every depth | Volume; success path unchanged |
| Persisted `self.history` tool rounds | Ephemeral in-turn arrays only (APP-031) |
| PII scrub beyond API-key patterns | v1 redacts secrets only; player prose in tool args logged truncated |
| `tool_arg_coerced` telemetry | **APP-080** optional — separate stretch; not blocking APP-034 |
| `transcript_sanitized` on every sanitize | **APP-031** optional — compare `len(messages)` vs `len(clean)` only on error path in v1 if cheap |
| Changes to `openrouter.py` | Pass-through unchanged |

## Requirements

Full behavior and test contracts: domain spec § **API error logging (APP-034)**.

### R1: Redaction helpers (`logger.py`)

**Acceptance criteria**

- [ ] Module-level `REDACTED = "[REDACTED]"` (or equivalent constant).
- [ ] `redact_secrets(value: Any) -> Any` — recursively walks str / dict / list; **never raises**.
- [ ] String redaction (case-insensitive) replaces substrings matching:
  - `sk-or-` through end of token segment (OpenRouter key prefix)
  - `Bearer ` + following token-like run
  - JSON-ish `"api_key"`, `"authorization"`, `OPENROUTER_API_KEY` values
- [ ] Applied to: exception message string, all serialized message fields, and nested tool argument previews before `log_entry`.
- [ ] `log_entry` swallow-on-IOError behavior unchanged (logging must not break gameplay).

### R2: Tool-chain serialization (`logger.py`)

**Acceptance criteria**

- [ ] `summarize_messages_for_log(messages: list[dict]) -> list[dict]` — returns a **new** list of per-message summaries (does not mutate input).
- [ ] Per message fields (when present):

| Field | Rule |
|-------|------|
| `role` | As-is |
| `content_len` | `len(content)` when `content` is str |
| `content_preview` | First **200** chars of content (after redaction); omit or `null` when absent |
| `tool_calls` | List of `{id, name, arguments_len, arguments_preview}` — `arguments_preview` max **120** chars after redaction |
| `tool_call_id` | For `role: tool` rows |

- [ ] `extract_tool_chain(messages: list[dict]) -> list[dict]` — ordered rounds: each entry `{assistant_tool_calls: [{id, name}], tool_results: [{tool_call_id, content_len}]}` for debugging id linkage (empty list when no tool roles).
- [ ] Helpers never raise on malformed message dicts (skip bad entries).

### R3: `log_api_error` event (`logger.py`)

**Acceptance criteria**

- [ ] `log_api_error(data: dict)` → JSONL type **`api_error`** via `log_entry`.
- [ ] Required payload keys on every emit:

| Key | Type | Meaning |
|-----|------|---------|
| `context` | str | Call-site label (e.g. `llm_loop`, `creation_llm_loop`, `combat_tools`, `combat_narrate`, `narrate_flavor`, `narrate_only`) |
| `exc_type` | str | `type(exc).__name__` |
| `error` | str | Redacted `str(exc)` |
| `model` | str | Model id from `_chat_completion` |
| `tools_present` | bool | `tools is not None` |
| `attempt` | int | `1` first failure; `2` when second `chat_completion` raises |
| `malformed_transcript_400` | bool | `is_malformed_transcript_400(exc)` on the exception being logged |
| `original_len` | int | `len(messages)` caller array |
| `sent_len` | int | `len(clean)` or `len(retry_clean)` for failing attempt |
| `messages_summary` | list | Output of `summarize_messages_for_log` for **failing attempt** messages |
| `tool_chain` | list | Output of `extract_tool_chain` for same array |

- [ ] Optional keys when provided by wrapper: `depth: int | None`, `retry_truncated: bool` (true when failing attempt used `_safe_prefix_fallback` output).
- [ ] Payload passed through `redact_secrets` as final step.

### R4: Wire point — `_chat_completion` (`orchestrator.py`)

**Acceptance criteria**

- [ ] Extend signature with optional kwargs: `context: str | None = None`, `depth: int | None = None` (defaults preserve existing call sites).
- [ ] **First attempt failure** (non-retryable): before re-raise, call `log_api_error(...)` with `attempt=1`, `sent_len=len(clean)`, failing messages = `clean`.
- [ ] **Malformed-transcript 400 path:**
  1. **Optional:** emit `log_transcript_400_retry` (R6) with `attempt=1`, lengths, `will_retry=true`.
  2. Run existing truncate → sanitize → second `chat_completion`.
  3. On second failure: `log_api_error(...)` with `attempt=2`, `sent_len=len(retry_clean)`, failing messages = `retry_clean`, `retry_truncated=true`; then re-raise.
- [ ] **Retry success:** no `api_error` event; optional R6 info log only.
- [ ] All six call sites pass distinct `context` string; tool loops pass current `depth` where already available (`_llm_loop`, `_creation_llm_loop`, `_combat_llm_loop_inner` tool pass).
- [ ] Wrapper is **canonical** failure logger — removes duplicate `log_error` at call sites that only repeat the same exception string (exploration, creation, narration). Player-facing fallbacks unchanged.

### R5: Combat silent-path fix

**Acceptance criteria**

- [ ] Combat tool pass API failure produces `api_error` with `context="combat_tools"` (via `_chat_completion`) even though caller returns `"[Mechanics failed — API error: …]"` without its own `log_error`.
- [ ] Combat narrate pass failure produces `api_error` with `context="combat_narrate"`.

### R6: `transcript_400_retry` (optional v1 — APP-032 deferral)

**Acceptance criteria**

- [ ] `log_transcript_400_retry(data: dict)` → JSONL type **`transcript_400_retry`**.
- [ ] Emitted once when `is_malformed_transcript_400(exc)` triggers retry, **before** second attempt.
- [ ] Payload: `{context, attempt: 1, original_len, clean_len, prefix_len, will_retry: true}` where `prefix_len = len(truncated)` after `_safe_prefix_fallback`.
- [ ] On retry **success**, optionally add `{outcome: "success"}` via a second info row or extend first row — Dev may choose single-row update vs second event; tests assert at least one retry marker exists in session log when retry runs.
- [ ] **Not blocking for ticket close** if time-boxed; R1–R5 are blocking.

## Test plan

```bash
cd app && python -m pytest tests/test_api_error_logging.py -q
cd app && python -m pytest tests/test_transcript_sanitize.py tests/test_transcript_400_retry.py -q
cd app && python -m pytest tests/ -q
```

| Test | Setup | Pass |
|------|-------|------|
| `test_redact_secrets_openrouter_key` | String containing `sk-or-v1-abc123` | Output contains `[REDACTED]`, not raw key |
| `test_redact_secrets_bearer` | `Authorization: Bearer eyJ…` | Token redacted |
| `test_redact_secrets_nested_dict` | Dict with nested api_key field | All levels redacted |
| `test_summarize_messages_tool_calls` | Assistant + 2 tool messages | Summary has ids, names, previews capped |
| `test_extract_tool_chain_order` | Multi-round chain | Round order matches input |
| `test_log_api_error_on_unrelated_400` | Mock `chat_completion` raise unrelated `BadRequestError` | One `api_error` row; `malformed_transcript_400=false`; `attempt=1` |
| `test_log_api_error_malformed_400_twice` | Mock malformed 400 both attempts | `api_error` with `attempt=2`, `retry_truncated=true`; `sent_len` < `original_len` |
| `test_malformed_400_retry_success_no_api_error` | Malformed 400 then ok | No `api_error`; optional `transcript_400_retry` present |
| `test_chat_completion_passes_context_depth` | Patch `log_api_error`, fail exploration-shaped call | Payload includes `context`, `depth` |
| `test_logger_never_raises` | Patch `open()` to raise | `_chat_completion` still re-raises API error; no secondary exception |
| `test_combat_tools_failure_logged` | Mock combat inner tool pass failure | `api_error` with `context=combat_tools` |

**Fixtures:** Holt-shaped malformed arrays from `test_transcript_sanitize.py`; patch `gm.orchestrator.chat_completion` per logging spec import discipline. Capture JSONL via patch `gm.logger.log_entry` or temp log dir.

## Human playtest hints (Stage 7)

Not primary for observability ticket — pytest is source of truth. Optional manual check:

- Induce API failure (invalid model in config or disconnect) during exploration tool turn; confirm `app/logs/session-YYYY-MM-DD.jsonl` contains `api_error` with `tool_chain` non-empty when tools were in flight.
- Confirm no raw `sk-or-` substrings in log file after auth-related failure.

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py` — `_chat_completion` intercept, optional `context`/`depth` kwargs at call sites, dedupe caller `log_error`
- `app/gm/logger.py` — `redact_secrets`, summarize/extract helpers, `log_api_error`, optional `log_transcript_400_retry`
- `app/tests/test_api_error_logging.py` — new module (R1–R5 tests)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft — api_error + tool chain + redaction; optional transcript_400_retry |
