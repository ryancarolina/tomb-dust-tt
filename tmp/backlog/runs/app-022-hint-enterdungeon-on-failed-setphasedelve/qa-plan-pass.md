# QA PASS: plan

**Task:** app-022-hint-enterdungeon-on-failed-setphasedelve  
**backlog_ticket:** APP-022  
**ticket_path:** [tmp/backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md](../../app-022-hint-enterdungeon-on-failed-setphasedelve.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (qa-spec-pass round 1: `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial, code-level)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches plan (`tmp/app-exploration-delve-spec.md` § Failed set_phase(delve) hint (APP-022))
- [x] Acceptance criteria testable (R1–R5, T1–T6, pytest + engine regressions)
- [x] Code traces match repo (independent read — audit table below)
- [x] AGENTS.md / canon compliance (orchestrator hints only; no FSM/bridge/prompt changes)
- [x] Tests/commands listed
- [x] Plan impl files ⊆ ticket Expected files
- [x] qa-spec-pass adversarial notes carried forward (depth guard, combat suppress, TurnTruth bypass)

## Code trace audit (adversarial)

| Claim | Repo check | Result |
|-------|------------|--------|
| Depth-0 reset block | `orchestrator.py:2364–2372` — `_last_tool_results`, `_entry_committed_this_turn`, `_exploration_pre_turn_mode` | **Match** — plan adds `_delve_entry_hint_this_turn` reset here |
| Tool loop: execute → log → store → fail inject | `orchestrator.py:2427–2454` | **Match** — plan inserts R1/R2 enrichment before `log_tool_call` (L2432) |
| Generic `TOOL FAILED` else branch | `orchestrator.py:2442–2448` | **Match** — R2 extends this block |
| `all_failed and content` + compose | `orchestrator.py:2462–2478` | **Match** — R3 inserts hint between `prefix` and `_compose_exploration_narration(content)` |
| Combat-tool R3 suppress | `orchestrator.py:2474–2475` (`failed_names & _COMBAT_TOOL_NAMES`) | **Match** — Flow E; R1/R2 may still run |
| `set_phase` has no `normalize_tool_args` special case | `app/gm/tool_args.py` — no `set_phase` entry | **Match** — trigger uses post-normalize `args.get("phase")` |
| Module constant anchor | `_SITE_ENTRY_REFUSAL_LINE` at `orchestrator.py:109–112` | **Match** — plan places helpers after this block |
| Turn-scoped state precedent | `_entry_committed_this_turn` init/reset at `orchestrator.py:367`, `2367` | **Match** — sticky flag pattern valid |
| `bridge.compass_exits()` shape for R4 | `bridge.py:616–626` → `exits.below[].address` via `exploration.py:365–367` | **Match** — optional suffix parsing correct |
| Post-loop double compose (APP-024 sibling) | `process_turn:1103–1105` composes full `_llm_loop` return | **Known** — same as existing `all_failed` path; hint/core prefix not in `_SITE_ENTRY_MARKER_RES` |
| Test helpers exist | `test_exploration_site_entry_gate.py` — `_tool_call`, `_patch_llm_sequence`, `_surface_exploration_orchestrator` | **Match** |
| No pre-existing APP-022 symbols | `rg "_delve_entry"` under `app/` → none | **Match** — greenfield impl |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| On failed `set_phase(delve)`, orchestrator hints `enter_dungeon` + `compass_exits` | § Approach R1–R3; Tasks 1–4; trigger predicate | T1 (tool JSON), T2 (player banner), T6 (system inject) |
| Spec sync on close | §6 domain spec + orchestrator spec checklist | Changelog on `release --done` (not impl Expected files) |

## Spec R1–R5 → plan map

| ID | Plan section | Verified |
|----|--------------|----------|
| R1 | §3 tool result `"hint"` before log/store | Yes |
| R2 | §3 system `Hint:` append | Yes |
| R3 | §4 `all_failed and content`, `depth == 0`, sticky flag | Yes — resolves qa-spec NOTE-6 |
| R4 | §1.3 `_build_delve_entry_hint` + try/except | Yes — optional; core hint satisfies AC |
| R5 | §1.2 predicate + T3/T4 | Yes |

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` (helpers, flag, R1–R3) | Yes |
| `app/tests/test_exploration_set_phase_delve_hint.py` (new T1–T6) | Yes |
| `tmp/app-exploration-delve-spec.md` | Spec sync on close (ticket § Spec sync) |
| `tmp/app-llm-orchestrator-spec.md` | Coordination on close — not impl Expected files |

No edits to `bridge.py`, `tools.py`, `system_prompt.py` (explicit out of scope).

## qa-spec-pass notes — plan resolution

| Note | Plan handling |
|------|---------------|
| Combat-tool batch suppresses R3 | Flow E — early return unchanged |
| Optional R4 suffix | §1.3 + optional non-blocking test |
| Exact hint prose not pinned | Substring tests T1/T2/T6 — aligned |
| Orchestrator spec open-work | §6 close-time checklist update |
| TurnTruth bypass | Approach + Flow A step — code-owned inject, not verify path |
| Depth guard for R3 | §4 `depth == 0 and hint` — explicit |

## Scope boundary (re-check)

| Topic | Plan handling |
|-------|---------------|
| APP-024 fiction gate | Unchanged compose on `content` only inside `_llm_loop`; hint outside sanitizer arg |
| APP-028 combat strip | Non-goal; combat batch early return preserved |
| APP-077 footer | Compose order documented; footer not implemented yet |
| Phase FSM / engine | Regression pytest only; no behavior change |
| Partial success (fail + ok `enter_dungeon`) | Flow D + T5 — no R3 player banner |

## Notes (non-blocking — implementation QA)

1. **Double compose:** R3 return (`prefix + hint + safe`) still passes through `process_turn` `_compose_exploration_narration` (L1105). Inherited APP-024 pattern; hint text avoids `_SITE_ENTRY_MARKER_RES` — impl should assert T2 via `process_turn` or document if testing `_llm_loop` only.
2. **T6 / T2 entry point:** Dev reflection prefers direct `_llm_loop` for T6; T2 player banner should use same path players see (`process_turn` or full loop return) — pick one consistently in impl.
3. **No explicit tests** for depth ≥ 1 R3 skip (Flow F) or combat-only R3 suppress (Flow E) — acceptable; predicate covered by unit tests on trigger + T2 depth-0 happy path.
4. **Session claim:** Plan open question — implementer must `focus APP-022` / active batch before `app/` edits (hooks).
5. **Hint prose vs domain markdown:** Plan uses plain tool names in injects; align domain § Hint text or changelog on close if strings differ from bold doc form.

## Summary

`plan.md` traces six flows (primary fail, success contrast, wrong phase, partial success, combat suppress, recurse depth), maps R1–R5 to concrete `_llm_loop` insertion points verified against live line numbers, defines sticky turn flag mirroring APP-024, lists T1–T6 with regression commands, and stays within ticket Expected files for code. Resolves all qa-spec-pass adversarial notes. Ready for Stage 4 (workstreams + implementation).

## Re-review focus

_None required unless Dev revises trigger predicate, R3 depth/combat guards, or hint copy._
