# QA PASS: spec — round 1

**Task:** app-080-normalize-tool-args  
**backlog_ticket:** APP-080  
**ticket_path:** [tmp/backlog/app-080-normalize-tool-args-before-dispatch.md](../../app-080-normalize-tool-args-before-dispatch.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; existing owner updated)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | Ticket file Status `in_progress`; claimed in `status.md` |
| `registry_gap: false` | PASS | `research-brief.md` + `app-master-spec.md` registry row for LLM orchestrator |
| Domain spec matches run spec | PASS | Normative § Tool argument normalization (APP-080) present in `tmp/app-llm-orchestrator-spec.md` |
| AC testable | PASS | Coercion table, helpers, wire points, pytest matrix in run + domain spec |
| Code traces | PASS | Independent read: three `json.loads` sites (~1496, ~1834, ~1972); ad-hoc `enter_dungeon` rewrite ~2086–2090; bridge signatures verified |
| Expected files ⊆ plan scope | PASS | Run `spec.md` Affected paths match ticket Expected files (+ gamebridge cross-link is spec-sync on close) |
| AGENTS.md drift policy | PASS | Behavior in domain spec; run spec defers to domain § |

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-llm-orchestrator-spec.md`, cross-link in `tmp/app-gamebridge-spec.md`)
- [x] Acceptance criteria testable (R1–R5 + domain coercion table + pytest commands)
- [x] Code traces match repo (research-brief + live orchestrator/bridge/tools reads)
- [x] AGENTS.md / canon compliance (app-only normalizer; no engine/bridge markup strip)
- [x] Tests/commands listed (`test_tool_args.py`, full `app/tests/`, Holt fixture policy)
- [x] registry_gap false — orchestrator domain spec owns behavior
- [x] Coercion table covers v1 minimum tools including `remember_fact`, `memory_recall`, `fortune_spend`, `clock_tick`, `enter_dungeon`
- [x] `fortune_spend.amount` mismatch resolved (drop unknown keys; coerce `character_id` only — R3 + domain table)
- [x] All three loop wire points documented in domain spec wire table (matches ticket AC)

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec | Ready |
|-----------|---------|-------------|-------|
| Tool arg contract at orchestrator boundary | R1, Goals | § Tool argument normalization — Boundary | Yes |
| Fail soft on coercion failures | R5 | § Failure modes | Yes (see SPEC-001 note) |
| `normalize_tool_args` module | R1 | Module + Helpers table | Yes |
| `_coerce_int` markup + clamp | R1 | `_coerce_int` contract | Yes |
| `remember_fact` coercions | R2 | Coercion table rows | Yes |
| Markup strip on scalars | R1 | `_strip_tool_markup` | Yes |
| Wire all three loops | R4 | Wire table steps 1–2 | Yes |
| Structured error on unrecoverable required fields | R4–R5 | § Failure modes | Partial — see SPEC-001 |
| v1 coercion table minimum | R2–R3 | Coercion table (v1) | Yes |
| Unit + integration tests | Test plan | § Tests APP-080 | Yes |
| Domain spec § + changelog on close | Expected files | Changelog 2026-05-21 | Yes |
| GameBridge cross-link | Pointers | `app-gamebridge-spec.md` § Typed args | Yes |

## Verified code traces (independent)

| Claim | Verified |
|-------|----------|
| `_llm_loop` parses args then `_execute_tool` with no normalize | Yes (`orchestrator.py` ~1972–1976) |
| `_combat_llm_loop_inner` → `_execute_combat_action(**args)` | Yes (~1834–1840) |
| `_creation_llm_loop` → `_execute_creation_choice` | Yes (~1496–1507) |
| `remember_fact` → `bridge.remember_fact(**args)` | Yes (~2064–2065) |
| `semantic.remember` clamp assumes int | Yes (`semantic.py` ~22) |
| Ad-hoc `site_id` → `site_address` in `_execute_tool` | Yes (~2086–2090) |
| `fortune_spend` bridge: `character_id` only | Yes (`bridge.py` ~547) |
| `tools.py` schema: no `amount` on `fortune_spend` | Yes (~272–280) |
| `memory_recall` bridge uses `top_k` | Yes (`bridge.py` ~523) |
| No `tool_args.py` / `test_tool_args.py` yet | Yes (spec stage — expected) |

## Adversarial notes (non-blocking)

1. **SPEC-001 — required-field failure contract** — Domain § Failure modes and run R5 require `{ok: false, error: "<field> required"}` before bridge, but no named validator (`validate_tool_args`) or explicit `_execute_tool` early-check list. No pytest row for `{}` / missing `fact` after normalize. Dev plan should pin validation location and add one negative test; behavior is implied but not fully enumerated per required field.
2. **SPEC-002 — unknown-key allowlist** — R1 and domain helper row say drop unknown keys for fixed bridge signatures; only `fortune_spend.amount` is tabulated. Dev must whitelist per v1 tool (at minimum the six tabled tools) so `**args` never passes spurious LLM keys — recommend plan.md lists allowed keys per tool or references bridge signatures.
3. **SPEC-003 — run spec R4 optional wording** — Run `spec.md` R4 says creation loop wiring “optional for v1 if Dev time-boxed” while ticket AC and domain wire table require all three paths. Domain spec is authoritative; remove optional language from run spec in plan phase to avoid Dev skipping creation/combat symmetry.
4. **SPEC-004 — domain vs run test matrix drift** — Run spec includes `enter_dungeon` / `clock_tick` unit rows; domain § Tests APP-080 omits them (coercion table includes both). Recommend Dev add those two cases or explicitly defer in plan — not ticket AC minimum.
5. **SPEC-005 — `memory_recall` dual alias** — When both legacy `top` and `top_k` appear, precedence undefined. Low risk; plan can specify `top_k` wins.
6. **SPEC-006 — registry Owns column** — Domain spec **Owns** lists `tool_args.py`; `app-master-spec.md` registry row for LLM orchestrator does not — update on ticket close for file-map hygiene.
7. **SPEC-007 — backlog README status** — Index lists APP-080 as `open` while ticket body is `in_progress`; cosmetic sync when convenient.
8. **SPEC-008 — entities as JSON string** — Coercion table assumes list or coercible array; stringified JSON array for `entities` not covered. Out of v1 session evidence; note for follow-up if logs show it.

## Summary

Run `spec.md` and domain § Tool argument normalization (APP-080) fully cover the Holt `remember_fact.importance` regression, v1 coercion table, three-loop wiring, `fortune_spend` correction, bridge typed-args cross-link, and pytest contracts. `registry_gap` is correctly false. Spec is implementation-ready; Dev plan should resolve validation placement, unknown-key whitelisting, and align run-spec R4 with mandatory loop wiring.

## Re-review focus

_None required for round 2 unless PM revises failure-mode validator contract or removes R4 optional language._
