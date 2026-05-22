# Dev implementation reflection — APP-026 (ws1)

**backlog_ticket:** APP-026  
**Agent:** Dev  
**Date:** 2026-05-22

## What shipped

- **`_resolve_combatant_id_for_gate`** — module-level helper in `app/gm/orchestrator.py`; mirrors engine combatant resolution (id + displayName, case-insensitive).
- **`_gate_pc_attack(attacker_id) -> dict | None`** — reads fresh `bridge.status()`, requires `status.combat`, checks resolved attacker ∈ `initiative[].id`; returns engine-aligned errors without calling bridge/engine.
- **R2 wire** — `_execute_tool` → `combat_attack`: gate before `bridge.combat_attack`.
- **R3 wire** — `_execute_combat_action`: gate when `action.upper().strip() == "ATTACK"` before turn check + `bridge.combat_action`.
- **Tests** — `app/tests/test_combat_attack_gating.py` G1–G8 + G6b per plan.
- **Spec** — `tmp/app-combat-play-spec.md` checklist + G pass marks + changelog.

## Verification

```bash
python -m pytest app/tests/test_combat_attack_gating.py app/tests/test_combat_failure_narration.py -v
# 20 passed
```

## Deviations / notes

- **Skipped optional R5** (`tools.py` description tweak) — not required for AC.
- **Dual no-combat strings preserved** — ATTACK path via gate returns `"no active combat for session"`; non-ATTACK still uses existing `"no active combat"` from `_execute_combat_action` (documented in plan/spec).
- **G7** runs full `test_combat_failure_narration.py` subprocess — T4 still passes; gate now supplies error before mock bridge would have been called (behavior change internal to error source, strip shape unchanged).

## Risks / follow-ups

- Empty `attacker_id` resolves to empty string not in initiative → `attacker not in combat: ` — not explicitly tested; matches engine pattern.
- Turn-order enforcement unchanged (by design); APP-027 engine validation still separate ticket.
