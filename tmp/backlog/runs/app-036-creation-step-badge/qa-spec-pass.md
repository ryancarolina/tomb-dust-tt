# QA PASS: spec

**Task:** app-036-creation-step-badge
**backlog_ticket:** APP-036
**ticket_path:** [tmp/backlog/app-036-creation-step-badge-in-ui.md](../../app-036-creation-step-badge-in-ui.md)
**Round:** 1
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `tmp/app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § File map (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R6, ticket AC, pytest + regression commands)
- [x] Code traces match repo (`_enrich_status_for_ui` at `app/ui/app.py` 341–349; APP-037 `is_map_travel_blocked` pattern; `CREATION_STEPS` / `CREATION_STATUS_LABELS` in `creation.py`; StatsPanel phase badge at `stats.py` 95–101; `_process_turn` `finally` → `_queue_turn_status` at 320–322; `test_process_turn_exception_queues_enriched_status` in `test_ui_map_creation_gate.py`)
- [x] AGENTS.md / canon compliance (app UI only; step truth from `CreationState.step`; no narration scrape)
- [x] Tests/commands listed (`test_ui_creation_badge.py` matrix + creation-flow/restore/map-gate regressions)
- [x] registry_gap false — pygame-ui domain spec owns § Creation step badge
- [x] Every ticket AC row mapped in run spec + domain spec § Creation step badge (APP-036)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false; existing `app-pygame-ui-spec.md` |
| AC testability | **PASS** | Display map, enrich keys, panel show/hide, exception-path refresh |
| Code traces | **PASS** | Enrich template matches APP-037; FSM keys verified in `creation.py` |
| Expected files ⊆ spec scope | **PASS** | All six ticket paths covered; `sidebar.py` correctly optional |
| Label policy (APP-065) | **PASS** | `CREATION_STEP_DISPLAY` ≠ footer tokens; AC “or equivalent” satisfied |
| Domain spec sync (R6) | **PASS** | PM draft in domain spec matches run spec; impl close adds final changelog |
| APP-062 layout | **PASS** | Stats-region placement; draw-only; `_do_layout` unchanged |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Visible badge while `creation.active` with human step label | R1–R4; domain § Badge signal + display map | `test_get_creation_step_badge_active`, panel show test | **PASS** |
| Badge hidden after creation / roster live | R2 hide rule; R4 clear | `test_get_creation_step_badge_inactive`, `test_creation_flow` regression | **PASS** |
| Data from orchestrator — never narration scrape | R2–R3; APP-065/037 cross-refs | enrich + helper tests; forbidden paths documented | **PASS** |
| APP-062 layout compatibility | R5; domain § Layout | resize preserve test (APP-037 pattern) | **PASS** |

## Adversarial notes (non-blocking)

1. **Ticket AC wording** — Ticket cites `CREATION_STATUS_LABELS`; run spec correctly mandates separate `CREATION_STEP_DISPLAY` because label values are internal footer enums (`SKILLS_INPUT`, …). Outcome matches AC intent (“or equivalent”).
2. **Resume refresh hook** — R3 “next status push after load” is satisfied by orchestrator restore inside `process_turn` + `_queue_turn_status` in `finally` (not `_load_session` alone). Dev plan should mock this path explicitly in `test_process_turn_exception_queues_creation_badge` / restore regression.
3. **`WORLD_INTRO` / Reception** — Badge shows “Reception” only while `creation.active`; post-finalize hide is intentional per R2 desync guard (PM flagged; playtest in Stage 7).
4. **Headless draw** — Spec allows StatsPanel state assertions without pixel tests; consistent with APP-035/037 precedent.
5. **Third vocabulary** — `CREATION_STEP_DISPLAY` adds maintenance alongside `CREATION_STEPS`; R1 unit test requiring full step coverage mitigates drift.

## Summary

Run `spec.md` is implementation-ready: enrich pattern mirrors APP-037, step truth from `creation.step`, player-facing labels decoupled from footer tokens, StatsPanel placement documented, and domain spec § Creation step badge (APP-036) already aligned. No blockers for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
