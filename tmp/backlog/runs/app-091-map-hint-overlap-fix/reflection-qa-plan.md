# Reflection: QA plan — APP-091 round 1

**Agent:** QA (adversarial)  
**Round:** 1  
**Deliverables:** qa-plan-pass.md, reflection-qa-plan.md

## Completed

- Read run `plan.md`, `spec.md`, `qa-spec-pass.md`, ticket Expected files, domain § Hint placement (APP-091), `reflection-dev-plan.md`.
- Cross-walked spec R1–R5 and all five ticket AC rows to plan flows A–D, exact changes §1–3, and § Tests fail-pre contract.
- Independently traced live code: `map_view.py` surface collision (L210–226, L278–291), dungeon branch (L269–276), hover (L99–100), `app.py` enrich/hover (L68–69, L346–349), `sidebar.py` forward/resize (L33, L46–52).
- Verified plan file set ⊆ ticket Expected files (three paths only).
- Checked `qa-spec-pass` non-blocking notes for resolution in plan (dungeon `hint_outside`, API shape, wrap math, placement test).

## Verdict rationale

Default FAIL bar not met: no missing spec requirement, no scope outside Expected files, no untestable primary AC, no contradiction between draw fix and footer reservation. Issued **PASS** with non-blocking notes on stale MOUSEMOTION line ref, metrics-helper drift risk, and weak dungeon automation (accepted per ticket surface repro).

## Self-critique

- Did not run pytest (plan stage; no impl yet) — fail-pre contract reviewed logically (AttributeError on missing helper).
- Did not simulate pygame font metrics to confirm `len(wrapped) >= 2` at 240px width — relied on plan math + FONT_SIZE_SMALL derivation.
- Did not read full APP-037 run plan — parent non-regression inferred from R3 + existing test list + unchanged orchestrator/sidebar scope.
- Did not verify whether impl agent will create `human-test-plan.md` before manual contrast check — pipeline Stage 7 defers it; noted in pass notes.

## Did I miss anything?

- [x] Ticket AC ↔ spec R1–R5 ↔ plan sections
- [x] Expected files gate (strict ⊆)
- [x] Independent code trace vs plan line refs (found one stale ref)
- [x] qa-spec-pass adversarial carry-forward
- [x] Fail-pre / pass-post test contract
- [x] TurnTruth N/A for layout-only ticket
- [ ] Whether `_hovering` should be grid-only vs panel-wide — spec/plan silent; APP-037 behavior unchanged (not escalated)

## Handoff

**Ready for:** workstreams + implementation (single stream; 3 Expected files)  
**Impl QA watch:** shared `_layout_hint_placements` used by both draw and `_travel_block_hint_rect`; prefer `_compute_surface_grid` extraction; run full `test_ui_map_creation_gate.py` + manual `32-C` hover before spec changelog close.

**Escalate human if:** post-impl hint unreadable inside overlay (contrast) or plan deviates to footer-row hint (requires layout budget change).

**Orchestrator:** Mark Stage “QA plan PASS (round 1)” in `status.md`; dispatch implementation.
