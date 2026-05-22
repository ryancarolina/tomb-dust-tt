# Reflection: PM — APP-027 spec r2

**Agent:** PM  
**Round:** 2 (QA spec revision)  
**Deliverables:** `spec.md`, `tmp/app-combat-play-spec.md`, ticket Expected files, `reflection-pm-r2.md`

## Completed

- **TICKET-001:** Added `app/tests/test_combat_monster_validation.py` to ticket Expected files; run `spec.md` Affected paths aligned (V1–V8 + optional `test_tool_args.py`).
- **SPEC-001:** V5 rewired to `_dispatch_like_llm_loop` (APP-080); R3/R4 and validation-layer table corrected — `validate_tool_args` runs in `_llm_loop` before `_execute_tool`, not inside `_execute_tool`.
- **SPEC-002:** R1 mandates `play/tomb_gm/services/simulation/combat.py` as sole `validate_monster_specs` implementation; bridge imports engine module only.
- **SPEC-003:** V8 defined as unmocked `_llm_loop` integration with real `content_root` and `hollow-knight:1`; explicitly not satisfied by APP-028 T3 mocks alone.
- **SPEC-004:** V9 split to new `play/tomb_gm/tests/test_validate_monster_specs.py`; `test_simulation.py -k unknown_monster` demoted to optional CLI regression.

## Self-critique

- V4 happy-path bridge test still optional/deferrable to APP-030 — unchanged from r1.
- Did not add `play/tomb_gm/tests/test_validate_monster_specs.py` to ticket Expected files — covered by existing `play/tomb_gm/` glob; Dev should still create the named module per V9.
- V6 keeps direct `_execute_tool` to exercise bridge R1 — intentional; differs from V5 tool-args layer.

## Did I miss anything?

- [x] TICKET-001 — test module in Expected files
- [x] SPEC-001 — V5 + R3/R4 wire prose
- [x] SPEC-002 — engine-only R1
- [x] SPEC-003 — V8 integration contract
- [x] SPEC-004 — V9 vs CLI split
- [x] Domain spec sync + changelog r2 entry
- [ ] `app-llm-orchestrator-spec.md` cross-ref — deferred (combat-play spec owns APP-027 behavior)

## Handoff

**Ready for:** QA spec re-review (round 2) — focus on V5 `_dispatch_like_llm_loop`, V8 unmocked `_llm_loop`, V9 engine module path

**Escalate human if:** Product wants validation duplicated inside `_execute_tool` for defense-in-depth (spec forbids — conflicts with APP-080)
