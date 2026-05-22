# QA PASS: spec — round 1

**Task:** app-091-map-hint-overlap-fix
**backlog_ticket:** APP-091
**ticket_path:** [tmp/backlog/app-091-map-travel-block-hint-overlap-fix.md](../../app-091-map-travel-block-hint-overlap-fix.md)
**Round:** 1
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § File map (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R5, ticket AC, pytest commands)
- [x] Code traces match repo (collision at `map_view.py` L210–213, L224–226, L278–291)
- [x] AGENTS.md / canon compliance (app UI layout-only; no mechanics drift)
- [x] Tests/commands listed (`test_ui_map_creation_gate.py`, creation-flow regression)
- [x] registry_gap false — pygame-ui domain spec owns § Map travel during creation
- [x] Every ticket AC row mapped in run spec + domain § Hint placement (APP-091)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 bug; in_progress; three Expected files |
| registry_gap | **PASS** | false; justified in research-brief § Registry gap justification |
| AC testability | **PASS** | Placement test + manual repro; wrap/readability manual |
| Code traces | **PASS** | Shared `grid_y + grid_h + 16` for `displayName` and hint confirmed |
| Expected files ⊆ spec scope | **PASS** | `map_view.py`, `test_ui_map_creation_gate.py`, domain spec |
| Domain spec sync | **PASS** | § Hint placement (APP-091) + draft changelog; finalize on close per R5 |
| Parent APP-037 non-regression | **PASS** | R3 locks gate behavior; no orchestrator/sidebar scope creep |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Hint does not overlap `displayName` or scene line | R1; domain § Draw inside overlay / Footer reserved / No footer-row hint | unit test inside `overlay_rect` + manual `32-C` | **PASS** |
| Readable on narrow sidebar (APP-062) | R1 wrap; domain § Wrap on narrow column | manual at ~30% width; no automated min-width test | **PASS** |
| Default hint string unchanged | R3; domain § Copy unchanged | `test_map_view_default_hint_string` (existing) | **PASS** |
| Unit test for hint blit placement | R4; domain § Tests APP-091 | new test fail-pre/pass-post contract | **PASS** |
| Domain spec § + changelog on close | R5; domain § Hint placement + draft changelog L361 | review + release step | **PASS** |

## Code evidence (root cause)

| Location | Finding |
|----------|---------|
| `app/ui/panels/map_view.py:210–213` | `info_y = grid_y + grid_h + 16`; `displayName` blitted at `(x, info_y)` |
| `app/ui/panels/map_view.py:224–226` | `_draw_travel_block_overlay(..., x, grid_y + grid_h + 16)` — same Y as footer |
| `app/ui/panels/map_view.py:289–291` | Hover hint blitted at external `(hint_x, hint_y)` — overlaps footer text |
| `app/tests/test_ui_map_creation_gate.py` | 10 tests; no draw-position assertions (gap addressed by R4) |

## Adversarial notes (non-blocking)

1. **Pre-impl domain wording** — `tmp/app-pygame-ui-spec.md` L127 states hint inside grid overlay under Layers; code still uses footer-row Y until impl. Draft changelog L361 marks APP-091 in flight; acceptable for spec gate.
2. **Dungeon path (R2)** — Non-regression relies on smoke (existing tests green); no dungeon travel-block draw test today. Ticket repro is surface-only at `32-C`; Dev plan should branch surface vs dungeon in overlay helper if API refactors.
3. **Wrap / contrast** — Multi-line centering inside semi-transparent overlay unspecified at pixel level; human playtest should confirm muted-on-muted readability (research risk).
4. **API shape** — R1 allows refactor of `_draw_travel_block_overlay` hint params; Dev plan should spell surface (rect-centered) vs dungeon (legacy `y + 4`) to avoid accidental dungeon layout change.
5. **APP-037 human TC-3** — Prior playtest allowed “below/near grid”; APP-091 tightens to inside-overlay — intentional AC upgrade, not scope creep.

## Summary

Ticket, run `spec.md`, and domain § Hint placement (APP-091) are aligned, testable, and scoped to layout-only fix within the correct domain spec. Root-cause line numbers match research and live code. No registry gap, no missing Expected files, no untestable ticket AC. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
