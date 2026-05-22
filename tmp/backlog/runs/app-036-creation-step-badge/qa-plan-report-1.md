# QA Report: plan — round 1

**Task:** app-036-creation-step-badge  
**backlog_ticket:** APP-036  
**ticket_path:** [tmp/backlog/app-036-creation-step-badge-in-ui.md](../../app-036-creation-step-badge-in-ui.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### TICKET-001 — blocker

- **Location:** `plan.md` § Task 4, § Files table, Flow D steps 6–7; vs ticket **Expected files** in [app-036-creation-step-badge-in-ui.md](../../app-036-creation-step-badge-in-ui.md)
- **Issue:** Plan requires edits to `app/ui/panels/sidebar.py` (cache `creation_step_display` on `update_from_status`; re-apply after `StatsPanel` recreation in `_do_layout`) but the ticket Expected files list **does not include** `sidebar.py`. Plan § Open questions #2 acknowledges the gap (“Ticket Expected files omit `sidebar.py`”) yet still lists the file in § Files while claiming “must ⊆ ticket Expected files.”
- **Implementation gap:** Spec R4 AC and domain spec § Layout require “Sidebar resize (`_do_layout`) does not drop badge state” (`test_sidebar_resize_preserves_creation_badge`, mirroring APP-037). Live `sidebar.py` recreates `StatsPanel` on every `_do_layout` (L20–26) — badge draw state cannot survive resize without sidebar-level cache (same pattern as `_map_travel_blocked` / APP-037). Backlog hooks deny `app/` writes outside ticket Expected files; impl cannot land the resize test without a ticket update.
- **Suggested fix:** Add `app/ui/panels/sidebar.py` to ticket Expected files (mirror [APP-037](../../app-037-block-map-travel-during-creation.md)). Update run `spec.md` § File map row for `sidebar.py` from “Unchanged wiring unless…” to “Cache + re-apply badge on resize (APP-037 mirror).” Re-run plan QA round 2.

### PLAN-002 — minor

- **Location:** `plan.md` §5 Tests, “Regression fix (small, recommended)”; vs ticket Expected files
- **Issue:** Plan recommends updating `test_enrich_status_for_ui_payload` in `app/tests/test_ui_map_creation_gate.py` to set `mock_orch.get_creation_step_badge.return_value = None`. That module is not in ticket Expected files. After `_enrich_status_for_ui` calls `get_creation_step_badge()`, an unconfigured `MagicMock()` is truthy and will pollute the enriched payload (verified: `test_ui_map_creation_gate.py` L83–95).
- **Implementation gap:** Map-gate regression suite fails post-APP-036 unless mock is fixed or ticket scope expanded.
- **Suggested fix:** Add `app/tests/test_ui_map_creation_gate.py` to ticket Expected files **or** document that the one-line mock fix is mandatory in the same PR and list the path on the ticket before impl. Non-blocking for plan quality if resolved with TICKET-001 ticket update (batch both paths).

## Verified (no findings)

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-pygame-ui-spec.md`
- [x] Plan aligns with run `spec.md` R1–R6 and `qa-spec-pass.md` (display map, orchestrator helper, enrich keys, StatsPanel placement, APP-062 layout, domain sync on close)
- [x] Acceptance criteria testable — ticket AC + spec requirements mapped in plan flows A–E, § Task breakdown, § Tests table
- [x] Code traces match repo (`_enrich_status_for_ui` at `app/ui/app.py` L341–349; `is_map_travel_blocked` ~L348 orchestrator pattern; `Sidebar._do_layout` recreates panels L20–31; `CREATION_STEPS` / `CREATION_STATUS_LABELS` in `creation.py`; phase badge at `stats.py` L95–101; `_queue_turn_status` in turn `finally`)
- [x] AGENTS.md / canon compliance (app UI only; step truth from `CreationState.step`; no narration scrape; APP-065 label policy)
- [x] Tests/commands listed (`test_ui_creation_badge.py` matrix + creation-flow/restore/map-gate/suggestions regressions)
- [x] APP-037 enrich template correctly extended (init + `finally` status push; exception-path test planned)
- [x] Label policy — `CREATION_STEP_DISPLAY` separate from footer tokens; R1 invariant test planned
- [x] Domain spec § Creation step badge (APP-036) matches plan; changelog deferred to ticket close (correct)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-036 `in_progress` |
| Plan files ⊆ Expected files | **FAIL** | `sidebar.py` in plan, absent from ticket; hook blocker |
| Spec R1–R6 in plan | **PASS** | All requirements traced in flows + tasks |
| Code traces | **PASS** | Line refs spot-checked against live `app.py`, `sidebar.py`, `stats.py`, `orchestrator.py` |
| Test plan vs `qa-spec-pass` | **PASS** | Matrix covers spec suggested cases + resize + exception path |
| R4 resize AC feasible | **PASS** | Plan correctly identifies APP-037 cache pattern — blocked only by ticket scope |
| APP-062 / APP-065 / APP-066 cross-refs | **PASS** | Stats-region placement; no footer tokens; `creation.active` guard |

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism | QA |
|-------------|------------|------------------|-----|
| Visible badge with human step label | Flows A–D; §1–4 | `test_get_creation_step_badge_active`, `test_stats_panel_shows_badge_from_status` | **PASS** |
| Badge hidden post-finalize | Flow B truth table; Flow E | `test_get_creation_step_badge_inactive`, `test_creation_flow` regression | **PASS** |
| Orchestrator source — no narration scrape | Flows B–C | enrich + helper tests; forbidden paths documented | **PASS** |
| APP-062 layout compatibility | Flow D; R5 | stats draw-only; resize test | **PASS** (impl blocked on ticket scope) |
| R4 resize survival | Flow D steps 6–7; §4 | `test_sidebar_resize_preserves_creation_badge` | **BLOCKED** — needs `sidebar.py` on ticket |

## Summary

Plan is technically sound and spec-complete: enrich pattern mirrors APP-037, resize hazard correctly diagnosed, test matrix covers helper/enrich/panel/exception/resize paths. **FAIL** because `app/ui/panels/sidebar.py` is a planned implementation target but missing from ticket Expected files — backlog hooks will block the changes required for R4 resize AC. Update ticket (and run spec file map) before implementation; optionally add `test_ui_map_creation_gate.py` for the one-line mock regression fix.

## Re-review focus

- Confirm ticket Expected files include `app/ui/panels/sidebar.py` (and optionally `app/tests/test_ui_map_creation_gate.py`).
- Confirm run `spec.md` § File map matches plan § Files (sidebar no longer “optional/unchanged”).
- Re-verify plan § Files table ⊆ updated ticket Expected files.
