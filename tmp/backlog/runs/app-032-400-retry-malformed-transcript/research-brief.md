# Research Brief: APP-032-400-retry-malformed-transcript

**Date:** 2026-05-22
**Question:** After APP-031 proactive sanitize, how do malformed-transcript **400** errors still surface from OpenRouter through `orchestrator.py`, and where should reactive truncate→sanitize→retry-once land?

**backlog_ticket:** APP-032
**ticket_path:** tmp/backlog/app-032-400-retry-on-malformed-transcript.md
**domain_spec:** tmp/app-llm-orchestrator-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

**False.** Ticket domain spec [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) is registered in [`tmp/app-master-spec.md`](../../../app-master-spec.md) as **LLM orchestrator** (`gm/orchestrator.py`, `openrouter.py`, …). Domain spec § **Transcript sanitize (APP-031)** already documents APP-032 pairing (reactive 400 → truncate to safe prefix, sanitize, retry once), lists APP-032 in open work, and cites the Google malformed-transcript error in § Problem. [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) § Known issues (2026-05-18) cross-links the same failure. No new registry row required.

## Summary

**APP-031 is landed:** every orchestrator LLM call flows through `Orchestrator._chat_completion`, which runs `sanitize_transcript_messages` then delegates to `openrouter.chat_completion`. **`openrouter.py` remains a pass-through** — it calls `client.chat.completions.create` with no validation or error handling; HTTP/API failures propagate as unchecked exceptions (typically `openai.BadRequestError` with `status_code == 400` on SDK 2.37.0).

**There is still no reactive repair.** Six call sites wrap `_chat_completion` in bare `except Exception`, log (inconsistently), and return player-facing fallback prose — notably `_llm_loop` → `"The GM falters. (API error: …)"`, which ends the turn and feels session-killing. No path truncates the in-turn `messages` array or retries the API call.

**Failure surface is in-turn tool loops only.** Persisted `self.history` holds `{user|assistant, content}` strings without tool roles; `build_messages` assembles system + history + current user input. Malformed arrays accumulate inside `_llm_loop`, `_creation_llm_loop`, and `_combat_llm_loop_inner` across depth ≥1 resubmits — the same surface APP-031 targeted.

**APP-032 should extend `_chat_completion`**, not `openrouter.py` (ticket Expected files scope). On **malformed-transcript** 400: apply existing `_safe_prefix_fallback(messages)` → `sanitize_transcript_messages` → **one** retry. Shared primitives from APP-031 are ready; no duplicate repair logic needed. Optional observability (`transcript_400_retry`) may defer to APP-034 alongside tool-chain dumps.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Central wire point | `app/gm/orchestrator.py` — `_chat_completion` (L1174–1192) | Sanitize pre-send; **no** try/except today |
| Proactive sanitize | `app/gm/orchestrator.py` — `sanitize_transcript_messages`, `_safe_prefix_fallback` (L226–309) | APP-031 done; `_safe_prefix_fallback` = leading `system` + last `user` |
| API client | `app/gm/openrouter.py` — `chat_completion` (L21–63) | Unchecked `client.chat.completions.create`; raises on 400 |
| Exploration loop | `app/gm/orchestrator.py` — `_llm_loop` (L2314–2443) | Primary player-visible failure; depth ≤4 |
| Creation loop | `app/gm/orchestrator.py` — `_creation_llm_loop` (L1830–) | `for depth in range(4)` in-loop |
| Combat loop | `app/gm/orchestrator.py` — `_combat_llm_loop_inner` (L2179–2269) | Two `_chat_completion` calls (tools + narrate) |
| Narration-only calls | `_call_narration_llm`, `_narrate_only` | Low malformed-transcript risk (no tool roles) |
| Message assembly | `app/gm/context.py` — `build_messages` (L174–190) | No tool roles from history |
| Persisted history | `self.history` append sites (~L1074, L1408, L2126, L2158) | Tool rounds never persisted |
| Error logging | `app/gm/logger.py` — `log_error` (L97–98) | JSONL `error` event; no tool-chain context (APP-034) |
| APP-031 tests | `app/tests/test_transcript_sanitize.py` | 12 tests; Holt shapes; wrapper integration — **no 400 retry tests** |
| Domain pairing | `tmp/app-llm-orchestrator-spec.md` § Transcript sanitize — APP-031 vs APP-032 | 031 prevent → 032 recover |
| Session evidence | `app/logs/session-2026-05-20.jsonl` (gitignored) | Holt multi-tool / Google 400 string cited in APP-031 research |

## Code-path traces

### OpenRouter → exception (no handling today)

1. **Entry:** `Orchestrator._chat_completion(messages=…)` (L1174).
2. **Sanitize:** `clean = sanitize_transcript_messages(messages)` — non-mutating copy (L1183).
3. **Delegate:** `return chat_completion(self.client, model=…, messages=clean, …)` (L1184–1191).
4. **HTTP:** `openrouter.chat_completion` → `client.chat.completions.create(**kwargs)` (L41) — OpenAI SDK 2.x.
5. **On provider reject:** raises `openai.BadRequestError` (400) or other `openai.APIStatusError` subclasses — **not caught** in `_chat_completion` or `openrouter.py`.
6. **Typical message (Google via OpenRouter):** `Tool-call assistant message produced no valid function calls but is followed by tool result messages` (domain spec § Problem, APP-031 research).

### Exploration `_llm_loop` — primary player-visible 400 path

1. **Entry:** `process_turn` → `build_messages(…, self.history, player_input)` → `_llm_loop(messages, depth=0)` (L2314).
2. **Depth 0 call:** `_chat_completion(messages, tools=TOOLS)` (L2339–2342).
3. **Tool round:** append `assistant` + `tool_calls` (L2370–2374); per tool: optional `system` TOOL FAILED (L2399–2405), then `tool` result (L2406–2410).
4. **Recurse:** `return self._llm_loop(messages, depth + 1)` (L2443) — **same mutable `messages` list** carries assistant/tool/system ordering.
5. **Depth ≥1 400 today:** `except Exception as exc` (L2343–2347) → `log_error("chat_completion", str(exc))` → `_last_content` or `"The GM falters. (API error: {exc})"`. **No truncate, no retry.**
6. **Post-APP-031:** depth ≥1 resubmit should pass `assert_transcript_invariants` (see `test_wrapper_called_in_llm_loop`); 400 implies **sanitizer gap** or **provider-specific invariant** beyond APP-031 rules.

### APP-032 intended intercept (not implemented)

1. **Location:** inside `_chat_completion` (single wrapper — all six call sites benefit).
2. **Detect:** malformed-transcript 400 — recommend `isinstance(exc, openai.BadRequestError)` **and** substring/heuristic on `str(exc)` for known tool-order errors (avoid retrying unrelated 400s e.g. bad model name).
3. **Recover:** `truncated = _safe_prefix_fallback(messages)` → `retry_clean = sanitize_transcript_messages(truncated)` → second `chat_completion(…, messages=retry_clean)`.
4. **Budget:** **one** retry per `_chat_completion` invocation (domain spec); if second call fails, re-raise for existing caller fallbacks.
5. **Open design:** retry uses a **copy** for the API; caller’s `messages` list is **not** updated today — subsequent loop depths still hold the malformed tail unless PM spec adds in-place replacement (see Risks).

### Other call-site fallbacks (same uncaught 400 source)

| Call site | On `_chat_completion` failure | Logs? |
|-----------|------------------------------|-------|
| `_call_narration_llm` (L1197–1206) | `_NAME_LENGTH_STATIC_FALLBACK` | `log_error("narrate_flavor")` |
| `_narrate_only` (L1821–1825) | `"The clerk regards you with a weary sigh."` | `log_error("narrate_only")` |
| `_creation_llm_loop` (L1841–1849) | `"The clerk mutters something unintelligible."` | `log_error("creation_llm_loop")` |
| `_combat_llm_loop_inner` tools (L2184–2191) | `"[Mechanics failed — API error: {exc}]"` | **No** `log_error` |
| Combat narrate pass (L2265–2269) | mechanical `brief` string | **No** log |
| `_llm_loop` (L2343–2347) | `_last_content` or GM falters | `log_error("chat_completion")` |

### `_safe_prefix_fallback` contract (reuse for truncate)

```226:241:app/gm/orchestrator.py
def _safe_prefix_fallback(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """When sanitize would return empty, keep leading system + last user (APP-031)."""
    ...
    # (1) all leading system messages in order
    # (2) last user message only
    # (3) otherwise []
```

APP-031 explicitly deferred including trailing content-only `assistant` — acceptable v1 floor for APP-032 truncate; PM may widen if recovery loses too much in-turn context.

## Existing specs & docs

- **Ticket:** [`tmp/backlog/app-032-400-retry-on-malformed-transcript.md`](../../app-032-400-retry-on-malformed-transcript.md) — AC: malformed transcript 400 → repair/truncate + retry once; Expected files: `orchestrator.py` only.
- **Domain spec:** [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § Transcript sanitize — APP-031 vs APP-032 table (L414–421); checklist item still open for APP-032.
- **APP-031 close artifacts:** drift-check notes `_safe_prefix_fallback` ready for APP-032; human-test-plan TC-6 routes residual 400s to APP-032.
- **APP-034 (open):** log full tool chain on API errors — complementary, not blocking.
- **APP-079:** transport 400 retry explicitly out of scope (orthogonal to `finish_reason: length`).

## Tests & commands

```bash
# APP-031 baseline (sanitize — no 400 retry yet)
cd app && python -m pytest tests/test_transcript_sanitize.py -q

# Existing mock loop patterns for new retry tests
cd app && python -m pytest tests/test_combat_failure_narration.py tests/test_exploration_site_entry_gate.py -q

# Full app suite after implementation
cd app && python -m pytest tests/ -q
```

**Suggested test cases (PM/Dev — ticket does not list test file; APP-031 precedent added `test_transcript_sanitize.py` outside initial ticket scope):**

| Case | Setup | Expected |
|------|-------|----------|
| Malformed-transcript 400 then success | Mock `chat_completion`: raise `BadRequestError` with Google string on 1st call, ok on 2nd | `_chat_completion` returns response; exactly 2 HTTP attempts; 2nd `messages` satisfies invariants + safe-prefix shape |
| Non-malformed 400 | Mock: 400 with unrelated message (e.g. invalid model) | No retry; exception propagates to caller |
| Second call also 400 | Mock: fail twice | Exception propagates; caller fallback unchanged |
| `_llm_loop` integration | Monkeypatch `_chat_completion` or underlying `chat_completion` with fail-then-ok at depth 1 | Turn completes without `"The GM falters"` |
| Caller list immutability | Shared `messages` ref across loop | Input list unchanged after retry (APP-031 non-mutating contract preserved) |

## Risks & unknowns

- **“Retry once” scope:** Domain spec implies once per `_chat_completion` call (each depth may retry independently). Ticket wording is singular — PM should confirm vs once-per-turn cap.
- **Caller `messages` not repaired:** Internal retry sends truncated copy to API only; loop still appends to the original list. A successful retry at depth 1 does not remove bad assistant/tool rows — depth 2 may 400 again unless sanitize catches it or another retry fires. PM may require `_chat_completion` to return `(response, repaired_messages)` or loop-level truncate-on-400.
- **400 detection heuristic:** Provider error strings vary by route/model. Narrow matching on known malformed-transcript substrings + `status_code == 400` reduces false retries; may miss novel provider wordings until logs (APP-034) inform expansion.
- **Residual 400 after APP-031:** Proactive sanitize may already eliminate most Holt-shaped failures; APP-032 value is **safety net** for sanitizer gaps and strict-provider edge cases — human TC-6 in APP-031 playtest is the live signal.
- **Recovery quality:** `_safe_prefix_fallback` drops entire in-turn tool chain — turn may complete with degraded context (acceptable vs hard fail per grooming note).
- **Expected files gap:** Ticket lists only `orchestrator.py`; pytest file not listed — follow APP-031 pattern and add to ticket before impl if tests are required for close.
- **Combat narrate pass:** Second `_chat_completion` includes full tool chain; same retry policy applies but failures currently silent (return `brief`).

## Raw notes

### `_chat_completion` today (sanitize only)

```1174:1192:app/gm/orchestrator.py
    def _chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        ...
    ) -> dict:
        clean = sanitize_transcript_messages(messages)
        return chat_completion(
            self.client,
            model=self.model,
            messages=clean,
            ...
        )
```

### `openrouter.py` — exception propagates

```41:41:app/gm/openrouter.py
    response = client.chat.completions.create(**kwargs)
```

### `_llm_loop` 400 → session-killing fallback

```2338:2347:app/gm/orchestrator.py
        try:
            response = self._chat_completion(
                messages=messages,
                tools=TOOLS if (allow_tools and depth < 3) else None,
            )
        except Exception as exc:
            log_error("chat_completion", str(exc))
            if self._last_content:
                return self._last_content
            return f"The GM falters. (API error: {exc})"
```

### OpenAI SDK (local env)

- `openai>=1.30.0` in `app/requirements.txt`; runtime **2.37.0**.
- Use `openai.BadRequestError` / `openai.APIStatusError` with `.status_code` for 400 classification.

### APP-031 → APP-032 handoff (from drift-check)

> APP-032 should reuse `sanitize_transcript_messages` / `_safe_prefix_fallback` after truncate — shared primitive ready.

### Grooming context (ticket Notes)

Pair with APP-031 (prevent) and APP-080 (arg normalization, done). P1 because single malformed transcript currently kills the turn loop with no repair.
