# Reflection: Dev impl WS1 — APP-080

**Date:** 2026-05-21  
**Stream:** WS1 — Tool-args module  
**Agent:** Dev  
**Files:** `app/gm/tool_args.py` (new)

## What shipped

- New boundary module `app/gm/tool_args.py` with no orchestrator imports.
- Helpers: `_strip_tool_markup`, `_coerce_int`, `_coerce_str` (optional markup strip), `_coerce_str_list`.
- `_ALLOWED_KEYS` frozenset whitelist for all seven v1 tools.
- `normalize_tool_args` — per-tool branches, never raises (try/except fallback to shallow copy); unknown tools passthrough.
- `validate_tool_args` — separate required-field checks returning `"<field> required"` or `None`.

## Design choices

| Choice | Rationale |
|--------|-----------|
| `strip_markup=False` on `remember_fact.fact` | Plan/scalar-only rule — long quest prose must not be truncated |
| `top_k` wins when both `top` and `top_k` present | SPEC-005; tested inline |
| `bool` → default in `_coerce_int` | Avoid `True`/`False` becoming 1/0 via Python bool/int subclass |
| Normalizer try/except → raw copy | Belt on "never raises" contract if a branch regresses |
| `_coerce_str_list` drops non-strings | Spec says filter, not coerce — mixed lists lose int entries |

## Holt regression path (verified inline)

```
normalize_tool_args("remember_fact", {..., importance: "4</importance>..."})
  → importance: int 4
validate_tool_args → None
semantic.remember(..., importance=4) — no TypeError
```

## Out of scope (deferred streams)

- `app/gm/orchestrator.py` wire at three `json.loads` sites — **WS2**
- `app/tests/test_tool_args.py` formal pytest matrix — **WS3**
- `log_tool_arg_coerced` telemetry — APP-034 / optional

## Tests run (WS1 inline, no pytest file)

Executed from `app/` via `python -c` asserting plan matrix:

| Check | Result |
|-------|--------|
| Module import | pass |
| `_coerce_int` markup prefix → 4 | pass |
| `_coerce_int` invalid → default 3 | pass |
| `_strip_tool_markup` truncates `</invoke>` tail | pass |
| `remember_fact` corrupted importance → int 4 | pass |
| `semantic.remember` with coerced args — no TypeError | pass |
| `memory_recall` string `top_k`, legacy `top`, `top_k` wins | pass |
| `fortune_spend` drops `amount` | pass |
| `enter_dungeon` `site_id` → `site_address` only | pass |
| `clock_tick` string `segments` → 2 | pass |
| validate missing `fact` / `query` / `character_id` | pass |
| unknown tool passthrough + validate None | pass |

## Risks / notes for WS3

- Formal pytest should import `_coerce_int`, `_strip_tool_markup` from `gm.tool_args` — already public enough for tests.
- Integration test `_execute_tool` + Holt fixture belongs in WS3; module alone is sufficient for unit coverage.
- WS2 must remove ad-hoc `site_id` rewrite in orchestrator once wired.

## Done when (WS1 gate)

```bash
cd app && python -c "from gm.tool_args import normalize_tool_args, validate_tool_args"
```

Met.
