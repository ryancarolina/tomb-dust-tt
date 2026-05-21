# Reflection: Dev plan — APP-080

**Role:** Dev (plan phase)  
**backlog_ticket:** APP-080  
**Artifact:** [plan.md](./plan.md)

## What went well

- Research-brief code paths matched live `orchestrator.py` line ranges (~1496, ~1834, ~1972, ~2086–2090) and bridge signatures on independent re-read.
- Splitting **normalize** (pure coercion) from **validate** (required fields) answers SPEC-001 without overloading return types or pushing checks into `_execute_tool`’s broad `except Exception`.
- Whitelist table ties directly to `tools.py` + bridge kwargs; resolves SPEC-002 and the ticket’s erroneous `fortune_spend.amount` row via drop, not bridge extension.

## Decisions locked for implementation

1. **Validation in `tool_args.validate_tool_args`**, invoked in each loop before dispatch — not in bridge, not inside normalize.
2. **`top_k` over `top`** when both keys present (SPEC-005).
3. **All three loops wired** — creation/combat are low risk but required by domain wire table; run spec R4 “optional” wording overridden (SPEC-003).
4. **`enter_dungeon` alias** fully owned by normalizer; delete `_execute_tool` rewrite.
5. **Log post-normalize args** in `log_tool_call` for consistent telemetry.

## Risks to watch during impl

- `_execute_tool` still passes `**args` to many non-whitelisted tools — passthrough branch must remain until incremental expansion.
- Integration test scope: prefer `_execute_tool` + mock bridge over full `_llm_loop` depth chain to keep test small.
- APP-034 `tool_arg_coerced` logging is optional; skip in v1 unless trivial hook exists.

## Open for QA plan review

- Negative validate tests for `{}` after `JSONDecodeError` on each required tool in v1 table (at minimum `remember_fact`).
- Whether `log_tool_call` should retain a duplicate pre-normalize snapshot — plan chooses post-normalize only; flag if QA wants both.

## Estimate

Single dev stream (~1 module + orchestrator wiring + tests). No workstream split unless impl discovers circular imports (unlikely: `tool_args` must not import `orchestrator`).
