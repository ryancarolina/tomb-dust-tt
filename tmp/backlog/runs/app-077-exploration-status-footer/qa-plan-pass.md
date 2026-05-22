# QA PASS: plan — round 1

**Task:** app-077-exploration-status-footer  
**backlog_ticket:** APP-077  
**ticket_path:** [tmp/backlog/app-077-code-owned-exploration-status-footer.md](../../app-077-code-owned-exploration-status-footer.md)  
**Round:** 1  
**domain_spec_creation:** not_needed  
**Reviewer role:** QA (adversarial)

**Verdict:** PASS

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Backlog ticket valid (`in_progress`) | PASS | `tmp/backlog/app-077-code-owned-exploration-status-footer.md` |
| Plan files ⊆ ticket Expected files | PASS | Plan § Files L347–357 lists only ticket Expected paths (7 files) |
| Acceptance criteria testable | PASS | Plan §8 maps F1–F11 → pytest cases; regression commands L317–324 |
| Code traces match repo | PASS | Independent read — see traces below |
| AGENTS.md / drift policy | PASS | Spec/domain updates deferred to close; no orphan behavior |
| Tests/commands listed | PASS | `test_exploration_status_footer.py` matrix + four regression suites |
| Spec alignment (post qa-spec-pass) | PASS | Plan F1–F12 map 1:1 to run `spec.md` and domain § APP-077 |
| TurnTruth / APP-083 ordering | PASS | Plan L15, F12 — compose independent; verify-before-compose when Phase 2 lands |

## Independent code traces (plan vs repo)

| Plan claim | Verified location | Match |
|------------|-------------------|-------|
| `_compose_exploration_narration` APP-024 stub only | `orchestrator.py` L657–662 — sanitizer + refusal, no strip/footer | ✅ |
| Exploration `process_turn` compose post-`_llm_loop` | L1170–1173 | ✅ |
| `_llm_loop` `all_failed and content` inner compose | L2615–2634; returns `prefix + hint? + safe` | ✅ |
| Double-compose path (inner + outer) | Inner L2630 + outer L1172 | ✅ — F8 idempotency required |
| Combat emit without compose | `_combat_turn` L2302, L2334 `_emit_narration` direct | ✅ — F9 wires compose |
| Combat prefix-only skip | `_combat_llm_loop_inner` L2427 `return prefix`; `_combat_turn` L2273 combat-start fail | ✅ — F9 `_is_code_only_combat_narration` |
| Death boilerplate skip | L2323, L2435 `_emit_narration(death_result.message)` | ✅ — F9 skip |
| L2287 early return no emit | L2282–2287 `_narrate_text` return only | ✅ — out of scope (NOTE-003) |
| `strip_llm_status_tags` narrow regex | `creation.py` L115–118, L573–576 | ✅ — F4 broadens |
| `format_creation_status` reference | `creation.py` L671–674 | ✅ |
| Prompt bracket mandate | `system_prompt.py` L213, L271–273 | ✅ — F10 |
| `_auto_finalize` footer shape ref | `orchestrator.py` L1992 | ✅ |
| `bridge.status()` combat payload | `cmd_core.py` L211–218 — `turn_id`, no `actor` | ✅ — plan F3 uses `turn_id` only |
| Roster HP/Fortune pre-formatted | `cmd_core.py` L165–166 `"current/max"` strings | ✅ — plan uses entry fields directly |
| Test helpers exist | `test_exploration_site_entry_gate.py` L29, L49 | ✅ |

## Requirements → plan coverage

| Spec / ticket | Plan section | Test gate |
|---------------|--------------|-----------|
| F1 `format_exploration_status` | §1 L76–118 | `test_format_exploration_status_golden` |
| F2 field mapping + transit GP | §1 L92–118 | `test_format_exploration_status_gp_transit` |
| F3 combat `Turn:` | §1 L101–108 | golden combat variant |
| F4 broad bracket strip | §2 L122–144 | strip unit + creation regression |
| F5 meta strip | §3 L148–167 | `test_strip_llm_meta_narration` |
| F6–F8 compose order + idempotency | §4 L171–192 | compose unit tests incl. **F8 mandatory** |
| F9 combat wire | §5 L198–224 | `test_combat_turn_compose_wrong_gp` |
| F10 prompt | §7 L246–262 | grep / human playtest |
| F11 optional drift | §6 L228–242 | optional |
| Ticket AC wrong-GP integration | §8.3–8.4 | compose + combat tests |

## Adversarial notes (non-blocking)

1. **PLAN-001 — Line-number drift** — Plan cites L1135–1172; live `process_turn` compose is L1170–1173. Impl should re-anchor symbols, not line numbers.
2. **PLAN-002 — Domain wiring table wording** — Domain spec § Wiring L402 says inner `_llm_loop` compose should be “complete (no second compose)”; reality is mandatory double-compose (inner L2630 + outer L1172). Plan F8 correctly treats idempotency as **required**; domain table is aspirational wording, not a plan defect.
3. **PLAN-003 — F4 broad regex risk** — Third alternation may strip any `[…]` containing status tokens. Plan gates via golden footer tests + creation `-k status` regression; impl must run both before close.
4. **PLAN-004 — Prefix-only footer asymmetry** — Exploration `process_turn` always composes (footer on `[Mechanics failed — …]` only); combat prefix-only skips via `_is_code_only_combat_narration`. Consistent with domain § “code-only failure” row; human playtest should confirm combat HUD suffices when footer omitted.
5. **PLAN-005 — F11 GP parse** — `parse_narration_status_line` lacks GP today; F11 drift helper needs new GP capture regex as plan states — optional AC.
6. **PLAN-006 — `_emit_exploration_narration` vs inline** — Plan leaves wrapper choice to impl (L209–218); either OK if F9 tests pass.

## Summary

`plan.md` is implementation-ready: deep code-path traces verified against live `orchestrator.py`, `creation.py`, `system_prompt.py`, and `cmd_core.py`; all ticket Expected files covered; F8 idempotency explicitly gated; qa-spec-pass adversarial notes (F3 `turn_id` only, empty roster, NOTE-003 L2287, creation regression) addressed. No blockers for Stage 4 workstreams dispatch.

## Re-review focus

_None required unless Dev revises F4 regex shape, F8 idempotency strategy, F9 combat skip heuristics, or adds files outside ticket Expected list._
