# QA PASS: plan — round 1

**Task:** app-037-block-map-travel-during-creation  
**backlog_ticket:** APP-037  
**ticket_path:** [tmp/backlog/app-037-block-map-travel-during-creation.md](../../app-037-block-map-travel-during-creation.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; PM r2 domain § Map travel during creation)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (strict six-path set; no scope creep)
- [x] Acceptance criteria testable — ticket AC + spec R1–R7 mapped in plan flows, task breakdown, and §5 test table
- [x] Code traces match repo (`app/ui/app.py` L68–71 map click; L125–126 init status; L299–300 success-only status; L315–318 `except` + `return`; L319–320 `_queue_turn_suggestions` in `finally`; `map_view.py` L94–95 stub click; `sidebar.py` L18–28 `_do_layout` recreates `MapView`)
- [x] AGENTS.md / canon compliance (UI defense-in-depth; APP-008 engine gate unchanged; no `build/` drift)
- [x] Tests/commands listed (`test_ui_map_creation_gate.py`, `test_ui_suggestions.py`, `test_creation_flow.py` regressions)
- [x] Spec R1–R7 coverage in plan (orchestrator signal, status enrichment, click guard, MapView overlay/hint, sidebar resize survival, post-finalize re-enable, domain changelog on close)
- [x] Round 1 spec findings (TICKET-001, SPEC-001, SPEC-002) reflected in plan scope and `_queue_turn_status` / `finally` design
- [x] APP-065 parity explicitly addressed (exception-path test, `except return` preserved, resize cache hazard)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — `is_map_travel_blocked()` | Yes |
| `app/ui/app.py` — enrich status, `_queue_turn_status`, click guard, cache | Yes |
| `app/ui/panels/map_view.py` — `set_travel_blocked`, overlay, hover hint, gated click | Yes |
| `app/ui/panels/sidebar.py` — forward flag, resize re-apply, click short-circuit | Yes |
| `app/tests/test_ui_map_creation_gate.py` (new) | Yes |
| `tmp/app-pygame-ui-spec.md` — changelog on close only | Yes |

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 dual-condition block signal on orchestrator | Flow A; §1 | `test_is_map_travel_blocked_*` (4 truth-table rows) |
| R2 init + post-turn status refresh (incl. exception) | Flow B; §2; pseudocode L98–117 | `_enrich_status_for_ui`, `_queue_turn_status`; `test_enrich_status_for_ui_payload`; `test_process_turn_exception_queues_enriched_status` |
| R3 app click guard when blocked | Flow C; §2 step 7 | `_map_travel_blocked()` cache + L68–71 guard (impl + integration via exception test) |
| R4 MapView display on, travel off, hint copy | Flow D; §3 | `test_map_view_click_blocked_returns_none`; `test_map_view_default_hint_string` |
| R5 sidebar forward + resize survival | Flow E; §4 | `test_sidebar_update_from_status_forwards_block`; `test_sidebar_resize_preserves_blocked`; Flow E step 2 documents `update_position` while blocked |
| R6 re-enable after finalize | Flow F; §1 post-finalize test | `test_is_map_travel_blocked_post_finalize` + `test_creation_flow` regression |
| R7 domain spec sync | §6; rollback | Changelog on `release APP-037 --done` |
| Ticket: travel disabled during creation / desync | R1 truth table | orchestrator unit tests |
| Ticket: hint *"Finish Registry intake first"* | Flow D; §3 | exact-string MapView default test |
| Ticket: re-enable after finalize | Flow F | post-finalize test |
| Ticket: map displays hub; travel blocked only | Flow D step 6–7; Flow E step 2 | draw AC documented; manual hover step |
| Ticket: APP-062 resize compatible | Flow E; resize hazard note | `test_sidebar_resize_preserves_blocked` |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-037 `in_progress` |
| Plan ⊆ Expected files | **PASS** | Six paths only |
| Spec R1–R7 in plan | **PASS** | All requirements traced |
| Code traces | **PASS** | Line refs spot-checked against live `app.py`, `sidebar.py`, `map_view.py`, `orchestrator.py` |
| Test plan vs `qa-spec-pass` | **PASS** | Exception-path automation committed (avoids APP-065 PLAN-001 regression) |
| Except-path behavior preservation | **PASS** | Pseudocode L113–116 retains `return` in `except` (avoids APP-065 PLAN-002 regression) |
| APP-008 / APP-065 / APP-062 / APP-063 cross-refs | **PASS** | Three-layer defense; chip desync parity; resize cache |

## Notes (non-blocking — implementation QA)

1. **Finally-only status push** — Plan consolidates success + exception refresh into `_queue_turn_status` in `finally` (open Q1). Outcome matches R2 AC and APP-065 chip pattern; domain spec prose still mentions “success path” separately — behavior equivalent.
2. **`_load_session` overlay lag** — Open Q2: resume mid-creation may lack overlay until first turn `finally`; not in R2 AC; acceptable defer.
3. **Draw/grid regression** — No automated assert that overlay does not suppress title/cells/scene dots; manual hover step + impl review sufficient for v1.
4. **`update_position` while blocked** — Flow E step 2 documents behavior; impl should assert in `test_sidebar_update_from_status_forwards_block` if trivial to add party + blocked keys together.
5. **Hover hint rendering** — Headless tests cover state/hint string; full blit placement validated manually until APP-063 hit-test lands.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
