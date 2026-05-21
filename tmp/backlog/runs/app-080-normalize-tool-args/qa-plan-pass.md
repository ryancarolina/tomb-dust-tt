# QA PASS: plan — round 1

**Task:** app-080-normalize-tool-args  
**backlog_ticket:** APP-080  
**ticket_path:** [tmp/backlog/app-080-normalize-tool-args-before-dispatch.md](../../app-080-normalize-tool-args-before-dispatch.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | Ticket Status `in_progress`; run `status.md` Stage 0 claimed |
| Plan inputs present | PASS | `plan.md`, `reflection-dev-plan.md`, `spec.md`, `qa-spec-pass.md` |
| Plan files ⊆ ticket scope | PASS | Impl: `tool_args.py`, `orchestrator.py`, `test_tool_args.py`; spec sync on close: `tmp/app-llm-orchestrator-spec.md` (Expected files); `tmp/app-gamebridge-spec.md` + `tmp/app-master-spec.md` authorized by ticket **Spec sync** / SPEC-006 on close only — not impl creep |
| Addresses spec R1–R5 | PASS | Module, helpers, coercion table, `validate_tool_args`, three-loop wire, failure modes, Holt regression |
| QA spec notes resolved | PASS | Plan § “QA spec notes addressed” — SPEC-001–005, 008; SPEC-006/007 deferred to close |
| Code traces (independent) | PASS | Line ranges verified live |
| Test plan adequate | PASS | Unit matrix + Holt fixtures + integration `_execute_tool`; pytest commands match spec |

**Blocker count:** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-llm-orchestrator-spec.md`; gamebridge cross-link on close)
- [x] Acceptance criteria testable via plan test matrix and implementation order
- [x] Code traces match repo (plan only)
- [x] AGENTS.md / canon compliance (app-only boundary; no engine/bridge markup strip)
- [x] Tests/commands listed (`test_tool_args.py`, full `app/tests/`, Holt fixture policy)
- [x] Plan implementation paths ⊆ ticket Expected files (+ documented spec-sync-on-close)
- [x] registry_gap false — behavior owned by orchestrator domain spec

## Independent code traces

| Claim | Verified |
|-------|----------|
| `_creation_llm_loop` `json.loads` ~1496, no normalize | Yes |
| `_combat_llm_loop_inner` `json.loads` ~1834, `**args` to `_execute_combat_action` | Yes |
| `_llm_loop` `json.loads` ~1972 → `_execute_tool` ~1976, no normalize | Yes |
| `enter_dungeon` ad-hoc `site_id` rewrite ~2086–2090 | Yes |
| `remember_fact` → `bridge.remember_fact(**args)` ~2064–2065 | Yes |
| `semantic.remember` `max(1, min(5, importance))` ~22 | Yes (`play/tomb_gm/services/memory/semantic.py`) |
| `fortune_spend(character_id)` only; no `amount` in `tools.py` ~272–280 | Yes |
| `memory_recall(query, top_k=5)` ~523 | Yes |
| `tool_args.py` / `test_tool_args.py` absent (pre-impl) | Yes |
| `COMBAT_ACTION_TOOL` / `SET_CREATION_CHOICE_TOOL` required fields match plan whitelist | Yes (`tools.py`) |

## Spec / plan alignment

| Requirement | Plan coverage |
|-------------|---------------|
| R1 `normalize_tool_args` + helpers | `tool_args.py` symbols table |
| R2 v1 coercion table | Per-tool normalize rules + `_ALLOWED_KEYS` |
| R3 `fortune_spend` drop `amount` | Whitelist + unit test |
| R4 three loops + remove `enter_dungeon` rewrite | Sites 1–3 + delete ~2086–2090 |
| R5 fail soft, no TypeError on v1 fields | `validate_tool_args` before dispatch; normalize never raises |
| Domain wire table | All three loops mandatory (overrides run spec R4 optional wording) |
| Holt regression | Paths A/B + fixtures + integration test |
| APP-048 `top` → `top_k` | Alias + `top_k` wins + tests |

## Adversarial notes (non-blocking)

1. **Validate test coverage partial** — Plan documents validate rules for eight tools but unit tests only assert three (`remember_fact`, `memory_recall`, `fortune_spend`). Acceptable for v1 Holt focus; impl may add `enter_dungeon` / `clock_tick` validate rows if cheap.
2. **Domain wire table** — Step 2 is normalize-only today; plan adds validate before dispatch. Spec sync on close must add `validate_tool_args` to Helpers + wire step (plan § Spec sync on close).
3. **`log_tool_call` post-normalize only** — Raw args remain in LLM transcript; plan documents tradeoff; no pre-normalize snapshot unless APP-034 needs it.
4. **SPEC-008 entities JSON string** — Explicitly out of v1; follow-up if logs show it.
5. **Creation/combat loop tests** — No dedicated orchestrator-loop integration tests; `_execute_tool` integration + unit matrix deemed sufficient per plan.

## Summary

`plan.md` is implementation-ready: scope matches ticket Expected files, independently verified dispatch sites, resolves all qa-spec round-1 notes (validation placement, whitelist, mandatory three loops, `top_k` precedence, extended normalize tests). Test plan covers Holt regression, coercion matrix, and structured required-field errors. Proceed to implementation.

## Re-review focus

_None unless Dev revises scope (e.g. drops creation/combat wiring or `validate_tool_args`)._
