# Reflection: QA spec — APP-091 round 1

**Agent:** QA (adversarial)
**Round:** 1
**Deliverables:** qa-spec-pass.md, reflection-qa-spec.md

## Completed

- Read ticket APP-091 AC, run `spec.md`, domain `tmp/app-pygame-ui-spec.md` § Map travel during creation / Hint placement (APP-091), `research-brief.md`, `reflection-pm.md`, dev-team templates.
- Cross-walked all five ticket AC rows to run spec R1–R5 and domain placement table.
- Spot-checked live code at `map_view.py` L210–226, L278–291 and `test_ui_map_creation_gate.py` (10 tests, no blit-position coverage).
- Verified `registry_gap: false`, Expected files alignment, and APP-037 parent scope boundaries.

## Verdict rationale

Default FAIL bar not met: no missing AC, no wrong domain owner, no untestable core behavior, collision coordinates confirmed in repo. Issued **PASS** with non-blocking notes on pre-impl domain Layers wording, weak dungeon-path test coverage, and Dev-plan API branching for surface vs dungeon overlay helper.

## Self-critique

- Did not run pytest (spec stage; no impl).
- Did not read full APP-037 run spec line-by-line — relied on research + domain cross-refs for parent non-regression.
- Did not verify markdown anchor `#hint-placement-app-091` renders in GitHub preview (heading matches convention).
- Narrow-sidebar wrap has no automated minimum-width AC — acceptable per ticket but Dev plan should cite manual step.

## Did I miss anything?

- [x] Ticket AC ↔ spec ↔ domain
- [x] registry_gap / expected files / AGENTS.md drift policy
- [x] Research code-path traces vs live file
- [x] Test gap (blit position) addressed in R4
- [ ] Whether hint should show only when hovering grid vs full panel — current `_hovering` is panel-wide; spec silent; behavior unchanged from APP-037 (not escalated)

## Handoff

**Ready for:** Dev plan (`plan.md`) — surface path: center/wrap hint inside `grid_rect`; preserve dungeon `y + 4` path or explicit branch; extract testable hint rect; confirm new test fails on current main before impl.

**Escalate human if:** Plan moves hint below footer (requires footer height budget change per research) or expands into APP-063 map UX.

**Orchestrator:** Mark Stage “QA spec PASS (round 1)” in `status.md`; dispatch Dev plan round 1.
