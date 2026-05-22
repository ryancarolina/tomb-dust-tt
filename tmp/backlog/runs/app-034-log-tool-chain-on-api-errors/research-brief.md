# Research Brief: APP-034-log-tool-chain-on-api-errors

**Date:** 2026-05-22
**Question:** When OpenRouter/`chat_completion` fails, what context is lost today, and where should we log a **full in-turn tool-call chain** (with secret redaction) so APP-031/032 debugging is actionable?

**backlog_ticket:** APP-034
**ticket_path:** tmp/backlog/app-034-log-tool-chain-on-api-errors.md
**domain_spec:** tmp/app-llm-orchestrator-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

**False.** Ticket domain spec [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) is registered in [`tmp/app-master-spec.md`](../../../app-master-spec.md) as **LLM orchestrator** (`gm/orchestrator.py`, `openrouter.py`, …). The spec already lists APP-034 in open work and explicitly defers three observability hooks to this ticket: `tool_arg_coerced` (APP-080 §), `transcript_sanitized` (APP-031 §), `transcript_400_retry` (APP-032 §). Companion spec [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) documents JSONL `error` events but not tool-chain payloads. No new registry row required.

## Summary

**APP-031 and APP-032 are landed.** Every orchestrator LLM call flows through `Orchestrator._chat_completion`, which sanitizes via `sanitize_transcript_messages`, calls `openrouter.chat_completion`, and on **narrow** malformed-transcript 400 runs `_safe_prefix_fallback` → sanitize → **one** retry. **Neither success nor failure paths emit structured tool-chain telemetry.**

On API failure, callers catch `Exception` and call `log_error(context, str(exc))` — a flat JSONL `error` row with **no** `messages` snapshot, depth, model, tools flag, sanitized vs original lengths, retry attempt, or per-message `tool_calls` / `tool_call_id` chain. Correlation is weak: `log_llm_request` records `messages` **count** and `depth` immediately before the try, but not content; `log_tool_call` only fires **after** successful parse+dispatch, so a 400 on depth ≥1 often means the failing request never produced tool log lines for the assistant message that triggered the reject.

**Combat is the worst gap:** `_combat_llm_loop_inner` returns `"[Mechanics failed — API error: {exc}]"` on tool-pass failure **without** `log_error` (L2234–2235). The narrate-only second `_chat_completion` (L2310–2313) fails silently to mechanical `brief`.

**Recommended wire point:** extend `_chat_completion` (single intercept — all six call sites) to emit one structured JSONL event on **any** uncaught exception after retry exhaustion (and on non-retryable errors). Implement redaction + serialization helpers in `app/gm/logger.py`. Keep existing caller `log_error` for context strings or thin-wrap to the new helper — PM should avoid duplicate noisy rows.

**Pairs with APP-031/032:** proactive sanitize + reactive retry reduce hard failures; APP-034 makes **residual** failures and retry outcomes debuggable (including expanding `is_malformed_transcript_400` heuristics from real logged provider strings).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Central intercept | `app/gm/orchestrator.py` — `_chat_completion` (L1208–1236) | Sanitize + try/retry; **no** logging on `except` |
| 400 classifier | `is_malformed_transcript_400` (L321–337) | Narrow; retry only when true |
| Truncate helper | `_safe_prefix_fallback` (L229–244) | Drops in-turn tool chain for retry |
| API client | `app/gm/openrouter.py` — `chat_completion` (L21–63) | Unchecked `create`; raises SDK errors |
| Exploration loop | `_llm_loop` (L2358+) | `log_error("chat_completion", str(exc))` on failure |
| Creation loop | `_creation_llm_loop` (L1874+) | `log_error("creation_llm_loop", …)` |
| Combat loop | `_combat_llm_loop_inner` (L2223+) | API error: **no** `log_error`; narrate pass silent |
| Flavor LLM | `_call_narration_llm`, `_narrate_only` | `log_error` yes; no tool roles in typical input |
| Per-tool success logs | `log_tool_call` in `logger.py` (L80–81) | Post-dispatch only; not failure chain |
| Request/response skim | `log_llm_request` / `log_llm_response` (L84–94) | Count + tool **names** only on success path |
| Generic errors | `log_error` (L97–98) | `{context, error}` string only |
| Tool arg normalize | `app/gm/tool_args.py` (APP-080) | Optional `tool_arg_coerced` deferred here |
| Domain deferrals | `tmp/app-llm-orchestrator-spec.md` § APP-031/032 observability | Three optional JSONL event types |
| Logging spec | `tmp/app-logging-qa-spec.md` § JSONL | `error` listed; no `api_error` / tool chain |
| Paired tickets | APP-031 (done), APP-032 (done) | Repair transcript; APP-034 observes failures |

## Code-path traces

### `_chat_completion` — all API errors funnel here

```1208:1236:app/gm/orchestrator.py
    def _chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list | None = None,
        ...
    ) -> dict:
        clean = sanitize_transcript_messages(messages)
        cc_kwargs = dict(...)
        try:
            return chat_completion(self.client, **cc_kwargs)
        except Exception as exc:
            if not is_malformed_transcript_400(exc):
                raise
            truncated = _safe_prefix_fallback(messages)
            retry_clean = sanitize_transcript_messages(truncated)
            return chat_completion(
                self.client,
                **{**cc_kwargs, "messages": retry_clean},
            )
```

| Failure mode | Behavior today | Logging today |
|--------------|----------------|---------------|
| Non-400 or unrelated 400 | Re-raise immediately | None in wrapper |
| Malformed-transcript 400, retry succeeds | Returns normally | None (retry invisible) |
| Malformed-transcript 400, retry fails | Re-raise second exception | None |
| 429, 5xx, auth, model errors | Re-raise | Caller `log_error` only |

**APP-034 opportunity:** log on re-raise paths with: `exc_type`, redacted `exc_message`, `malformed_transcript_400`, `attempt` (1 or 2), `original_len`, `clean_len`, `retry_len`, `tools_present`, `model`, and **tool-chain extract** from the `messages` (or `clean` / `retry_clean`) that were sent on the failing attempt.

### Exploration `_llm_loop` — primary “GM falters” surface

1. `log_llm_request(len(messages), model, depth)` (L2380).
2. `_chat_completion(messages, tools=TOOLS if depth < 3 else None)` (L2383–2386).
3. On exception: `log_error("chat_completion", str(exc))` (L2388) → player `"The GM falters. (API error: …)"` (L2391).
4. **Gap:** JSONL has error string only; cannot reconstruct assistant `tool_calls` + following `tool` / `system` ordering that caused provider reject at depth ≥1.

### Creation `_creation_llm_loop`

Same pattern (L1883–1893): `log_error("creation_llm_loop", str(exc))` without messages payload. In-loop `messages` accumulates assistant + tool rows across `depth in range(4)`.

### Combat `_combat_llm_loop_inner`

1. Tool pass (L2228–2235): on API error → return `"[Mechanics failed — API error: {exc}]"` — **no** `log_error`.
2. Narrate pass (L2309–2313): bare `except Exception: return brief` — **no** log.
3. **High value:** narrate pass sends **full** prior tool chain with `tools=None`; malformed tool tail from pass 1 surfaces here.

### Narration-only calls (lower priority)

`_call_narration_llm` / `_narrate_only`: failures logged as `narrate_flavor` / `narrate_only`; inputs rarely contain `tool` roles. Ticket AC still applies (“API errors”) — PM may scope v1 to tool-enabled `_chat_completion` invocations only.

### What “full tool-call chain” should mean (recommended payload)

Serialize the **in-turn** `messages` array (caller’s list at failure time, not persisted `self.history`) focusing on:

| Field | Source |
|-------|--------|
| `depth` | Pass from caller or infer from wrapper kwargs / thread-local — **not** in `_chat_completion` today; callers already know depth |
| `messages_summary` | Per-message: `role`, `content_len` or truncated `content`, `tool_calls` (id, name, arguments preview), `tool_call_id` for `tool` rows |
| `tool_chain` | Ordered list extracted: `{assistant_tool_calls: [...], tool_results: [{id, name, ok?}]}` |
| `sanitize_delta` | Optional: `len(messages)` vs `len(clean)` if sanitize dropped rows (feeds deferred `transcript_sanitized`) |

Persisted `self.history` is **not** required for AC — tool rounds are ephemeral per turn (APP-031 research).

### Redaction (“redact keys”)

**No redaction helper exists** in `app/` today. Grep finds only `OPENROUTER_API_KEY` in `openrouter.py` / README.

| Secret surface | Risk |
|----------------|------|
| `str(exc)` on auth failures | May echo key fragments or bearer tokens |
| `messages` system prompts | Large canon context — not secret but noisy |
| `tool` result JSON | Engine state, not API keys |
| `remember_fact` args | Player prose — out of “keys” scope unless PM widens PII policy |

**Minimum v1 (ticket AC):** redact patterns matching `sk-or-`, `OPENROUTER_API_KEY`, `Bearer `, and generic `api_key`/`authorization` substrings in serialized output and `error` field. Apply recursively to dict/list payloads before `json.dumps`.

## Existing specs & docs

- **Ticket:** [`tmp/backlog/app-034-log-tool-chain-on-api-errors.md`](../../app-034-log-tool-chain-on-api-errors.md) — AC: log full tool-call chain on API errors (redact keys); Expected: `orchestrator.py`, `logger.py`.
- **Domain spec:** [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) — APP-031 § Observability (optional `transcript_sanitized`); APP-032 § (`transcript_400_retry`); APP-080 optional `tool_arg_coerced`; open-work checklist includes APP-034.
- **Logging spec:** [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) — extend event table on close (not in ticket Expected files; changelog cross-sync).
- **APP-031/032 close:** Both deferred JSONL events to APP-034; drift-checks mark absence as non-blocking.
- **APP-080:** Coercion telemetry optional; `log_tool_call` logs **post-normalize** args only.

## Tests & commands

```bash
# Baseline transcript suite (unchanged by APP-034 unless tests touch wrapper)
cd app && python -m pytest tests/test_transcript_sanitize.py tests/test_transcript_400_retry.py -q

# Suggested new module (PM/Dev — ticket does not list test file; precedent: APP-031/032 added tests)
cd app && python -m pytest tests/test_api_error_logging.py -q
```

**Suggested test cases:**

| Case | Setup | Expected |
|------|-------|------------|
| Redact API key in exception string | Mock `chat_completion` raise with `sk-or-v1-…` in message | JSONL payload has `[REDACTED]` not raw key |
| Tool chain on 400 | Mock fail with messages containing assistant+tool | Log includes tool ids/names/order |
| Malformed 400 retry then fail | `side_effect` [malformed 400, malformed 400] | Log shows `attempt: 2`, `retry_len` < `original_len` |
| Malformed 400 retry success | First 400, second ok | Optional: `transcript_400_retry` success marker or no error log |
| Non-tool `_chat_completion` | Flavor messages only | PM decision: omit `tool_chain` or log empty chain |
| Combat API error | Mock combat loop failure | `log_error` or unified event fires (fixes silent gap) |
| Logger never raises | IOError on log file | Swallow like existing `log_entry` (L33–34) |

Use mock `chat_completion` / patch `gm.orchestrator.chat_completion` per [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) import discipline.

## Risks & unknowns

| Risk | Detail |
|------|--------|
| Log volume | Full chain per error can be large (multi-tool turns); cap argument preview length in PM spec |
| Duplicate events | Wrapper log + caller `log_error` — coordinate one canonical `api_error` type |
| Depth not in wrapper | Need optional `depth` / `loop` param on `_chat_completion` or post-hoc context in caller-only logs |
| Retry success invisible | Operators cannot tell APP-032 saved the turn without `transcript_400_retry` info log |
| Sanitize observability | APP-031 deferred `transcript_sanitized` — only know drops if wrapper compares `len(messages)` vs `len(clean)` |
| `registry_gap` for logging spec | Event types live in orchestrator domain spec today; PM should append row to `app-logging-qa-spec.md` on close |
| Unrelated 400s | Still hard-fail; logged chain helps distinguish bad model vs transcript vs quota |
| Combat silent path | Must fix as part of “API errors” AC or explicitly document exclusion |

## Raw notes

### `_chat_completion` call sites (all inherit wrapper logging once added)

| Call site | Tools? | Caller on failure |
|-----------|--------|-------------------|
| `_call_narration_llm` | No | `log_error("narrate_flavor")` |
| `_narrate_only` | No | `log_error("narrate_only")` |
| `_creation_llm_loop` | Yes (depth-dependent) | `log_error("creation_llm_loop")` |
| `_combat_llm_loop_inner` tools | Yes | **None** |
| `_combat_llm_loop_inner` narrate | No | **None** |
| `_llm_loop` | Yes (depth-dependent) | `log_error("chat_completion")` |

### Deferred JSONL events (consolidation candidate for APP-034)

| Event | Source ticket | Trigger |
|-------|---------------|---------|
| `api_error` / `chat_completion_error` | APP-034 AC | Any `_chat_completion` failure after retry |
| `transcript_400_retry` | APP-032 R5 | Malformed 400 path before retry |
| `transcript_sanitized` | APP-031 R5 | Sanitize drops/reorders (compare before/after) |
| `tool_arg_coerced` | APP-080 optional | `normalize_tool_args` changed value |

PM may ship **ticket AC only** (`api_error` + chain) and treat the other three as stretch goals in the same ticket to avoid follow-up churn.

### Session evidence

`app/logs/session-2026-05-20.jsonl` (gitignored) — Holt multi-tool / Google 400 string documented in APP-031/080 research. Not replayed in this run; pytest fixtures remain source of truth for CI.

### `log_llm_response` limitation (motivation)

```88:94:app/gm/logger.py
def log_llm_response(content: str, tool_calls: list, finish_reason: str):
    log_entry("llm_response", {
        "content_length": len(content),
        "content_preview": content[:300],
        "tool_calls": [tc["function"]["name"] for tc in tool_calls] if tool_calls else [],
        "finish_reason": finish_reason,
    })
```

Arguments JSON and `tool_call_id` linkage are **not** logged on success either — APP-034 error payload should include them for the failing request at minimum.
