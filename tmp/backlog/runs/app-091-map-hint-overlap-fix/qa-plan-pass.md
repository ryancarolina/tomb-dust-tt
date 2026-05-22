# QA PASS: plan — round 1

**Task:** app-091-map-hint-overlap-fix  
**backlog_ticket:** APP-091  
**ticket_path:** [tmp/backlog/app-091-map-travel-block-hint-overlap-fix.md](../../app-091-map-travel-block-hint-overlap-fix.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; domain § Hint placement APP-091 drafted)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (strict three-path set; no scope creep)
- [x] Acceptance criteria testable — ticket AC + spec R1–R5 mapped in plan flows, exact changes, and § Tests
- [x] Code traces match repo (collision at `map_view.py` L210–213, L224–226, L278–291; hover L99–100; dungeon L269–276)
- [x] AGENTS.md / canon compliance (layout-only `MapView` fix; no orchestrator/mechanics drift)
- [x] Tests/commands listed (`test_ui_map_creation_gate.py`, `test_creation_flow.py` regression)
- [x] Spec R1–R5 coverage in plan (surface overlay hint, dungeon non-regression, APP-037 lock, placement test, spec changelog on close)
- [x] `qa-spec-pass.md` adversarial notes addressed (surface vs dungeon API branch, wrap/readability, fail-pre test contract)
- [x] TurnTruth / narration gate correctly marked N/A (no `app/gm/` edits)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/ui/panels/map_view.py` — wrap/center hint, refactor overlay helper, test helpers | Yes |
| `app/tests/test_ui_map_creation_gate.py` — `test_map_view_hint_blit_inside_overlay_not_footer_row` | Yes |
| `tmp/app-pygame-ui-spec.md` — changelog finalize on close only | Yes |

**Not edited (explicit):** `app/ui/app.py`, `sidebar.py`, `orchestrator.py`, `theme.py`, `rich_text.py` — matches ticket non-goals.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 surface hint inside grid overlay; footer reserved | Flow A; §1a–1d; layout math table | `test_map_view_hint_blit_inside_overlay_not_footer_row`: `grid_rect.contains(hint_rect)`, `hint_rect.bottom < info_y`; manual `32-C` repro |
| R1 word-wrap on narrow sidebar (APP-062) | §1b `_wrap_hint_lines`; narrow 240px math | same test: `len(wrapped) >= 2`; manual at ~30% sidebar width |
| R2 dungeon path no regression | Flow D; `hint_outside=(x, y + 4)` | existing suite green; no dungeon draw test (surface-only repro per ticket) |
| R3 APP-037 gate unchanged | Flow B/C marked unchanged; out-of-scope table | all 10 existing `test_ui_map_creation_gate.py` tests preserved |
| R4 placement unit test fail-pre / pass-post | §2; fail-pre table | pre-fix: missing `_travel_block_hint_rect` → fail; post-fix: rect assertions |
| R5 domain spec sync on close | §3 | changelog L361 on `release APP-091 --done` |
| Ticket: hint does not overlap `displayName` or scene line | R1 post-fix invariant | hint inside `grid_rect` strictly above `info_y` protects both footer rows |
| Ticket: default hint string unchanged | R3 | existing `test_map_view_default_hint_string` |
| Ticket: domain spec § + changelog | R5 | PM draft § Hint placement (APP-091) already in domain spec |

## Independent code traces (spot-checked)

| Path | Live repo finding | Plan alignment |
|------|-------------------|----------------|
| `map_view.py:_draw_surface` L209–226 | Footer blit at `info_y = grid_y + grid_h + 16`; overlay called with same Y | Root cause confirmed; plan removes footer-row hint coords |
| `map_view.py:_draw_travel_block_overlay` L278–291 | Single-line hint at external `(hint_x, hint_y)` | Plan refactors to in-rect wrap/center + optional `hint_outside` |
| `map_view.py:_draw_dungeon` L269–276 | `content_rect` overlay; hint at `(x, y + 4)` after address line | Flow D preserves via `hint_outside` kwarg |
| `map_view.py:handle_hover` L99–100 | `_hovering = self.rect.collidepoint(pos)` — full panel | Unchanged; plan Flow B correct on behavior |
| `app.py` L68–69 | `MOUSEMOTION` → `sidebar.handle_hover` | Plan Flow B cites ~L339 (stale line ref — see note 1) |
| `app.py:_enrich_status_for_ui` L346–349 | `map_travel_blocked` + hint enrichment | Plan Flow C correct; no edits planned |
| `sidebar.py:update_from_status` L46–52 | forwards block to `MapView` | Unchanged per R3 |
| `sidebar.py:_do_layout` L33 | re-applies cached block on resize | Unchanged per R3 |
| `test_ui_map_creation_gate.py` | 10 tests; no blit-position coverage | R4 gap addressed by planned new test |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-091 `in_progress`; P1 bug; three Expected files |
| Plan ⊆ Expected files | **PASS** | Strict three-path set |
| Spec R1–R5 in plan | **PASS** | All requirements traced with tests or manual repro |
| Code traces | **PASS** | Collision coordinates verified; one stale MOUSEMOTION line ref (non-blocking) |
| Test plan vs `qa-spec-pass` | **PASS** | Placement test + wrap assert + fail-pre contract; exception/gate paths untouched |
| APP-037 / APP-062 / APP-063 cross-refs | **PASS** | Gate behavior locked; narrow wrap; no APP-063 scope |
| Draw-order / footer legibility | **PASS** | Footer drawn before overlay; hint moves inside `grid_rect` only |

## Notes (non-blocking — implementation QA)

1. **Stale line ref in Flow B** — Plan cites `app.py` event loop ~L339 for `MOUSEMOTION`; live handler is L68–69. Behavior trace is correct; update line ref during impl if touching docs.
2. **`_surface_grid_metrics` drift** — Plan duplicates `_draw_surface` grid math unless impl extracts `_compute_surface_grid` (recommended in Risks). Impl QA should assert metrics match production draw or use shared helper.
3. **Shared layout path** — Plan commits to `_layout_hint_placements` (or equivalent) shared by `_draw_travel_block_overlay` and `_travel_block_hint_rect`; verify draw path calls same helper (not a parallel layout copy).
4. **Dungeon regression (R2)** — No automated dungeon travel-block draw test; acceptable for surface-only ticket repro. Impl should smoke-check `_draw_dungeon` + `hint_outside` branch manually if overlay API changes.
5. **Tall wrap edge case** — If wrapped hint height exceeds `overlay_rect.height`, `grid_rect.contains(hint_rect)` should fail — acceptable guard; unlikely at sidebar map sizes.
6. **Contrast / readability** — Muted-on-muted inside semi-transparent overlay deferred to human playtest (`human-test-plan.md` at Stage 7 per pipeline status); no color token change in scope.
7. **Wrap assert font sensitivity** — `len(wrapped) >= 2` depends on Consolas metrics at 11px; same dummy-SDL pattern as existing map tests; flag if CI font fallback differs.

## Summary

Plan is implementation-ready: layout-only fix scoped to `MapView`, spec R1–R5 and all ticket AC mapped to concrete helpers, API refactor, and a fail-pre placement test. Root-cause traces independently confirmed in live code. `qa-spec-pass` adversarial items (surface vs dungeon branch, wrap stress, test contract) are addressed. No missing Expected files, no orchestrator scope creep, no untestable core AC.

## Re-review focus

_None — proceed to workstreams + implementation (Stage 4)._
