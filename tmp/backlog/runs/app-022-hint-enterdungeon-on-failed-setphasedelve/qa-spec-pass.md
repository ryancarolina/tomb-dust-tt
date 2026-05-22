# QA PASS: spec — round 1

**Task:** app-022-hint-enterdungeon-on-failed-setphasedelve  
**backlog_ticket:** APP-022  
**ticket_path:** [tmp/backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md](../../app-022-hint-enterdungeon-on-failed-setphasedelve.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; existing owner updated)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-exploration-delve-spec.md` § Failed set_phase(delve) hint (APP-022))
- [x] Acceptance criteria testable (R1–R5, T1–T6, pytest commands)
- [x] Code traces match repo (`orchestrator.py` `_llm_loop` L2431–2478: generic `TOOL FAILED`, `all_failed and content`, `_COMBAT_TOOL_NAMES` early return; `set_phase` has no `normalize_tool_args` normalizer in `tool_args.py`; research path A confirmed)
- [x] AGENTS.md / canon compliance (app-only hints; no phase FSM or bridge behavior change)
- [x] Tests/commands listed (new `test_exploration_set_phase_delve_hint.py`, engine regressions, APP-024 regression)
- [x] registry_gap false — exploration-delve domain spec owns behavior; orchestrator spec coordination only
- [x] Every ticket AC row mapped in `spec.md` § Acceptance criteria mapping and domain § Tests (APP-022)

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec | Testable |
|-----------|---------|-------------|----------|
| On failed `set_phase(delve)`, orchestrator hints `enter_dungeon` + `compass_exits` | R1–R3 hint text contract; trigger table | § Trigger, Hint text, Injection 1–3 | T1, T2, T6 (tool/system); T2 (player banner) |
| Spec sync on close | Expected files + changelog row | Checklist open work + changelog draft | Drift gate at Stage 6 |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; Expected files = orchestrator + new test module |
| registry_gap | **PASS** | false; domain § APP-022 added 2026-05-22 |
| AC testability | **PASS** | Substring asserts (`compass_exits`, `enter_dungeon`); negatives T3–T5 |
| Code traces | **PASS** | Injection points match `_llm_loop` failure branch; no `_delve_entry_tool_hint` yet (impl pending) |
| Expected files ⊆ spec scope | **PASS** | No hook allow-list gap |
| Non-goals / sibling layers | **PASS** | APP-024, APP-028, APP-077 boundaries and compose order documented |
| TurnTruth | **PASS** | Code-owned hint text (not LLM verify path); consistent with APP-024 refusal pattern |

## Adversarial notes (non-blocking)

1. **Combat-tool batch** — If `set_phase(delve)` fails alongside `_COMBAT_TOOL_NAMES`, R3 is suppressed by existing early return (`orchestrator.py` L2474–2475). Rare on surface; documented in run spec R3.
2. **Optional R4 suffix** — Live `compass_exits()` in hint builder is optional; core static hint satisfies ticket AC (PM reflection aligned).
3. **Exact hint prose** — Not pinned as exported constant; tests use substring asserts — appropriate.
4. **Orchestrator spec open-work list** — APP-022 still listed under open work in `tmp/app-llm-orchestrator-spec.md`; update on ticket close (PM noted).
5. **TurnTruth bypass** — Spec does not name the gate explicitly; hint is code-owned system/player inject, not verified LLM prose — acceptable; Dev plan may note sibling to APP-024 refusal.
6. **Depth guard for R3** — Run spec and domain spec require `depth == 0` for player-visible hint; current `_llm_loop` block has no depth check — Dev must add guard on implement.

## Summary

`spec.md` and domain § Failed set_phase(delve) hint (APP-022) fully cover the single ticket AC with testable dual injection (tool JSON, system `TOOL FAILED`, player `all_failed` banner), negative cases, APP-024 compose order, and scope limits. No registry gap. Spec is implementation-ready for Dev plan + QA plan gates.

## Re-review focus

_None required — proceed to Dev plan._
