# Reflection: Dev plan — APP-027

**Agent:** Dev  
**Round:** 1  
**Deliverables:** [plan.md](./plan.md)

## Completed

- Re-read ticket Expected files, run `spec.md`, `qa-spec-pass.md`, domain § APP-027 (R1–R6, V1–V9).
- Traced live code: `combat.py` spawn/INSERT order (L237 before L249), `bridge.start_combat` exception mapping (L224–239), `tool_args.validate_tool_args` missing `start_combat` branch (L164–191), `_llm_loop` APP-080 gate already at L2572–2576, `_execute_tool` direct bridge at L2684–2685, beat/pending_start → `start_combat_from_trigger` (L2480–2499, L2266–2273), APP-028 `_COMBAT_TOOL_NAMES` strip (L2615–2628).
- Locked **orchestrator.py out of impl scope** — R4 satisfied by existing wire; changes confined to engine + bridge + tool_args + tests (+ optional tools.py).
- Standardized empty-list error on **`monster_specs required`** across R1 and R3 (QA adversarial note 1).
- Mapped V5 to `_dispatch_like_llm_loop` from `test_tool_args.py`; V8 explicitly unmocked bridge vs APP-028 T3 mocks; V9 split to engine module per SPEC-004.

## Self-critique

- **Line anchors** (~2572, ~2684, ~224) verified 2026-05-22; may drift before impl.
- **`_normalize_start_combat` coercion** (single string → list) is implied but not in PM spec — included as minimal APP-080 consistency; skip if YAGNI unless tests need it.
- **Engine `start_combat` early R1 call** marked optional — bridge R2 is AC-critical; engine top-of-function return avoids CLI inconsistency but is not ticket AC.
- **V4 happy path** deferred/skipped — acceptable per spec; APP-030 owns golden start.
- **V7 roster:** Assumes JSON-missing fails before `spawn_roster_combatants` — true in current `_spawn_instances`-before-party order; re-verify if engine order changes.

## Did I miss anything?

- [x] Ticket scope / Expected files — plan ⊆ `app/gm/`, `play/tomb_gm/`, `app/tests/test_combat_monster_validation.py`
- [x] Domain spec / registry_gap / AGENTS.md — engine-only R1; no canon edits; spec sync on close documented
- [x] Code paths traced — validate_monster_specs, bridge, validate_tool_args, _llm_loop, beat/pending_start, V1–V9
- [x] APP-028 substring stability — contractual `monster JSON not found: {id}`
- [x] TurnTruth bypass for code-owned failure lines
- [x] No `test_tool_args.py` expansion (optional superseded by V5)
- [x] Mixed-tool fiction explicitly out of scope

## Handoff

**Ready for:** QA plan gate (Stage 4) → implementation  
**Escalate human if:** QA plan requires orchestrator changes for mixed-tool fiction or beat regex content fix under APP-027 scope
