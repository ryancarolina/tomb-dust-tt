# APP-080: Normalize tool args before dispatch

| Field | Value |
|-------|-------|
| **ID** | APP-080 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-21 |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-20 |

## Summary

LLM tool arguments are passed straight from `json.loads` to `GameBridge` with no type coercion or markup cleanup. Session 2026-05-20 (Fatty / Holt quest): `remember_fact` failed because `importance` arrived as `"4</importance>\n</invoke>\n<invoke name=\"enter_dungeon\">..."` instead of integer `4`, causing `max(1, min(5, importance))` to raise `TypeError`. The tool loop recovered with `enter_dungeon`, but the **quest fact was never persisted**.

**Proper fix:** central **normalize tool args at the orchestrator** before `_execute_tool` — same boundary pattern as creation flavor sanitizers before `_compose_creation_narration`.

## Problem (observed)

**Log (`session-2026-05-20.jsonl`, 19:51:38):**

```json
{
  "name": "remember_fact",
  "args": {
    "fact": "Marshal Holt tasked Fatty with retrieving his brother's signet ring...",
    "entities": ["Marshal Holt", "Breley Undercrypt", "Holt signet ring"],
    "importance": "4</importance>\n</invoke>\n<invoke name=\"enter_dungeon\">..."
  },
  "result": { "ok": false, "error": "'<' not supported between instances of 'str' and 'int'" }
}
```

**Root cause chain:**

1. Model merged/corrupted JSON for a second tool (`enter_dungeon`) into the `importance` string (XML-style markup bleed).
2. `_llm_loop` / `_combat_llm_loop_inner` / `_creation_llm_loop` call `json.loads` then `_execute_tool(name, args)` with no normalization.
3. `bridge.remember_fact(**args)` → `semantic.remember()` → `max(1, min(5, importance))` compares `str` to `int`.
4. Exception caught in `_execute_tool` → `{ok: false}`; LLM retried **only** `enter_dungeon` at depth 1 — quest memory lost.

**Impact:** gameplay continued; **campaign memory** for Holt's quest hook missing (generic `enter_dungeon` auto-fact does not capture quest text).

## Acceptance criteria

### Decision (document in domain spec)

- [x] **Tool arg contract:** orchestrator normalizes/coerces args from LLM JSON **before** bridge dispatch; bridge methods assume clean Python types.
- [x] **Fail soft:** predictable coercion failures return `{ok: false, error: ...}` — do not rely on bare `except Exception` for known type mismatches.

### Code

- [x] `normalize_tool_args(tool_name: str, args: dict) -> dict` in `app/gm/tool_args.py` (or `orchestrator.py` if module is overkill).
- [x] `_coerce_int(value, default, *, min_v, max_v)` — if `str`, extract leading digits with regex; invalid → `default`; clamp to range.
- [x] **`remember_fact`:** coerce `importance` to `int` 1–5 (default 3); ensure `fact` is `str`; `entities` is `list[str]` (drop non-strings).
- [x] Optional string cleanup: strip XML/tool markup fragments from string fields when detected (`</invoke>`, `<parameter`, etc.) — at minimum on `importance` and other short scalar fields.
- [x] Wire `normalize_tool_args` in **all** tool dispatch paths after `json.loads`:
  - `_llm_loop`
  - `_combat_llm_loop_inner`
  - `_creation_llm_loop` (if retained)
- [x] On normalization failure (unrecoverable args for required fields), return structured error without throwing — enables LLM retry.
- [ ] Optional (B-tier): on `remember_fact` failure, system inject hints retry with integer importance and separate tools — **only if** coercion alone insufficient in tests. _(N/A — coercion sufficient; not implemented.)_

### Scope for v1 coercions (minimum)

| Tool / field | Coercion |
|--------------|----------|
| `remember_fact.importance` | int 1–5 |
| `memory_recall.top` / `top_k` | int ≥ 1 (align APP-048) |
| `fortune_spend.character_id` | `str()`; drop unknown keys (e.g. spurious `amount` — not in app schema; see run spec R3) |
| `clock_tick.*` | ints if present |
| Generic | string fields → `str()`; array fields → filter to expected element type |

Expand table in spec when implementing; do not block ticket on every tool if `remember_fact` + tests green.

### Tests

- [x] Unit: `_coerce_int("4</importance>...", 3, min_v=1, max_v=5)` → `4`.
- [x] Unit: `_coerce_int("abc", 3, ...)` → `3`.
- [x] Unit: `normalize_tool_args("remember_fact", {... corrupted importance ...})` → valid dict; `bridge.remember_fact` receives `int`.
- [x] Unit: corrupted args no longer raise from `semantic.remember`.
- [x] Integration: mock tool loop with corrupted `remember_fact` args → `{ok: true}` and fact queryable via memory (or mock bridge assert).

### Logging (optional, coordinate APP-034)

- [ ] When coercion changes a value or falls back to default, log `tool_arg_coerced` JSONL with tool name, field, raw → coerced (dev telemetry). _(Deferred to APP-034.)_

## Expected files

- `app/gm/tool_args.py` _(new, preferred)_
- `app/gm/orchestrator.py`
- `app/tests/test_tool_args.py`
- `tmp/app-llm-orchestrator-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add § **Tool argument normalization** to [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) with coercion table + changelog.
3. Cross-link from [`app-gamebridge-spec.md`](../app-gamebridge-spec.md) if bridge contract documented (“orchestrator supplies typed args”).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-034 | soft — log raw args when coercion fails |
| APP-031 / APP-032 | adjacent — transcript/API repair; orthogonal to arg typing |
| APP-048 | `memory_recall` top_k param — include in coercion table |

## Notes

### Defense in depth (target)

| Layer | Behavior |
|-------|----------|
| Prompt | “Use integer importance 1–5; one tool call per intent” (supplement only) |
| Orchestrator | `normalize_tool_args` before `_execute_tool` (**primary**) |
| Bridge | Assume clean types; no XML stripping |
| Memory | Optional belt-and-suspenders `int()` in `semantic.remember` — not primary fix |

### Non-goals

- Code-owned quest memory from player prose (separate feature).
- Full JSON Schema validator for every tool in v1 — start with coercions for known fragile fields + `remember_fact` regression.
- Fixing multi-tool provider bugs at the API client — sanitize what we receive.

### Session evidence

Fatty @ 19:51 — Holt quest narration played correctly; DB lacks explicit quest fact; `enter_dungeon` auto-fact is `"Player entered dungeon at room ..."` only (`choice_facts.tool_impact_fact`).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-080 --task normalize-tool-args
python tmp/backlog/claim_ticket.py release APP-080 --done
```
