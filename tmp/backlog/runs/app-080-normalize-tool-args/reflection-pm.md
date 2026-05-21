# Reflection: PM — APP-080 spec

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-llm-orchestrator-spec.md` (§ Tool argument normalization), `tmp/app-gamebridge-spec.md` (cross-link), `reflection-pm.md`

## Completed

- Wrote run-local [spec.md](./spec.md) with requirements R1–R5, test matrix, human playtest hints, and affected paths aligned to ticket Expected files.
- Promoted domain spec draft § Tool argument normalization to normative behavior in [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md): helpers, coercion table, wire points, failure modes, tests, changelog.
- Resolved **`fortune_spend.amount` mismatch**: ticket AC referenced a non-existent app tool param; spec targets `character_id` (str) and drops unknown keys; documented engine CLI vs bridge divergence.
- Cross-linked [tmp/app-gamebridge-spec.md](../../../app-gamebridge-spec.md) — bridge assumes orchestrator-supplied typed args; no markup stripping in bridge.
- Mapped `enter_dungeon` `site_id` → `site_address` migration from ad-hoc `_execute_tool` block into normalizer per research.

## Self-critique

- Creation/combat loop wiring is marked required in ticket AC but lower risk; run spec notes symmetry preference while v1 regression priority stays `_llm_loop` + `remember_fact`. Dev may time-box creation/combat if QA agrees — I did not demote in domain spec to avoid ticket AC drift.
- Markup stripping on `fact` (long prose) is intentionally minimal in v1; if corruption spreads to `fact` in future sessions, a follow-up ticket may be needed — called out in research, not expanded here.
- Optional APP-034 `tool_arg_coerced` logging left optional; no coordination with APP-034 ticket file in this pass.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths not traced — covered via research-brief echo
- [x] Tests or AC not mapped — test table in spec.md + domain spec Tests subsection
- [ ] Ticket file coercion table row for `fortune_spend.amount` — corrected in run/domain spec and ticket AC table (R3)

## Handoff

**Ready for:** QA spec review (adversarial gate)  
**Escalate human if:** QA rejects creation/combat loop scope as mandatory vs v1 priority, or requests `fortune_spend.amount` exposure in tools/bridge (engine change — new ticket)
