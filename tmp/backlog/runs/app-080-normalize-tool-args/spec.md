# Spec: APP-080-normalize-tool-args

**Status:** draft  
**backlog_ticket:** APP-080  
**ticket_path:** [tmp/backlog/app-080-normalize-tool-args-before-dispatch.md](../../app-080-normalize-tool-args-before-dispatch.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-llm-orchestrator-spec.md`, `tmp/app-gamebridge-spec.md`

## Problem

LLM tool arguments are passed from `json.loads` directly to `GameBridge` with no type coercion or markup cleanup. Session 2026-05-20 (Fatty / Marshal Holt quest): `remember_fact` received `importance` as `"4</importance>\n</invoke>\n<invoke name=\"enter_dungeon\">..."` instead of integer `4`. `semantic.remember()` raised `TypeError` on `max(1, min(5, importance))`. `_execute_tool` returned `{ok: false}`; the tool loop retried at depth 1 with **`enter_dungeon` only** — quest fact never persisted. Gameplay continued; campaign memory for the Holt hook is missing.

**Root cause chain:** model merged/corrupted JSON for a second tool into a scalar string field → no normalization boundary → bridge/engine assume Python types → exception caught as generic tool failure → LLM chose a different tool on retry.

## Goals

- Central **`normalize_tool_args(tool_name, args)`** at the orchestrator boundary (same pattern as creation flavor sanitizers before `_compose_creation_narration`).
- **`remember_fact.importance`** regression fixed — corrupted markup string coerces to valid int 1–5.
- Bridge methods assume clean Python types; no XML stripping in bridge or engine memory layer (defense in depth in engine is non-primary).
- Predictable coercion failures return `{ok: false, error: ...}` without raising through `_execute_tool`.

## Non-goals

| Deferred | Notes |
|----------|-------|
| Code-owned quest memory from player prose | Separate feature |
| Full JSON Schema validator for every tool in v1 | Expand coercion table incrementally |
| Fixing multi-tool provider bugs at API client | Sanitize what we receive |
| `semantic.remember` belt-and-suspenders `int()` | Orchestrator is primary fix |
| B-tier LLM retry hints on `remember_fact` failure | Only if coercion alone insufficient in tests |

## Requirements

Full behavior, coercion table, and test contracts: domain spec § **Tool argument normalization (APP-080)**.

### R1: Normalization module and helpers

**Acceptance criteria**

- [ ] `normalize_tool_args(tool_name: str, args: dict) -> dict` in `app/gm/tool_args.py` (preferred) or `orchestrator.py` if module is overkill.
- [ ] `_coerce_int(value, default, *, min_v, max_v) -> int` — if `str`, extract leading digits with regex; invalid → `default`; clamp to `[min_v, max_v]`.
- [ ] `_strip_tool_markup(s: str) -> str` — remove XML/tool fragments (`</invoke>`, `<invoke`, `</parameter>`, `<parameter`, etc.) from short scalar strings when detected; apply before numeric coercion on targeted fields.
- [ ] Unknown/extra keys for tools with fixed bridge signatures are **dropped** before dispatch (e.g. spurious `amount` on `fortune_spend` — see R3 resolution).

### R2: Tool-specific coercions (v1 minimum)

**Acceptance criteria**

- [ ] **`remember_fact`:** `fact` → `str()`; `entities` → `list[str]` (drop non-strings); `importance` → int 1–5 (default 3) via `_coerce_int` + markup strip.
- [ ] **`memory_recall`:** `query` → `str()`; `top_k` → int ≥ 1 (default 5); accept legacy alias `top` → rename to `top_k` (APP-048 name fix; APP-080 type fix).
- [ ] **`fortune_spend`:** `character_id` → `str()` + markup strip; **no `amount` param** in app tool schema or bridge — drop if present (see R3).
- [ ] **`clock_tick`:** `clock` → `str()`; `segments` → int ≥ 1 (default 1).
- [ ] **`enter_dungeon`:** migrate existing ad-hoc `site_id` → `site_address` alias from `_execute_tool` into `normalize_tool_args`; coerce both to `str()`.
- [ ] **Generic fallback:** string schema fields → `str()`; array fields → ensure list, filter to expected element type where tool is listed in coercion table.

### R3: `fortune_spend.amount` mismatch resolution

**Ticket AC listed `fortune_spend.amount` — incorrect for current app surface.**

| Layer | `amount` support |
|-------|------------------|
| Engine `spend_fortune(..., amount=1)` | Yes — CLI `--amount` |
| `GameBridge.fortune_spend(character_id)` | **No** — always spends 1 |
| `tools.py` schema | **No `amount`** — only `character_id` |
| `choice_facts.tool_impact_fact` | Uses `args.get("amount", 1)` for prose when logging auto-facts |

**Spec decision:** v1 coercion targets **`fortune_spend.character_id`** (required string). Normalizer **drops** unknown keys (`amount`, etc.) so `bridge.fortune_spend(**args)` never receives unexpected kwargs. Auto-fact prose continues to default to 1 Fortune point — consistent with bridge behavior. Exposing `amount` in tools/bridge is **out of scope** for APP-080.

### R4: Wire normalization at dispatch boundaries

**Acceptance criteria**

- [ ] **`_llm_loop`:** immediately after `json.loads(tc["function"]["arguments"])`, before `_execute_tool` — **required for v1** (only path that dispatches memory tools).
- [ ] **`_combat_llm_loop_inner`:** same pattern before `_execute_combat_action` — symmetry; low risk (`combat_action` string fields).
- [ ] **`_creation_llm_loop`:** same pattern before `_execute_creation_choice` — symmetry; optional for v1 if Dev time-boxed, but ticket AC lists all three; prefer wired for consistency.
- [ ] **`JSONDecodeError` → `{}`:** when `{}` cannot satisfy required fields after normalization, `_execute_tool` returns structured `{ok: false, error: "..."}` **without** calling bridge (do not rely on bridge `TypeError` for known missing required fields).
- [ ] Remove duplicate `enter_dungeon` `site_id` rewrite from `_execute_tool` once migrated to normalizer.

### R5: Failure modes

**Acceptance criteria**

- [ ] Coercion never raises into `_execute_tool`'s bare `except Exception` for known type mismatches on v1 fields.
- [ ] Unrecoverable required field (e.g. `remember_fact` with empty/missing `fact` after normalize) → `{ok: false, error: "<field> required"}` from normalizer or early check in `_execute_tool` before bridge call.
- [ ] Optional (coordinate APP-034): when coercion changes a value or falls back to default, log `tool_arg_coerced` JSONL with tool name, field, raw → coerced.

## Test plan

```bash
cd app && python -m pytest tests/test_tool_args.py -q
cd app && python -m pytest tests/ -q
python -m pytest play/tomb_gm/tests/test_memory.py -q   # reference — no engine changes expected
```

| Test | Setup | Pass |
|------|-------|------|
| `test_coerce_int_markup_prefix` | `_coerce_int("4</importance>...", 3, min_v=1, max_v=5)` | Returns `4` |
| `test_coerce_int_invalid` | `_coerce_int("abc", 3, min_v=1, max_v=5)` | Returns `3` |
| `test_normalize_remember_fact_corrupted_importance` | Session-shaped args: valid `fact`/`entities`, corrupted `importance` string | `importance` is `int` 1–5; dict valid for `bridge.remember_fact` |
| `test_normalize_remember_fact_no_bridge_typeerror` | Same fixture through normalize + mock/`semantic.remember` | No `TypeError` on clamp |
| `test_normalize_memory_recall_top_k_string` | `{"query": "Holt", "top_k": "5"}` | `top_k == 5` (int) |
| `test_normalize_memory_recall_legacy_top` | `{"query": "Holt", "top": "3"}` | `top_k == 3`; no `top` key |
| `test_normalize_fortune_spend_drops_amount` | `{"character_id": "pc-1", "amount": "2"}` | Only `character_id` remains; str type |
| `test_normalize_enter_dungeon_site_id_alias` | `{"site_id": "breley-undercrypt"}` | `site_address` set; `site_id` removed or aliased per spec |
| `test_normalize_clock_tick_segments_string` | `{"clock": "delve", "segments": "2"}` | `segments == 2` (int) |
| `test_integration_remember_fact_ok_after_corruption` | Mock tool loop or `_execute_tool` with corrupted args | `{ok: true}`; fact persist path exercised (mock bridge assert or memory query) |

**Fixtures:** carry Holt-session `importance` payload in pytest — do not depend on gitignored `app/logs/session-2026-05-20.jsonl` in CI.

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Quest accept + dungeon entry:** Accept an NPC quest, then enter a dungeon. After session, `memory_recall` for quest giver/objective should return the quest fact (not only generic `"Player entered dungeon at room …"`).
- **Fortune spend:** Spend Fortune via GM tool path — no `unexpected keyword argument 'amount'` in logs.
- **Regression log watch:** `app/logs/session-*.jsonl` — `remember_fact` with numeric importance should show `ok: true` when LLM sends corrupted scalar strings (post-fix: coercion logged if APP-034 wired).

## Affected paths

Must match ticket **Expected files**:

- `app/gm/tool_args.py` _(new, preferred)_
- `app/gm/orchestrator.py`
- `app/tests/test_tool_args.py`
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-gamebridge-spec.md` _(cross-link only)_

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — code paths, session evidence, `fortune_spend.amount` mismatch
- **Domain truth:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — § Tool argument normalization (APP-080)
- **Bridge contract:** [tmp/app-gamebridge-spec.md](../../../app-gamebridge-spec.md) — orchestrator supplies typed args
- **Adjacent:** APP-048 (`top_k` name), APP-034 (coercion telemetry), APP-031/032 (transcript repair — orthogonal)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | PM draft — normative requirements; `fortune_spend.amount` corrected to `character_id`; coercion table in domain spec |
