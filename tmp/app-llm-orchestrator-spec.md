# Spec — App LLM Orchestrator

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/orchestrator.py`, `tool_args.py`, `tools.py`, `context.py`, `system_prompt.py`, `openrouter.py`, `choice_memory.py`

---

## Spec

Turn loop: **player input → context → LLM (+ tools) → narration → UI/TTS**.

### Mechanical truth (non-negotiable)

**Code state leads narration.** Player must not see outcomes (PRE_DELVE, combat hits, site entry, loot) unless the matching bridge/tool call returned `"ok": true`.

### Modes

| Mode | When | Behavior |
|------|------|----------|
| Creation | `creation.active` | Only creation handlers — no exploration tool loop; `_llm_loop` blocked when active |
| Combat | `combat.active` or engine combat | `combat_fsm` + combat tools |
| Exploration | default | `status`/`check`/`suggest` context + full tool set |

### Tools (`tools.py`)

Schemas must match `bridge.py` method signatures. When adding a tool:

1. Add bridge method (gamebridge spec).
2. Add tool schema here.
3. Add handler in `orchestrator._dispatch_tool`.
4. Update `system_prompt.py` usage rules.
5. Update this spec checklist.

**APP-080:** LLM JSON args are normalized in orchestrator (`normalize_tool_args`) before bridge dispatch — bridge assumes clean Python types. See [APP-080](backlog/app-080-normalize-tool-args-before-dispatch.md) and [GameBridge spec](app-gamebridge-spec.md) (typed-args contract).

### Tool argument normalization (APP-080)

**Problem:** Raw `json.loads` output may contain string-typed integers, XML/tool markup bleed from merged tool calls, or legacy param names. Passing these to `GameBridge` causes `TypeError` (e.g. `remember_fact.importance` → `semantic.remember` clamp) and silent memory loss when the LLM retries a different tool.

**Boundary:** Same pattern as creation flavor sanitizers (APP-073) — sanitize **structured tool args** before mechanical dispatch, not assistant prose.

| Step | Location | Action |
|------|----------|--------|
| 1 | `_llm_loop`, `_combat_llm_loop_inner`, `_creation_llm_loop` | `args = json.loads(...)`; on `JSONDecodeError` → `{}` |
| 2 | Same | `args = normalize_tool_args(fn_name, args)` |
| 3 | Same | `err = validate_tool_args(fn_name, args)`; if `err` → `{ok: false, error: err}` and skip dispatch |
| 4 | `_execute_tool` / `_execute_combat_action` / `_execute_creation_choice` | Dispatch with coerced dict; bridge assumes clean types |

**Module:** `app/gm/tool_args.py` (preferred).

#### Helpers

| Function | Contract |
|----------|----------|
| `normalize_tool_args(tool_name, args) -> dict` | Tool-specific coercions + generic fallbacks; drops unknown keys for tools with fixed bridge signatures; never raises |
| `validate_tool_args(tool_name, args) -> str \| None` | After normalize: returns `"<field> required"` or `None`; orchestrator loops short-circuit before bridge |
| `_coerce_int(value, default, *, min_v, max_v) -> int` | If `str`, strip markup then extract leading digits via regex; invalid → `default`; clamp to `[min_v, max_v]` |
| `_strip_tool_markup(s: str) -> str` | Remove fragments: `</invoke>`, `<invoke`, `</parameter>`, `<parameter`, etc. — apply on short scalars before numeric coercion |

#### Coercion table (v1)

| Tool | Field | Coercion |
|------|-------|----------|
| `remember_fact` | `fact` | `str()`; required — empty/missing → normalization failure |
| `remember_fact` | `entities` | `list[str]`; drop non-strings; default `[]` |
| `remember_fact` | `importance` | int 1–5; default 3; markup strip + `_coerce_int` — **regression:** `"4</importance>…"` → `4` |
| `memory_recall` | `query` | `str()`; required |
| `memory_recall` | `top_k` | int ≥ 1; default 5; string `"5"` → `5` |
| `memory_recall` | `top` (legacy) | Rename to `top_k` then coerce (APP-048 name + APP-080 type) |
| `fortune_spend` | `character_id` | `str()` + markup strip; required |
| `fortune_spend` | `amount` | **Drop** — not in app tool schema or bridge; engine CLI supports `amount`; bridge always spends 1 |
| `clock_tick` | `clock` | `str()`; required |
| `clock_tick` | `segments` | int ≥ 1; default 1 |
| `enter_dungeon` | `site_address` / `site_id` | `str()`; if only `site_id` present, set `site_address` from it (migrated from ad-hoc `_execute_tool` rewrite) |
| `set_creation_choice` | `step`, `value` | `str()`; both required (creation loop) |
| `combat_action` | `action`, `actor_id`, … | `str()` on present keys; `action` + `actor_id` required (combat loop) |
| Generic | string fields | `str()` on known tools when value present |
| Generic | array fields | Ensure `list`; filter element type when schema declares `items.type` |

Expand table incrementally; do not block APP-080 on every tool if `remember_fact` regression + unit tests are green.

#### Failure modes

- Coercion must **not** raise into `_execute_tool`'s generic `except Exception` for v1 fields.
- Missing/unrecoverable required field after normalize → `{ok: false, error: "<field> required"}` before bridge call.
- Optional (APP-034): log `tool_arg_coerced` JSONL when raw ≠ coerced (tool name, field, raw, coerced).

#### Non-goals (v1)

- Full JSON Schema validator for every tool.
- Code-owned quest memory from player prose.
- Markup stripping on long prose fields (`fact`) unless session evidence requires it — scalars first.
- Engine/bridge `int()` belt-and-suspenders in `semantic.remember` — orchestrator is primary.
- Exposing `fortune_spend.amount` in tools/bridge (separate ticket if needed).

---

## Task checklist

- [x] `process_turn` with creation / combat / exploration branches
- [x] Tool dispatch to GameBridge
- [x] LLM loop with depth limit for tool chains
- [x] `build_state_context` from status + recap + inventory
- [x] Block `_llm_loop` during active character creation (APP-008)
- [x] Normalize + validate LLM tool args before bridge dispatch (APP-080)

**Open work:** [APP-022](backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md), [APP-028](backlog/app-028-combat-tool-failure-narration.md), [APP-031](backlog/app-031-transcript-sanitize-orphan-tool-messages.md)–[APP-034](backlog/app-034-log-tool-chain-on-api-errors.md), [APP-077](backlog/app-077-code-owned-exploration-status-footer.md), [APP-079](backlog/app-079-finish-reason-length-recovery-policy.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Problem (from logs)

- Google 400: *Tool-call assistant message produced no valid function calls but is followed by tool result messages*
- SQLite cross-thread error (2026-05-18)

---

## Tests

```bash
cd app && python -m pytest tests/test_tool_args.py -q
cd app && python -m pytest tests/ -q
```

**APP-080 (`test_tool_args.py`):**

| Case | Expected |
|------|----------|
| `_coerce_int("4</importance>…", 3, min_v=1, max_v=5)` | `4` |
| `_coerce_int("abc", 3, …)` | `3` (default) |
| `normalize_tool_args("remember_fact", {corrupted importance, valid fact/entities})` | `importance: int`; no `TypeError` through bridge/memory |
| `normalize_tool_args("memory_recall", {"query": "x", "top_k": "5"})` | `top_k == 5` |
| `normalize_tool_args("memory_recall", {"query": "x", "top": "3"})` | `top_k == 3`; no `top` key |
| `normalize_tool_args("fortune_spend", {"character_id": "pc-1", "amount": "2"})` | only `character_id`; no `amount` |
| Integration: corrupted `remember_fact` through `_execute_tool` | `{ok: true}`; fact persist path (mock bridge or memory assert) |

Use pytest fixtures for Holt-session `importance` payload — not gitignored session JSONL in CI.

- Mock LLM tests in `app/tests/test_orchestrator.py` (when added).
- Session JSONL: every tool call logged with result.

---

## File map

| File | Role |
|------|------|
| `orchestrator.py` | Turn loop, creation/combat branches |
| `tool_args.py` | `normalize_tool_args`, `validate_tool_args`, `_coerce_int`, markup strip (APP-080) |
| `tools.py` | OpenAI function schemas |
| `context.py` | State block for LLM |
| `system_prompt.py` | GM persona + rules |
| `openrouter.py` | API client, history sanitize |
| `choice_memory.py` | Creation choice recall |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | APP-080 done: `tool_args.py` + three-loop wire (`normalize_tool_args` → `validate_tool_args` → dispatch); Holt `remember_fact` regression tests green; optional `tool_arg_coerced` logging deferred (APP-034) |
| 2026-05-21 | APP-080 PM spec: normative § Tool argument normalization — coercion table, helpers, wire points, tests; `fortune_spend.amount` corrected to `character_id` + drop unknown keys |
| 2026-05-20 | APP-080 spec draft: § Tool argument normalization — `normalize_tool_args` before bridge; `remember_fact.importance` coercion (Fatty/Holt session) |
| 2026-05-20 | APP-008: `_llm_loop` blocked when `creation.active` |
| 2026-05-20 | Spec created; merged mechanical-truth + llm-transcript-resilience content |
