# Spec: APP-032-400-retry-malformed-transcript

**Status:** draft  
**backlog_ticket:** APP-032  
**ticket_path:** [tmp/backlog/app-032-400-retry-on-malformed-transcript.md](../../app-032-400-retry-on-malformed-transcript.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-llm-orchestrator-spec.md`

## Problem

APP-031 proactively sanitizes every orchestrator `chat_completion` payload, but provider-specific strictness or sanitizer gaps can still yield **400 Bad Request** on malformed tool transcripts — notably Google via OpenRouter:

```text
Tool-call assistant message produced no valid function calls but is followed by tool result messages
```

Today `_chat_completion` has no try/except; exceptions propagate to six call sites with divergent player-facing fallbacks. Exploration `_llm_loop` (~L2338) logs `log_error("chat_completion", …)` and returns `"The GM falters. (API error: …)"` — a single mid-chain 400 **kills the turn** even when the prior depth succeeded.

Failure surface remains **in-turn** tool loops only (`_llm_loop`, `_creation_llm_loop`, `_combat_llm_loop_inner`). Persisted `self.history` has no tool roles.

## Goals

- **Reactive safety net:** on **malformed-transcript** 400 only, truncate to safe prefix, re-sanitize, retry **once** per `_chat_completion` invocation.
- Reuse APP-031 primitives — `_safe_prefix_fallback` + `sanitize_transcript_messages` — no duplicate repair logic.
- All six call sites benefit via the single `_chat_completion` wrapper (already wired by APP-031).
- Preserve APP-031 non-mutating contract: caller `messages` list unchanged; retry uses internal copies only.

## Non-goals

| Deferred | Owner |
|----------|-------|
| Proactive sanitize / invariant enforcement | **APP-031** (done) |
| Tool arg coercion | **APP-080** (done) |
| Full tool-chain JSONL dump on API error | **APP-034** |
| Mutating caller `messages` in place after retry | Out of v1 — loops keep appending to original list; per-call retry is sufficient |
| Retry on non-400 errors (429, 5xx, network) | Out of scope |
| Retry on unrelated 400 (invalid model, bad API key, context length) | Narrow detection only |
| Changes to `openrouter.py` | Ticket scope **`orchestrator.py`** only |
| Including trailing content-only `assistant` in safe prefix | APP-031 deferred; same floor for APP-032 truncate |

## Requirements

Full behavior and test contracts: domain spec § **Reactive 400 retry (APP-032)**.

### R1: Malformed-transcript 400 detection

**Acceptance criteria**

- [ ] Module-level helper `is_malformed_transcript_400(exc: BaseException) -> bool` in `app/gm/orchestrator.py` (or private `_…` alias).
- [ ] Returns `True` only when **both**:
  1. Exception is `openai.BadRequestError` **or** `openai.APIStatusError` with `status_code == 400`.
  2. `str(exc)` (case-insensitive) matches **at least one** transcript-related substring:
     - `tool-call assistant message produced no valid function calls`
     - `no valid function calls but is followed by tool`
     - `tool result messages` **and** (`tool_call` or `tool_calls` in message)
- [ ] Returns `False` for unrelated 400s (e.g. `"model"`, `"invalid_api_key"`, `"context_length"`) — use negative fixture in tests.
- [ ] Never raises.

### R2: Retry pipeline inside `_chat_completion`

**Acceptance criteria**

- [ ] Flow on every `_chat_completion` call:
  1. `clean = sanitize_transcript_messages(messages)` (existing APP-031).
  2. First attempt: `chat_completion(…, messages=clean)`.
  3. On exception: if **not** `is_malformed_transcript_400(exc)` → **re-raise immediately** (no retry).
  4. If malformed-transcript 400:
     - `truncated = _safe_prefix_fallback(messages)` — use **caller's original** `messages`, not `clean`.
     - `retry_clean = sanitize_transcript_messages(truncated)`.
     - **One** second attempt: `chat_completion(…, messages=retry_clean)`.
  5. Second failure (any exception) → **re-raise**; existing caller fallbacks unchanged.
- [ ] **Budget:** exactly **one** retry per `_chat_completion` invocation. Multi-depth loops may each retry independently at their depth (not once-per-turn cap).
- [ ] **Non-mutating:** caller's `messages` list and dict refs unchanged (same contract as APP-031 sanitize).
- [ ] Retry preserves all kwargs (`tools`, `tool_choice`, `max_tokens`, `temperature`) from the first attempt.

### R3: APP-031 pairing

**Acceptance criteria**

- [ ] APP-032 does **not** duplicate sanitize invariants or reorder logic — only orchestrates truncate → sanitize → retry.
- [ ] `_safe_prefix_fallback` and `sanitize_transcript_messages` remain shared module-level helpers (no forked copies).
- [ ] First attempt still always runs proactive sanitize (031 prevent → 032 recover).

### R4: Caller behavior unchanged

**Acceptance criteria**

- [ ] No changes required at `_call_narration_llm`, `_narrate_only`, `_creation_llm_loop`, `_combat_llm_loop_inner`, or `_llm_loop` except benefiting from wrapper retry.
- [ ] Successful retry returns normal response dict — callers cannot distinguish first- vs second-attempt success.
- [ ] Exhausted retry (second call fails) propagates to existing `except Exception` paths and fallback prose.

### R5: Observability (optional v1)

**Acceptance criteria**

- [ ] On malformed-transcript retry path, optional JSONL event `transcript_400_retry` with `{attempt: 2, prefix_len, original_len}` — **defer to APP-034** if time-boxed; not blocking for close.
- [ ] If deferred: at minimum existing `log_error` at call sites still fires only when retry exhausted (unchanged).

## Test plan

```bash
cd app && python -m pytest tests/test_transcript_400_retry.py -q
cd app && python -m pytest tests/test_transcript_sanitize.py -q   # APP-031 regression
cd app && python -m pytest tests/ -q
```

| Test | Setup | Pass |
|------|-------|------|
| `test_malformed_400_then_success` | Mock underlying `chat_completion`: raise `BadRequestError` with Google malformed string on 1st call; ok dict on 2nd | `_chat_completion` returns response; exactly 2 HTTP attempts; 2nd call `messages` passes `assert_transcript_invariants` and matches safe-prefix shape (leading `system` + last `user`) |
| `test_unrelated_400_no_retry` | Mock: `BadRequestError` with `"invalid model"` / non-transcript message | Single attempt; exception propagates |
| `test_malformed_400_twice_propagates` | Mock: malformed 400 on both calls | Exception propagates after 2 attempts |
| `test_non_400_no_retry` | Mock: raise `APIConnectionError` or 429 | Single attempt; no retry |
| `test_is_malformed_transcript_400_cases` | Parametrize known Google string, negative cases | Helper true/false per R1 |
| `test_caller_messages_unchanged_after_retry` | Shared `messages` list ref; fail-then-ok | Input list length, identity, dict contents unchanged |
| `test_llm_loop_depth1_retry_integration` | Monkeypatch `chat_completion` fail-then-ok at depth ≥1 with Holt-shaped array | Turn completes without `"The GM falters"` |

**Fixtures:** reuse `assert_transcript_invariants` from `test_transcript_sanitize.py` (import or shared helper); encode malformed arrays in pytest — no gitignored session JSONL.

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Residual 400 after APP-031 (TC-6 from APP-031 human plan):** If proactive sanitize alone still 400s, turn should recover via truncate+retry — no mid-turn `"The GM falters. (API error: …)"`.
- **Multi-tool depth ≥1:** Memory + travel/dungeon in one turn completes with narration.
- **Tool failure mid-chain:** APP-028 TOOL FAILED ordering + retry still yields GM prose, not hard API fail.
- **Log watch:** optional `transcript_400_retry` if wired; no repeated double-400 on same `_chat_completion` without fallback.

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py`
- `app/tests/test_transcript_400_retry.py` _(new)_
- `tmp/app-llm-orchestrator-spec.md`

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — intercept location, six fallbacks, detection heuristic
- **Domain truth:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — § Reactive 400 retry (APP-032)
- **Paired:** [APP-031](../../app-031-transcript-sanitize-orphan-tool-messages.md) — proactive sanitize (done)
- **Adjacent:** [APP-034](../../app-034-log-tool-chain-on-api-errors.md) — telemetry; [APP-079](../../app-079-finish-reason-length-recovery-policy.md) — orthogonal (length, not transport 400)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | PM draft — reactive 400 retry in `_chat_completion`; narrow detection; once per call; reuse APP-031 truncate/sanitize; test module in Expected files |
