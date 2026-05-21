# Reflection: PM — APP-024 spec (round 2)

**Agent:** PM  
**Round:** 2  
**Trigger:** QA spec FAIL — `qa-spec-report-1.md` blockers SPEC-001, TICKET-001; SCOPE-001  
**Deliverables:** `spec.md`, `tmp/app-exploration-delve-spec.md`, `tmp/backlog/app-024-block-site-fiction-without-enter-tool.md`, `status.md`, `reflection-pm-r2.md`

## Blockers addressed

| ID | Fix |
|----|-----|
| **SPEC-001** | E1 now mandates sticky `entry_committed_this_turn` (or full-chain scan), explicitly forbids inferring commit from final `_last_tool_results[tool_name]` because L1978 overwrites per name. Domain spec § Entry committed + § Wiring aligned. |
| **TICKET-001** | AC rewritten: "current turn's tool chain includes successful `enter_dungeon` / `site_enter`"; second AC for sticky commit (success-then-failed same tool). Run `spec.md` § Entry commit vs engine mode + AC mapping updated. |
| **SCOPE-001** | `app/tests/test_exploration_site_entry_gate.py` added to ticket Expected files and spec Affected paths. |

## Additional changes

- Regression test **`test_success_then_failed_enter_dungeon_retains_fiction`** added to run spec and domain spec test table (seven cases total).
- `status.md` goal line aligned with clarified AC.

## Non-blockers (deferred)

| ID | Decision |
|----|----------|
| **NOTE-001** | `app-llm-orchestrator-spec.md` cross-link — defer to ticket close; mechanical truth already consistent. |
| **NOTE-002** | Refusal copy — still pinned at Dev plan / impl QA per APP-070 pattern. |

## Self-critique

- Root cause was PM r1 conflating "any success in chain" prose with `_last_tool_results` as the implementation signal — QA correctly caught the overwrite bug.
- Sticky flag is the simplest implementer-facing contract; full-chain scan of a per-turn results list is acceptable alternative if Dev prefers not to add instance state beyond the loop.

## Handoff

**Ready for:** QA spec re-review (round 2)  
**Re-review focus:** E1 flag semantics, ticket AC ↔ spec mapping, Expected files include test module, success-then-failed regression case
