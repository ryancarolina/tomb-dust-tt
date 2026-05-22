# Research Brief: APP-031-transcript-sanitize-orphan-tool-messages

**Date:** 2026-05-22
**Question:** Where do in-turn LLM `messages` arrays gain orphan `tool` role entries (or invalid assistant `tool_calls`), causing provider 400s — and where should proactive transcript sanitization run before every `chat_completion`?

**backlog_ticket:** APP-031
**ticket_path:** tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md
**domain_spec:** tmp/app-llm-orchestrator-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

**False.** Ticket domain spec [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) is registered in [`tmp/app-master-spec.md`](../../../app-master-spec.md) as **LLM orchestrator** (`gm/orchestrator.py`, `openrouter.py`, …). The spec already documents the problem (§ Problem — Google 400), lists APP-031 in open work, and file map notes `openrouter.py` as “history sanitize” (not yet implemented). [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) § Known issues (2026-05-18) cross-links malformed transcript. No new registry row required.

## Summary

There is **no transcript sanitizer in code today**. `app/gm/openrouter.py` only wraps `client.chat.completions.create`; domain spec’s “history sanitize” is aspirational. All existing “sanitize” helpers (`sanitize_premature_site_entry_flavor`, `_sanitize_creation_flavor`, APP-073/080) target **player-facing prose or tool args**, not the API `messages` array.

Orphan / malformed tool transcripts are built **inside the turn**, in ephemeral `messages` lists passed through `_llm_loop`, `_creation_llm_loop`, and `_combat_llm_loop_inner`. Persisted `self.history` stores only `{role: user|assistant, content: str}` pairs — tool rounds are not saved across turns (`_restore_history` ~L241–251).

Three loops append `assistant` + `tool_calls` then `tool` results without validating structure before the next `chat_completion`. On tool failure (APP-028), exploration and combat insert a **`system` “TOOL FAILED” line between the assistant `tool_calls` message and the matching `tool` result** (~L2276–2287, ~L2091–2098). That ordering may be tolerated by some routes but is a latent strict-provider failure mode.

The groomed failure mode (session 2026-05-20, paired with APP-080 research) is **multi-tool / merged-invoke corruption**: model emits malformed `tool_calls` (e.g. `remember_fact` args bleeding `</invoke><invoke name="enter_dungeon">`), orchestrator still appends `tool` results for parsed IDs, and the **next** depth’s API call resubmits an array where upstream (Google via OpenRouter) sees an assistant message with **no valid function calls** followed by `tool` messages — matching the domain spec error string. APP-080 coerces args before dispatch but **does not** repair the transcript. APP-032 (reactive 400 → truncate/retry once) is the safety net; APP-031 is **proactive** repair before send.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| API client | `app/gm/openrouter.py` — `chat_completion` | No message validation; returns normalized `tool_calls` list |
| Exploration tool loop | `app/gm/orchestrator.py` — `_llm_loop` (~L2187–2320) | Primary path for `remember_fact`, travel, beats; depth ≤4 |
| Creation tool loop | `app/gm/orchestrator.py` — `_creation_llm_loop` (~L1688–1790) | `set_creation_choice` only; no TOOL FAILED system injection |
| Combat tool loop | `app/gm/orchestrator.py` — `_combat_llm_loop_inner` (~L2041–2142) | `combat_action`; second `chat_completion` for narrate uses full chain |
| Message assembly | `app/gm/context.py` — `build_messages` | System + history (user/assistant strings) + user input — **no tool roles** |
| Persisted history | `app/gm/orchestrator.py` — `self.history`, `_restore_history`, exploration turn end (~L942–946) | Tool rounds dropped before persist |
| Tool arg repair (adjacent) | `app/gm/tool_args.py` — APP-080 | Coerces args; transcript unchanged |
| Narration sanitizers (orthogonal) | `creation.py`, `orchestrator._compose_*` | Prose only |
| Error logging | `app/gm/logger.py` — `log_error`, `log_llm_request` | No tool-chain dump on 400 (APP-034) |
| Domain problem statement | `tmp/app-llm-orchestrator-spec.md` § Problem (~L379–382) | Google 400 verbatim |
| Paired ticket | `tmp/backlog/app-032-400-retry-on-malformed-transcript.md` | Reactive retry after 400 |
| Session evidence (gitignored) | `app/logs/session-2026-05-20.jsonl` | Cited in APP-080 research; not in repo clone |

## Code-path traces

### Exploration multi-depth tool chain (primary failure surface)

1. **Entry:** `process_turn` → `build_messages(..., self.history, player_input)` (~L929–937) → `_llm_loop(messages, depth=0)`.
2. **LLM call:** `chat_completion(..., messages=messages, tools=TOOLS)` (~L2212–2218) — **no pre-sanitize**.
3. **Tool round:** If `tool_calls` non-empty, append assistant with `tool_calls` (~L2247–2251); for each `tc`, dispatch via `_execute_tool`, optionally append **system TOOL FAILED** (~L2276–2282), then append `role: tool` (~L2283–2287).
4. **Early exit:** If `all_failed and content` (~L2295–2311), return composed prefix — **no further API call** (Holt `remember_fact` + empty content would **not** take this path).
5. **Recurse:** `return self._llm_loop(messages, depth + 1)` (~L2320) resubmits accumulated array including assistant/tool/system ordering from step 3.
6. **400 today:** `except Exception` (~L2220–2224) logs `chat_completion` error, returns fallback — **no repair** (APP-032 scope).

### Holt / corrupted `remember_fact` (session 2026-05-20, via APP-080 brief)

1. Depth 0: single `remember_fact` tool_call; args contain merged XML markup in `importance`.
2. Pre-APP-080: `TypeError` in `semantic.remember` → `{ok: false}`; system + tool appended; recurse depth 1.
3. Depth 1: new model response → `enter_dungeon` succeeds; turn completes (session log ~19:51:38–40).
4. **Residual risk post-APP-080:** coercion prevents TypeError, but merged markup in `arguments` JSON can still yield **structurally invalid `tool_calls`** on resubmit; sanitize must drop/repair before depth 1 call.

### Creation tool loop (secondary)

1. **Entry:** `_creation_llm_loop(messages, tools, tool_choice)` (~L1688).
2. Append assistant + `tool_calls`; append `tool` per call (~L1725–1755) — **no system injection on failure**.
3. Recurse in-loop (`for depth in range(4)`) with same `messages` list (~L1696–1708).
4. Same sanitize requirement before each `chat_completion`.

### Combat tool loop + narrate pass

1. **Entry:** `_combat_llm_loop_inner(messages, depth)` (~L2041).
2. Same assistant / system / tool append pattern as exploration (~L2068–2098).
3. On success, **second** `chat_completion` with `narrate_messages = messages + [user brief]` and `tools=None` (~L2128–2138) — full prior tool chain included; orphan tool entries would 400 here too.

### Non-tool LLM calls (low risk)

| Call site | Symbol | Tool messages in input? |
|-----------|--------|-------------------------|
| ~L1046 | `_call_narration_llm` | No (creation flavor) |
| ~L1673 | `_narrate_only` | Unlikely |

Sanitize at a shared pre-flight (wrapper or helper) still safe for these paths.

## Existing specs & docs

- **Ticket:** [`tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md`](../../app-031-transcript-sanitize-orphan-tool-messages.md) — AC: no orphan tool messages without preceding `tool_calls`.
- **Domain spec:** [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) — § Problem (400 string); open work APP-031–034; file map lists `openrouter.py` sanitize (unimplemented).
- **APP-032:** [`tmp/backlog/app-032-400-retry-on-malformed-transcript.md`](../../app-032-400-retry-on-malformed-transcript.md) — reactive repair + single retry; same Expected file; schedule **after or with** APP-031 (prevent first, recover second).
- **APP-080:** [`tmp/backlog/runs/app-080-normalize-tool-args/research-brief.md`](../app-080-normalize-tool-args/research-brief.md) — Holt session trace; adjacent, not duplicate.
- **APP-034:** tool-chain logging on API errors — complements debug story.
- **APP-028:** TOOL FAILED system injection — ordering risk when sanitizing.

## Tests & commands

```bash
# Baseline (no transcript tests yet)
cd app && python -m pytest tests/ -q

# Likely new module (PM/Dev — not in ticket Expected files; confirm in plan)
cd app && python -m pytest tests/test_transcript_sanitize.py -q
```

**Suggested unit cases (for PM spec):**

| Case | Expected |
|------|----------|
| `tool` message with no preceding assistant `tool_calls` | Removed or paired with synthetic assistant |
| Assistant `tool_calls: []` followed by `tool` | Orphan tools stripped; assistant de-tool’d |
| Assistant with invalid `tool_calls` (missing `id` / `function.name`) + `tool` | Invalid calls stripped; orphan tools removed |
| Valid assistant + two tools, one `tool_call_id` unmatched | Unmatched `tool` dropped |
| Exploration failure transcript: assistant → system TOOL FAILED → tool | Sanitized array accepted by mock API / invariants pass |
| Round-trip: sanitize does not mutate valid multi-tool chain | All IDs preserved |

**Integration:** Mock `chat_completion` to assert `messages` passed in at depth ≥1 never contain orphan tools (pattern from `test_exploration_site_entry_gate.py`, `test_combat_failure_narration.py`).

## Risks & unknowns

| Risk | Detail |
|------|--------|
| **System-before-tool ordering** | APP-028 inserts `system` between assistant `tool_calls` and `tool` results. Strict providers may treat following `tool` as orphan. Sanitizer may need to reorder (tool immediately after assistant) or fold failure into `tool.content`. |
| **Over-stripping valid chains** | Aggressive removal of `tool` messages loses mechanical context for the model; prefer drop orphan over truncating whole turn. |
| **Expected files scope** | Ticket lists only `orchestrator.py`; spec file map suggests `openrouter.py`. PM should pick one choke point (`sanitize_messages` in orchestrator called before each local `chat_completion` vs wrap in `openrouter.chat_completion`). |
| **APP-031 vs APP-032 boundary** | 031 = always sanitize before send; 032 = catch remaining 400, truncate `messages`/`history`, retry once. Avoid duplicate logic — shared repair helper. |
| **Persisted history** | Currently safe (no tool roles). If future tickets persist full tool chains, sanitize must also run in `build_messages` / restore path. |
| **Session logs gitignored** | Cannot re-verify 2026-05-18 400 in CI; pytest fixtures must encode malformed arrays. |
| **Provider variance** | OpenRouter routes to Google/Anthropic/etc.; sanitize should follow OpenAI chat tool message invariants (widest compatibility). |
| **Mid-chain APP-079** | Spec documents table-strip on `length` + tools; not implemented in `_llm_loop` when `tool_calls` present — future interaction with sanitizer. |

## Raw notes

### Domain spec error (target invariant)

```text
Google 400: Tool-call assistant message produced no valid function calls but is followed by tool result messages
```

### `chat_completion` call sites in `orchestrator.py` (all need pre-flight or shared wrapper)

| Line | Context |
|------|---------|
| ~1046 | `_call_narration_llm` |
| ~1673 | `_narrate_only` |
| ~1700 | `_creation_llm_loop` |
| ~2047 | `_combat_llm_loop_inner` |
| ~2132 | combat narrate (no tools) |
| ~2212 | `_llm_loop` |

### Tool append pattern (exploration)

```2247:2287:app/gm/orchestrator.py
        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls,
        })
        ...
            else:
                messages.append({
                    "role": "system",
                    "content": (
                        f"TOOL FAILED ({fn_name}): ..."
                    ),
                })
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str),
            })
```

### `_llm_loop` 400 handling (APP-032 gap)

```2220:2224:app/gm/orchestrator.py
        except Exception as exc:
            log_error("chat_completion", str(exc))
            if self._last_content:
                return self._last_content
            return f"The GM falters. (API error: {exc})"
```

### `openrouter.py` — no sanitize (spec drift)

File map claims “history sanitize”; implementation is pass-through only (~L21–63).

### APP-032 pairing (implementation order hint)

1. **APP-031:** `sanitize_messages(messages) -> messages` — enforce: every `tool` has matching `tool_call_id` on the nearest preceding assistant with valid `tool_calls`; strip empty/invalid `tool_calls` before append or on send.
2. **APP-032:** On `400` / malformed-transcript error string, truncate to last valid prefix (e.g. last user message + system) and retry **once**.

### Test gap

No `test_orchestrator.py` / `test_transcript_sanitize.py` in tree; mock patterns exist in `test_combat_failure_narration.py`, `test_exploration_site_entry_gate.py`.
