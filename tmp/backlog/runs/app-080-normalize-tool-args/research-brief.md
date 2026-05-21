# Research Brief: APP-080-normalize-tool-args

**Date:** 2026-05-21
**Question:** Where do LLM tool arguments enter the app, how did corrupted `remember_fact.importance` cause a silent memory loss, and what is the minimal central normalization boundary before `GameBridge` dispatch?

**backlog_ticket:** APP-080
**ticket_path:** tmp/backlog/app-080-normalize-tool-args-before-dispatch.md
**domain_spec:** tmp/app-llm-orchestrator-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

**False.** Ticket domain spec [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) is registered in [`tmp/app-master-spec.md`](../../../app-master-spec.md) as **LLM orchestrator** (`gm/orchestrator.py`, `tools.py`, …). APP-080 already has a draft § **Tool argument normalization** in that spec (2026-05-20 changelog). No new registry row or spec file is required; PM may promote draft bullets to normative behavior and cross-link [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) on close per ticket.

## Summary

Exploration and combat tool args flow **`json.loads` → `_execute_tool` / `_execute_combat_action` → `GameBridge`** with no type coercion. The Fatty / Marshal Holt regression is confirmed in `app/logs/session-2026-05-20.jsonl`: `remember_fact` received `importance` as a string containing XML/tool markup (`"4</importance>…<invoke name=\"enter_dungeon\">…"`), `semantic.remember()` raised `TypeError` on `max(1, min(5, importance))`, `_execute_tool` returned `{ok: false}`, and the loop retried at depth 1 with **`enter_dungeon` only** — quest text never persisted. A generic `tool_impact_fact` for `enter_dungeon` may still write `"Player entered dungeon at room …"` but not the Holt quest hook.

The ticket’s primary fix — **`normalize_tool_args(tool_name, args)` before dispatch** in `app/gm/tool_args.py` — matches an existing ad-hoc pattern (`enter_dungeon` renames `site_id` → `site_address` inside `_execute_tool`). Creation narration already sanitizes **LLM prose** (`strip_llm_status_tags`, table strippers) but not **tool JSON**. APP-048 fixed `memory_recall`’s `top_k` **name**; string-typed `top_k` would still break `scored[:top]` in `semantic.recall`. v1 should focus on `_llm_loop` + `remember_fact` regression; creation/combat loops are lower risk but listed in ticket AC for symmetry.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Exploration tool loop | `app/gm/orchestrator.py` — `_llm_loop`, `_execute_tool` | Only path that dispatches `remember_fact`, `memory_recall`, etc. |
| Combat tool loop | `app/gm/orchestrator.py` — `_combat_llm_loop_inner`, `_execute_combat_action` | Single tool `combat_action`; no memory tools |
| Creation tool loop | `app/gm/orchestrator.py` — `_creation_llm_loop`, `_execute_creation_choice` | Only `set_creation_choice`; bypasses `_execute_tool` |
| Tool schemas | `app/gm/tools.py` | `importance` / `top_k` / `segments` declared `integer` |
| Bridge memory | `app/gm/bridge.py` — `remember_fact`, `memory_recall` | Thin wrappers to `tomb_gm.services.memory` |
| Engine memory | `play/tomb_gm/services/memory/semantic.py` — `remember`, `recall` | `importance` clamp assumes `int`; `recall` slices with `top: int` |
| Auto memory on success | `play/tomb_gm/services/memory/choice_facts.py` — `tool_impact_fact` | `enter_dungeon` → generic room fact, not quest prose |
| Orchestrator auto-remember | `app/gm/orchestrator.py` — `_remember_player_choice` | Called after successful tools; swallows exceptions |
| Narration sanitizers (not args) | `app/gm/creation.py` — `strip_llm_status_tags`, table strippers | APP-073 pattern; pre-`_compose_creation_narration` |
| Logging | `app/gm/logger.py` — `log_tool_call` | Logs raw `args` + `result` (gitignored `app/logs/`) |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | **gitignored**; present locally; verified 2026-05-21 |
| Tests (gap) | `app/tests/` | No `test_orchestrator.py`; ticket expects `test_tool_args.py` |

## Code-path traces

### Fatty / Holt `remember_fact` failure (exploration)

1. **Entry:** Player input @ `19:51:35` — `"I accept your quest…"` (`session-2026-05-20.jsonl` event index 11141).
2. **`_llm_loop` depth 0:** `chat_completion` → `tool_calls` (1 call) (`orchestrator.py` ~1968–1976).
3. **Parse:** `args = json.loads(tc["function"]["arguments"])` — no normalization (~1972).
4. **Dispatch:** `_execute_tool("remember_fact", args)` → `bridge.remember_fact(**args)` (~2064–2065).
5. **Engine:** `remember_fact` → `semantic.remember` → `importance = max(1, min(5, importance))` with `str` → **TypeError** (`semantic.py` ~22).
6. **Catch:** `_execute_tool` `except Exception` → `{ok: false, error: "'<' not supported…"}` (~2115–2116); `log_tool_call` records corrupted args (~1977).
7. **Retry:** `messages` get system TOOL FAILED + tool result; `_llm_loop` depth 1 (~1993–2015).
8. **Recovery:** Second response → `enter_dungeon` `{ok: true}` (~11147); `tool_impact_fact` may persist generic dungeon entry (~1982–1984).
9. **Exit:** Narration plays; **quest-specific `remember_fact` never committed**.

### Normal exploration tool dispatch (target boundary)

1. **Entry:** `_llm_loop` / `_execute_tool` as above.
2. **New step (APP-080):** `args = normalize_tool_args(fn_name, args)` immediately after `json.loads` (and after `JSONDecodeError` → `{}` policy decided in spec).
3. **Dispatch:** `_execute_tool` receives typed/coerced dict; bridge assumes clean types.
4. **Failure mode:** Unrecoverable required fields → `{ok: false, error: …}` from normalizer **without** raising (ticket AC).

### `memory_recall` / APP-048

1. **Entry:** `_execute_tool` → `bridge.memory_recall(**args)`.
2. **Bridge:** `memory_recall(query, top_k=5)` passes `top=top_k` to `recall_facts` (APP-048 done).
3. **Risk:** LLM sends `"top_k": "5"` or legacy `"top"` → slice/type errors in `semantic.recall` unless coerced in `normalize_tool_args`.

### Creation / combat loops (secondary)

1. **`_creation_llm_loop`:** `json.loads` → `_execute_creation_choice(step, value)` (~1496–1507) — string fields only; no `remember_fact`.
2. **`_combat_llm_loop_inner`:** `json.loads` → `_execute_combat_action(**args)` (~1834–1840) — kwargs to bridge `combat_action`.
3. **Existing ad-hoc normalize:** `_execute_tool` rewrites `enter_dungeon` `site_id` → `site_address` (~2086–2090) — should migrate into `normalize_tool_args` or call it from there.

## Existing specs & docs

- **Ticket:** [`tmp/backlog/app-080-normalize-tool-args-before-dispatch.md`](../../app-080-normalize-tool-args-before-dispatch.md) — AC, coercion table, session narrative.
- **Domain spec:** [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) — draft § Tool argument normalization (APP-080).
- **Bridge spec:** [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) — Memory row; APP-048 `top_k` changelog; no “typed args from orchestrator” line yet (ticket asks on close).
- **APP-048:** [`tmp/backlog/app-048-fix-memoryrecall-topk-param.md`](../../app-048-fix-memoryrecall-topk-param.md) — param name fix only; coercion still APP-080.
- **Adjacent:** APP-031/032 (transcript repair), APP-034 (tool-chain logging), APP-073 (creation **narration** sanitizers, not tool args).

## Tests & commands

```bash
# New unit tests (ticket)
cd app && python -m pytest tests/test_tool_args.py -q

# Regression guard — no orchestrator tests exist yet
cd app && python -m pytest tests/ -q

# Engine memory (reference)
python -m pytest play/tomb_gm/tests/test_memory.py -q
```

**Suggested unit cases (from ticket):**

- `_coerce_int("4</importance>…", 3, min_v=1, max_v=5)` → `4`
- `_coerce_int("abc", 3, …)` → `3`
- `normalize_tool_args("remember_fact", {corrupted importance, valid fact/entities})` → `importance: int`, no exception through `semantic.remember`
- Integration: mock `_llm_loop` or `_execute_tool` with corrupted args → `{ok: true}` for `remember_fact`

**Session replay (human / local):** `app/logs/session-2026-05-20.jsonl` — Fatty quest turn ~`19:51:38`; grep `remember_fact` + `enter_dungeon`.

## Risks & unknowns

| Risk | Detail |
|------|--------|
| Markup stripping false positives | Regex cleanup on `fact` could damage legitimate prose containing `</invoke>` or `<parameter` (rare). Ticket says minimum on short scalars first. |
| Corruption in `fact` string | Holt case poisoned only `importance`; full multi-tool JSON merge into `fact` may need broader strip — test with session-shaped fixtures. |
| `JSONDecodeError` → `{}` | Empty args may cause confusing bridge errors vs explicit normalization failure; spec should define behavior per tool. |
| Ticket AC vs scope | `fortune_spend.amount` in ticket table but **`tools.py` has no `amount`** (only `character_id`); `tool_impact_fact` references `args.get("amount", 1)` — coerce `character_id` str, not amount. |
| All three loops wired | Creation/combat benefit less; wiring `_creation_llm_loop` is optional for v1 if PM agrees. |
| Defense in depth | `semantic.remember` `int()` belt-and-suspenders is explicitly **non-primary** per ticket. |
| Log gitignore | CI clones may lack `session-2026-05-20.jsonl`; pytest fixtures must carry regression payload. |
| APP-034 telemetry | `tool_arg_coerced` JSONL is optional; avoid duplicate/noisy logs without coordination. |

## Raw notes

### Session evidence (verified locally)

```
11141 19:51:35 INPUT  I accept your quest and will head for the undercrypt
11143 19:51:38 LLM_RESP tools=1
11144 19:51:38 TOOL remember_fact ok=False error='<' not supported between instances of 'str' and 'int'
  args.importance: "4</importance>\n</invoke>\n<invoke name=\"enter_dungeon\">..."
11146 19:51:40 LLM_RESP tools=1
11147 19:51:40 TOOL enter_dungeon ok=True
```

`log_llm_response` stores only tool **names**, not raw argument JSON — debugging corrupted args requires `tool_call` log lines or APP-034 enhancements.

### `json.loads` call sites in `orchestrator.py`

| Line | Loop | Next handler |
|------|------|----------------|
| ~1496 | `_creation_llm_loop` | `_execute_creation_choice` |
| ~1834 | `_combat_llm_loop_inner` | `_execute_combat_action` |
| ~1972 | `_llm_loop` | `_execute_tool` |

### `_execute_tool` exception envelope

```2017:2116:app/gm/orchestrator.py
    def _execute_tool(self, name: str, args: dict) -> dict:
        try:
            ...
            elif name == "remember_fact":
                return self.bridge.remember_fact(**args)
            ...
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
```

Known type errors surface as tool failure, not crash — but **failed `remember_fact` is not retried** as a dedicated tool; LLM chooses a different tool on next depth.

### `semantic.remember` clamp

```11:22:play/tomb_gm/services/memory/semantic.py
def remember(
    ...
    importance: int = 3,
    ...
) -> int:
    importance = max(1, min(5, importance))
```

### Prior art: narration vs args

- **APP-073:** `strip_llm_status_tags`, `strip_flavor_race_table` on **assistant text** before UI (`creation.py`, `orchestrator._compose_creation_narration`).
- **APP-080:** Same *boundary idea* for **structured tool args** before bridge.

### `tool_impact_fact` after `enter_dungeon` success

```160:162:play/tomb_gm/services/memory/choice_facts.py
    if tool_name == "enter_dungeon":
        room = result.get("room_id") or result.get("room", "?")
        return f"Player entered dungeon at room {room}."
```

Does not substitute for quest `remember_fact` content.

### APP-048 status

Bridge signature `memory_recall(self, query: str, top_k: int = 5)` — name aligned. String `top_k` from LLM still a latent bug class for APP-080 coercion table.
