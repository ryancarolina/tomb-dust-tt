# Drift Check: APP-080-normalize-tool-args

**backlog_ticket:** APP-080  
**Verdict:** PASS (synced)

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) | was yes (wire table omitted `validate_tool_args`; APP-080 still in open work; changelog “done” missing) | **Synced:** wire steps 1–4, `validate_tool_args` in Helpers, creation/combat rows in coercion table, checklist `[x]`, changelog **APP-080 done** |
| [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) | was minor (checklist lag) | **Synced:** checklist `[x]` typed-args; changelog **APP-080 done** |
| Run [`spec.md`](./spec.md) R1–R5 | no | Verified against `tool_args.py`, `orchestrator.py`, `test_tool_args.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| `normalize_tool_args` + `_coerce_int` + markup strip | `app/gm/tool_args.py` | yes |
| `validate_tool_args` before dispatch | `tool_args.py` L164–191; loops L1575, L1915, L2085 | yes |
| v1 coercion table (`remember_fact`, `memory_recall`, `fortune_spend`, `clock_tick`, `enter_dungeon`) | `_NORMALIZERS` + unit tests | yes |
| `set_creation_choice` / `combat_action` (loop symmetry) | Normalizers + validate rules | yes (added to spec table at drift close) |
| Three-loop wire after `json.loads` | `_creation_llm_loop`, `_combat_llm_loop_inner`, `_llm_loop` | yes |
| Holt regression — corrupted `importance` → int 4, `{ok: true}` | `test_coerce_int_markup_prefix`, integration test | yes |
| Drop `fortune_spend.amount` | `_ALLOWED_KEYS` whitelist | yes |
| `enter_dungeon` `site_id` alias in normalizer (not `_execute_tool`) | `_normalize_enter_dungeon` | yes |
| Fail soft — no `TypeError` on v1 scalars | normalize never raises; validate short-circuits | yes |
| Bridge assumes clean types | `app-gamebridge-spec.md` § Typed args | yes |
| Optional `tool_arg_coerced` JSONL | not implemented | deferred (APP-034; spec optional) |
| B-tier retry hints on `remember_fact` failure | not implemented | N/A (coercion sufficient) |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Tool arg contract + fail soft | ✓ |
| Module, helpers, remember_fact coercion, markup strip | ✓ |
| Wire all three loops + structured required-field errors | ✓ |
| v1 coercion scope (memory, fortune, clock, enter_dungeon) | ✓ |
| Unit + integration tests | ✓ (15 in `test_tool_args.py`) |
| Optional logging / B-tier hints | deferred / N/A |

## Tests run

```bash
cd app; python -m pytest tests/test_tool_args.py -q
```

**Result:** 15 passed (0.58s)

## Ticket close

- [x] Ticket acceptance criteria checked (required AC; optional logging deferred)
- [x] Status `done`, **Closed** 2026-05-21
- [ ] `python tmp/backlog/claim_ticket.py release APP-080 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Pre-drift lag was documentation only: implementation and qa-implementation-pass matched behavior; domain spec wire table and checklist were behind code.
- Non-v1 tools still pass raw `json.loads` dicts to bridge — consistent with spec “expand incrementally.”
- Validate unit tests cover 3 of 8 v1 tools; remaining validate branches exercised in loop short-circuit paths (non-blocking per qa-implementation-pass).
- Human PyGame Holt quest playtest deferred to Stage 7 (`human-test-plan.md`).
