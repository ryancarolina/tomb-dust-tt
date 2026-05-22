# Reflection: QA — APP-041 spec (round 2)

**Agent:** QA  
**Round:** 2 (post PM r2)  
**Deliverables:** `qa-spec-pass.md`, `reflection-qa-spec-r2.md`

## Completed

- Re-read ticket, `spec.md`, domain spec § APP-041, `reflection-pm-r2.md`, round 1 `qa-spec-report-1.md`
- Verified PM fixes for TICKET-001, TICKET-002, SPEC-001 against ticket + run spec + domain spec
- Re-ran live `parse_scene` probes for leak matrix and AV-GRID preservation (pre-impl baseline)
- Confirmed `app/ui/app.py` display/speak split and `queue.py` / `cmd_speak.py` CLI bypass traces

## Verdict rationale

**PASS** — Round 1 had three actionable gaps (hook allow-list, missing panel AC, false CLI “no bypass” claim). All three are closed in PM r2 with consistent wording across ticket, run spec, and domain spec. SPEC-002 remains a documented residual risk; PM explicitly deferred it; acceptable for spec gate.

## Self-critique

- Did not re-read full `research-brief.md` end-to-end — run spec + probes sufficient for r2 gate
- Did not elevate `--beat-id` / stored `speak_lines` to a finding — same dev-only bypass family as `--lines`; noted non-blocking in pass
- Did not run pytest (no implementation; spec-stage gate only)

## Did I miss anything?

- [x] TICKET-001 Expected files — resolved
- [x] TICKET-002 panel AC — resolved
- [x] SPEC-001 CLI scope — resolved (non-goal)
- [x] Domain spec / registry_gap — aligned
- [x] AC testability + mapping — both ACs covered
- [x] Code traces — leak matrix matches spec problem table

## Orchestrator recommendation

**Dispatch Dev agent (plan phase)** with `qa-spec-pass.md`, `spec.md`, `research-brief.md`, ticket Expected files. No further PM spec revision unless product requires dev CLI strip (escalate per `reflection-pm-r2.md`).
