# QA PASS: implementation — round 1

**Task:** app-026-combat-attack-gating  
**backlog_ticket:** APP-026  
**ticket_path:** [tmp/backlog/app-026-combat-attack-gating.md](../../app-026-combat-attack-gating.md)  
**Round:** 1  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md) § Combat attack gating (APP-026)

## Verdict

**PASS** — R1–R4 implemented; `_gate_pc_attack` + `_resolve_combatant_id_for_gate` wired on exploration `combat_attack` and combat-loop ATTACK; G1–G8 + G6b green; APP-028 full-module regression green (20/20).

## Automated tests

```text
python -m pytest app/tests/test_combat_attack_gating.py app/tests/test_combat_failure_narration.py -v
20 passed in 3.39s
```

| ID | Test | Result |
|----|------|--------|
| **G1** | `test_execute_tool_combat_attack_gated_no_combat` | ✓ |
| **G2** | `test_gate_pc_attack_rejects_unknown_attacker` | ✓ |
| **G3** | `test_gate_pc_attack_resolves_display_name` | ✓ |
| **G4** | `test_execute_combat_action_attack_no_combat` | ✓ |
| **G5** | `test_execute_combat_action_attack_not_in_initiative` | ✓ |
| **G6** | `test_execute_tool_combat_attack_passes_gate` | ✓ |
| **G6b** | `test_execute_combat_action_attack_passes_gate` | ✓ |
| **G7** | `test_app028_t4_regression` (subprocess full module) | ✓ |
| **G8** | `test_execute_combat_action_lowercase_attack_not_in_initiative` | ✓ |
| APP-028 | `test_combat_failure_narration.py` (11 tests) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Before attack: require `status.combat` | `_gate_pc_attack` L497–499; G1 `bridge.combat_attack` not called; G4 `bridge.combat_action` not called | ✓ |
| Attacker in initiative | `_gate_pc_attack` L505–507 initiative id set; G2, G5, G8 reject; G3/G6/G6b pass | ✓ |

## Spec requirements → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | `_gate_pc_attack(attacker_id) -> dict \| None` | `orchestrator.py` L494–509; fresh `bridge.status()`; no bridge/engine call | ✓ |
| **R1** | Combatant resolution (id + displayName, case-insensitive) | `_resolve_combatant_id_for_gate` L364–373 mirrors engine `combat.py` L476–485 | ✓ |
| **R1** | Error strings engine-aligned | `"no active combat for session"`, `f"attacker not in combat: {attacker_id}"` | ✓ |
| **R2** | Wire exploration `combat_attack` | `_execute_tool` L2686–2689 gate before `bridge.combat_attack` | ✓ |
| **R3** | Wire combat `combat_action` ATTACK (case-normalized) | `_execute_combat_action` L2462–2464 `action.upper().strip() == "ATTACK"` | ✓ |
| **R3** | Turn check unchanged after gate | L2469–2471 `not your turn` after gate on ATTACK path | ✓ |
| **R4** | APP-028 compatibility | G7 + 11/11 `test_combat_failure_narration.py`; gate errors feed same `{ok: false}` shape | ✓ |
| **R5** | Optional `tools.py` touch | Skipped (not required for AC) | ✓ (optional) |

## Wire-point verification

| Path | Gate runs | Bridge blocked on fail | Test |
|------|-----------|------------------------|------|
| `_execute_tool` → `combat_attack` | `_gate_pc_attack(args.get("attacker_id", ""))` | `combat_attack.assert_not_called()` | G1, G6 |
| `_execute_combat_action` ATTACK | `_gate_pc_attack(actor_id)` when `action.upper().strip() == "ATTACK"` | `combat_action.assert_not_called()` | G4, G5, G8, G6b |
| Lowercase `"attack"` | Same ATTACK branch (SPEC-001) | G8 | ✓ |

## Diff scope reviewed

| File | APP-026 change | In ticket Expected files? |
|------|----------------|---------------------------|
| `app/gm/orchestrator.py` | `_resolve_combatant_id_for_gate`, `_gate_pc_attack`, R2/R3 wire | ✓ |
| `app/tests/test_combat_attack_gating.py` | **new** G1–G8 + G6b | ✓ |
| `tmp/app-combat-play-spec.md` | § Combat attack gating, checklist, changelog | ✓ (close-stage sync) |
| `app/gm/tools.py` | No change (R5 optional skipped) | ✓ |

**Batch note:** `orchestrator.py` working tree also contains unrelated deltas (APP-022 delve hints, APP-034 API error logging). APP-026 gate symbols and wire points are isolated and correct; no APP-026 behavior depends on those hunks.

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Flow B untested** | When combat active, existing combat-only tool guard blocks `combat_attack` before gate — documented in plan; not required for AC |
| **Empty `attacker_id`** | Resolves to `attacker not in combat: ` — matches engine pattern; no G9 test (plan accepted) |
| **Dual no-combat strings** | ATTACK path: `"no active combat for session"` via gate; non-ATTACK: `"no active combat"` from defense-in-depth check — spec-aligned |
| **G7 subprocess** | Re-runs full `test_combat_failure_narration.py` via subprocess; passed; in-process import would be equivalent |
| **Ticket close** | Backlog ticket still `in_progress`; domain spec changelog marks APP-026 done — `release APP-026 --done` pending Stage 6 |
| **Human playtest** | Stage 7 — attack outside combat shows `[Mechanics failed — …]` with no hit fiction |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-026 --done` + human playtest plan.
