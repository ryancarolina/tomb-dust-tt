# Spec: APP-031-transcript-sanitize-orphan-tool-messages

**Status:** draft  
**backlog_ticket:** APP-031  
**ticket_path:** [tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md](../../app-031-transcript-sanitize-orphan-tool-messages.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-llm-orchestrator-spec.md`

## Problem

Multi-depth tool loops in `orchestrator.py` accumulate ephemeral `messages` arrays across `_llm_loop`, `_creation_llm_loop`, and `_combat_llm_loop_inner`. When the model emits malformed `tool_calls` (merged XML/markup in arguments, empty arrays, or missing `id`/`function.name`), the orchestrator still appends matching `tool` result messages and recurses. The next `chat_completion` resubmits an array where a provider (notably Google via OpenRouter) rejects:

```text
Tool-call assistant message produced no valid function calls but is followed by tool result messages
```

Session 2026-05-20 (Holt / `remember_fact` corruption, paired with APP-080 research) showed gameplay could continue after tool failure, but depth ≥1 API calls remain fragile. APP-080 coerces args before dispatch but **does not** repair the transcript. There is **no** message-array sanitizer in code today; domain spec file-map note on `openrouter.py` “history sanitize” is aspirational.

Persisted `self.history` stores only `{role: user|assistant, content}` — tool rounds are dropped before persist — so the failure surface is **in-turn** arrays only.

## Goals

- **Proactive** repair: every `chat_completion` receives a sanitized `messages` array that satisfies OpenAI chat tool-message invariants (widest OpenRouter provider compatibility).
- No orphan `tool` role entries without a matching, valid preceding assistant `tool_calls` entry.
- Preserve valid multi-tool chains (all matched IDs kept; loop behavior unchanged).
- Single shared helper reusable by APP-032 (reactive 400 truncate/retry) without duplicating repair logic.

## Non-goals

| Deferred | Owner |
|----------|-------|
| Reactive 400 catch, truncate `messages`/`history`, retry once | **APP-032** |
| Tool arg coercion / markup strip on scalar fields | **APP-080** (done) |
| JSONL dump of tool chain on API error | **APP-034** |
| Sanitize persisted `self.history` or `build_messages` output | Not needed today (no tool roles in history) |
| Changes to `app/gm/openrouter.py` | Ticket Expected files scope **`orchestrator.py` only** — sanitize at orchestrator pre-flight |
| Mid-chain APP-079 table strip policy changes | Orthogonal; sanitizer must not break valid assistant content |

## Requirements

Full behavior, invariants, and test contracts: domain spec § **Transcript sanitize (APP-031)**.

### R1: Sanitizer helper

**Acceptance criteria**

- [ ] `sanitize_transcript_messages(messages: list[dict]) -> list[dict]` implemented in `app/gm/orchestrator.py` (module-level function preferred for APP-032 import; private alias acceptable).
- [ ] **Non-mutating:** returns a **new** list; shallow-copies message dicts into the output. **Must not** mutate the caller’s input list or any dict already in that list (APP-032 may pass shared arrays).
- [ ] Never raises on malformed input. Apply R2 walk left-to-right; drop/reorder invalid entries. If the walk would yield an **empty** output while input was non-empty, **safe-prefix fallback:** (1) all leading `system` messages from input, in order; (2) if any `user` exists, append the **last** `user` only; (3) if no `system`/`user`, return `[]`. Empty input → `[]`.

### R2: Validity rules (target invariant)

**Acceptance criteria**

- [ ] **Valid tool_call:** non-empty string `id`; `function.name` non-empty string; `function.arguments` present (string, may be `"{}"`). Missing/invalid entries are **stripped** from the assistant’s `tool_calls` array.
- [ ] **Assistant with no valid tool_calls after strip:** emit assistant as content-only (no `tool_calls` key or empty array removed per OpenAI convention).
- [ ] **Each `tool` message:** `tool_call_id` must match an `id` from the **nearest preceding** assistant message that still has unresolved valid `tool_calls`. Unmatched `tool` messages are **dropped**.
- [ ] **No orphan tools:** after sanitize, invariant holds — no `tool` message appears when the preceding assistant (skipping only dropped messages) lacks valid `tool_calls` with that id.
- [ ] **Round-trip safety:** a already-valid multi-tool chain (assistant + N tools, all ids matched) passes through unchanged (order and content preserved).

### R3: APP-028 system-before-tool ordering

**Acceptance criteria**

- [ ] Exploration/combat failure path appends `system` “TOOL FAILED …” **between** assistant `tool_calls` and `tool` results today (~L2276–2287, ~L2091–2098). Sanitizer **reorders** so all `tool` messages for that assistant round immediately follow the assistant, then intervening `system`/`user` messages (content preserved, order fixed for provider strictness).
- [ ] TOOL FAILED text remains in the transcript (not dropped) — only ordering changes.

### R4: Wire point — before every `chat_completion`

**Acceptance criteria**

- [ ] All six orchestrator call sites sanitize immediately before `chat_completion`:
  - `_call_narration_llm` (~L1046)
  - `_narrate_only` (~L1673)
  - `_creation_llm_loop` (~L1700)
  - `_combat_llm_loop_inner` (~L2047)
  - combat narrate pass (~L2132)
  - `_llm_loop` (~L2212)
- [ ] Preferred pattern: single wrapper (e.g. `_chat_completion(messages, **kwargs)`) that runs `sanitize_transcript_messages` then delegates to `openrouter.chat_completion` — avoids six copy-pasted calls.
- [ ] **No** change to `openrouter.chat_completion` signature or behavior.

### R5: Observability (optional v1)

**Acceptance criteria**

- [ ] When sanitize drops or reorders messages, optional debug log via existing `log_error` or structured JSONL event `transcript_sanitized` with counts (`dropped_tools`, `stripped_calls`, `reordered_system`) — **defer to APP-034** if time-boxed; not blocking for APP-031 close.

### R6: APP-032 boundary

**Acceptance criteria**

- [ ] APP-031 does **not** implement 400 detection, history truncation, or retry loops.
- [ ] `sanitize_transcript_messages` is **public enough** for APP-032 to import and reuse after truncate (shared repair primitive).
- [ ] Document pairing in domain spec: **031 prevent → 032 recover**.

## Test plan

```bash
cd app && python -m pytest tests/test_transcript_sanitize.py -q
cd app && python -m pytest tests/ -q
```

| Test | Setup | Pass |
|------|-------|------|
| `test_orphan_tool_no_preceding_assistant` | `[user, {role: tool, tool_call_id: x}]` | Orphan tool removed |
| `test_assistant_empty_tool_calls_followed_by_tool` | `[assistant tool_calls: [], tool]` | Tools stripped; assistant content-only |
| `test_invalid_tool_call_missing_id` | `[assistant invalid call + tool]` | Invalid call stripped; orphan tool dropped |
| `test_valid_two_tool_chain` | Assistant + 2 matched tools | Unchanged ids and order |
| `test_unmatched_tool_call_id` | Assistant + tool A + tool B (B id wrong) | Unmatched tool B dropped; A kept |
| `test_system_between_assistant_and_tool` | assistant → system TOOL FAILED → tool | Tools immediately after assistant; system after tool block |
| `test_holt_session_shape` | Fixture: corrupted `tool_calls` args + tool result (post-APP-080 dispatch ok) | Sanitized array passes invariant checker; mock `chat_completion` receives no orphan tools |
| `test_wrapper_called_in_llm_loop` | Mock `_llm_loop` depth ≥1 | `chat_completion` kwargs `messages` satisfy invariant |
| `test_sanitize_does_not_mutate_caller_list` | Caller-owned list + dict refs | Input list length/identity and dict contents unchanged after call |
| `test_tail_invalid_returns_safe_prefix` | `[{role: tool, …}]` only, or assistant+tool where entire tail invalid | Returns `[]`; `[system, user, {role: tool}]` → `[system, user]`; `[system, system, user, assistant+orphan tool]` → `[system, system, user]` |

**Fixtures:** encode malformed arrays in pytest — do not depend on gitignored `app/logs/session-2026-05-20.jsonl`.

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Multi-tool turn:** Trigger a turn where the GM uses memory + travel/dungeon tools in one chain (e.g. accept quest fact, enter dungeon). Turn completes without “The GM falters. (API error: …)” mid-chain.
- **Tool failure recovery:** Force a tool failure (invalid site, combat illegal action). Next model call in same turn still returns narration — no session-killing 400.
- **Log watch:** `app/logs/session-*.jsonl` — no Google malformed-transcript 400 strings after fix; optional `transcript_sanitized` if wired.

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py`
- `app/tests/test_transcript_sanitize.py` _(new)_
- `tmp/app-llm-orchestrator-spec.md`

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — call sites, Holt trace, APP-028 ordering risk
- **Domain truth:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — § Transcript sanitize (APP-031)
- **Paired:** [APP-032](../../app-032-400-retry-on-malformed-transcript.md) — reactive retry after 400; schedule after or with APP-031
- **Adjacent:** [APP-080](../app-080-normalize-tool-args-before-dispatch.md) — arg coercion; [APP-034](../app-034-log-tool-chain-on-api-errors.md) — telemetry

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | PM draft — proactive transcript sanitize; APP-032 boundary; APP-028 reorder rule; orchestrator-only wire point |
| 2026-05-22 | PM r2 — ticket Expected files + test module; pinned non-mutating helper; R1 safe-prefix fallback algorithm + pytest rows |
