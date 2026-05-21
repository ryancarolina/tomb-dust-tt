# QA PASS: implementation — round 1

**Task:** app-080-normalize-tool-args  
**backlog_ticket:** APP-080  
**ticket_path:** [tmp/backlog/app-080-normalize-tool-args-before-dispatch.md](../../app-080-normalize-tool-args-before-dispatch.md)  
**Round:** 1  
**domain_spec:** draft present (`tmp/app-llm-orchestrator-spec.md` § Tool argument normalization); `validate_tool_args` wire step + dated “APP-080 done” changelog pending at `release --done`

## Verdict

**PASS** — Holt regression fixed; v1 coercion module + three-loop wire + structured required-field errors match ticket AC, run `spec.md` R1–R5, and domain spec coercion table.

## Automated tests

```text
python -m pytest app/tests/test_tool_args.py -v
15 passed in 0.57s

python -m pytest app/tests/ -q
100 passed in 11.05s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_tool_args.py` | 15 (helpers, normalize, validate, integration) | ✓ |
| Full `app/tests/` | 100 (regression) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Tool arg contract: normalize before bridge | `tool_args.py`; import + wire at `_creation_llm_loop` L1571, `_combat_llm_loop_inner` L1912, `_llm_loop` L2084 | ✓ |
| Fail soft — no bare `TypeError` on v1 type mismatches | `normalize_tool_args` never raises (L149–161 try/except); Holt path coerces `importance` → int before `bridge.remember_fact` | ✓ |
| `normalize_tool_args` in `app/gm/tool_args.py` | New module with `_NORMALIZERS` registry | ✓ |
| `_coerce_int` — leading digits, invalid → default, clamp | L36–50; `test_coerce_int_markup_prefix`, `test_coerce_int_invalid` | ✓ |
| `remember_fact` — fact str, entities list[str], importance int 1–5 | `_normalize_remember_fact` L76–82; Holt fixtures | ✓ |
| Markup strip on short scalars | `_strip_tool_markup` L24–33; applied in `_coerce_int` / `_coerce_str`; `fact` exempt (`strip_markup=False`) per spec non-goals | ✓ |
| Wire all three `json.loads` paths | Creation L1568–1578, combat L1909–1918, exploration L2081–2088 | ✓ |
| Required-field errors before bridge | `validate_tool_args` L164–191; loops set `{ok: false, error: err}` and skip dispatch | ✓ |
| v1 coercion table (memory, fortune, clock, enter_dungeon) | Per-tool normalizers + `_ALLOWED_KEYS`; unit tests for each row | ✓ |
| Remove ad-hoc `enter_dungeon` `site_id` rewrite | `rg` on `orchestrator.py`: no `site_id`→`site_address` pop; alias in `_normalize_enter_dungeon` L110–118 | ✓ |
| Unit: corrupted `importance` → int | `test_normalize_remember_fact_corrupted_importance` | ✓ |
| Unit: no `semantic.remember` TypeError | `test_normalize_remember_fact_no_typeerror_via_semantic` | ✓ |
| Integration: corrupted args → `{ok: true}` | `test_execute_tool_remember_fact_corrupted_importance_ok` via `_dispatch_like_llm_loop` | ✓ |
| APP-034 `tool_arg_coerced` logging | Not implemented — optional per ticket/plan | deferred |
| B-tier retry hints on `remember_fact` failure | Not implemented — optional “only if coercion insufficient” | N/A (coercion sufficient) |

## Run spec R1–R5 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Module + helpers + drop unknown keys | `tool_args.py`; `_ALLOWED_KEYS` + `_apply_whitelist` | ✓ |
| **R2** | v1 tool coercions | Seven normalizers in `_NORMALIZERS` | ✓ |
| **R3** | `fortune_spend` drop `amount` | Whitelist + `test_normalize_fortune_spend_drops_amount` | ✓ |
| **R4** | Three loops + JSONDecodeError → `{}` + remove duplicate rewrite | Loops traced; empty `{}` → validate → `"<field> required"` | ✓ |
| **R5** | Coercion never raises; required fields structured error | try/except in normalize; validate before `_execute_tool` | ✓ |

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| Holt regression (exploration loop) | `json.loads` → `normalize_tool_args("remember_fact", …)` → `validate_tool_args` → `_execute_tool` → `bridge.remember_fact` | `importance` int 4; no clamp TypeError |
| Legacy `memory_recall.top` | `_normalize_memory_recall` L89–90 → output `top_k` only | ✓ |
| `top_k` wins over `top` | L87–88 branch order | `test_normalize_memory_recall_top_k_wins_over_top` |
| Combat loop symmetry | `_combat_llm_loop_inner` normalize + validate before `_execute_combat_action(**args)` | ✓ |
| Creation loop symmetry | `_creation_llm_loop` normalize + validate before `_execute_creation_choice` | ✓ |
| Unknown v1 tool keys | e.g. `fortune_spend.amount` dropped post-coerce | ✓ |
| Non-v1 tools (e.g. `world_travel`) | `normalize_tool_args` passthrough raw dict; validate returns `None` | unchanged pre-APP-080 behavior (spec: expand incrementally) |

**Wire order (all three loops):** `json.loads` (or `{}` on decode error) → `normalize_tool_args` → `validate_tool_args` → dispatch or `{ok: false, error}`.

## Plan QA notes — resolution

| Plan note | Impl resolution |
|-----------|-----------------|
| Validate tests partial (3 of 8 tools) | `validate_tool_args` implements all eight v1 tools; unit tests cover `remember_fact`, `memory_recall`, `fortune_spend` only — acceptable per plan adversarial note |
| Integration via helper not `_llm_loop` | `_dispatch_like_llm_loop` matches production loop contract; orchestrator sites independently traced |
| Spec wire table missing validate step | Impl correct; domain spec sync deferred to `release --done` (SPEC-006) |
| `log_tool_call` logs post-normalize args only | Confirmed at all three sites — raw LLM transcript unchanged |

## Adversarial notes (non-blocking)

1. **Validate unit coverage gap** — No pytest for `clock_tick`, `enter_dungeon`, `set_creation_choice`, or `combat_action` required-field errors; code paths exist in `validate_tool_args` and are exercised in loops when LLM omits fields.
2. **Non-v1 tools unnormalized** — Tools outside `_NORMALIZERS` still pass raw JSON to bridge; string-typed ints on unlisted tools can still `TypeError` — consistent with spec “expand incrementally.”
3. **Integration test name** — Spec lists `test_integration_remember_fact_ok_after_corruption`; shipped as `test_execute_tool_remember_fact_corrupted_importance_ok` (same behavior).
4. **Release / drift** — Ticket still `in_progress`; domain spec wire table should add validate step + changelog on close; `app-master-spec.md` owns row per SPEC-006.
5. **Human playtest** — Not run this round (Stage 7: Holt quest accept + dungeon entry + Fortune spend log watch).

## Handoff

**Ready for:** Stage 6 drift check + `release APP-080 --done` (ticket AC checkboxes, Closed date, domain spec changelog + validate wire row).  
**Human playtest:** After quest accept + dungeon entry, `memory_recall` for quest giver should return Holt fact; session JSONL should show `remember_fact` `ok: true` with coerced numeric importance.
