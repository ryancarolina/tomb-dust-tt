# Reflection: QA — APP-027 plan (round 1)

**Agent:** QA (adversarial plan review)  
**Round:** 1  
**Deliverables:** [qa-plan-pass.md](./qa-plan-pass.md)

## Completed

- Read ticket APP-027 Expected files, run `spec.md`, `qa-spec-pass.md` (round 2), domain § APP-027, and `plan.md`.
- Independently traced live code: `combat.py` spawn/INSERT order, `bridge.start_combat` exception mapping, missing `start_combat` in `tool_args.py`, `_llm_loop` APP-080 gate at L2572–2576, `_execute_tool` direct bridge at L2684–2685, beat/pending_start → `start_combat_from_trigger`, APP-028 `_COMBAT_TOOL_NAMES` strip, `_dispatch_like_llm_loop` in `test_tool_args.py`, `hollow-knight` absent from `build/data/monsters/`, `grave-ghoul.json` present.
- Verified plan scope ⊆ ticket Expected files; orchestrator wire correctly out of impl scope.
- Confirmed round 1 spec blockers (TICKET-001, SPEC-001) are resolved in plan (V5 dispatch helper, dedicated test module, engine-only R1, V8/V9 split).

## Self-critique

- **Session fixture gap** is the strongest adversarial finding but non-blocking: plan follows domain R2 ordering (validate after session resolution) without documenting test bootstrap — flagged for impl QA, not plan FAIL.
- Did not run pytest (plan gate only); regression commands listed in plan are sufficient for impl stage.
- Line anchors checked against 2026-05-22 tree; drift expected before impl.

## Did I miss anything?

- [x] Plan vs spec R1–R6 and V1–V9 mapping
- [x] Expected files gate
- [x] APP-028 substring / regression compatibility
- [x] TurnTruth bypass for code-owned failure lines
- [x] Beat path bypasses R3 (R2 only) — plan Flow D correct
- [x] qa-spec-pass round 2 resolution cross-check

## Handoff

**Verdict:** PASS  
**Report:** `tmp/backlog/runs/app-027-validate-monster-id-combat/qa-plan-pass.md`  
**Ready for:** Implementation (add session fixture note during test authoring)
