# Drift Check: APP-026-combat-attack-gating

**backlog_ticket:** APP-026  
**Date:** 2026-05-22  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) | no | § **Combat attack gating (APP-026)** matches code; checklist **APP-026** `[x]`; G1–G8 + G6b Pass ✓; changelog **APP-026 done** (2026-05-22) already present from impl close |
| Run [`spec.md`](./spec.md) R1–R5 | no | Verified against `orchestrator.py`, `test_combat_attack_gating.py` |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Registry row `app-combat-play-spec → combat tool gating` still accurate; no priority-table change required |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** `_gate_pc_attack(attacker_id) -> dict \| None` | `orchestrator.py` L494–509 | yes |
| **R1** Fresh `bridge.status()` inside gate | L496 | yes |
| **R1** No combat → `"no active combat for session"` | L498–499 | yes |
| **R1** Resolve id/displayName (case-insensitive) | `_resolve_combatant_id_for_gate` L364–373 | yes |
| **R1** Resolved id ∈ initiative | L505–507 | yes |
| **R1** No bridge/engine call from gate | L494–509 (status read only) | yes |
| **R2** Wire `_execute_tool` → `combat_attack` | L2686–2689 gate before `bridge.combat_attack` | yes |
| **R3** Wire `_execute_combat_action` when `action.upper().strip() == "ATTACK"` | L2462–2464 | yes |
| **R3** Turn check unchanged after gate | L2469–2471 | yes |
| **R4** APP-028 compatibility — same `{ok: false}` shape | G7 + 11/11 `test_combat_failure_narration.py` | yes |
| **R5** `tools.py` optional touch | Skipped (not required for AC) | yes (optional) |

## Ticket AC → verification

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Before attack: require `status.combat` | `_gate_pc_attack` L498–499; G1 `combat_attack` not called; G4 `combat_action` not called | ✓ |
| Attacker in initiative | L505–507 initiative id set; G2, G5, G8 reject; G3/G6/G6b pass | ✓ |

## Tests run

```bash
python -m pytest app/tests/test_combat_attack_gating.py app/tests/test_combat_failure_narration.py -q
```

**Result:** 20 passed (3.61s)

| ID | Test | Result |
|----|------|--------|
| **G1** | `test_execute_tool_combat_attack_gated_no_combat` | ✓ |
| **G2** | `test_gate_pc_attack_rejects_unknown_attacker` | ✓ |
| **G3** | `test_gate_pc_attack_resolves_display_name` | ✓ |
| **G4** | `test_execute_combat_action_attack_no_combat` | ✓ |
| **G5** | `test_execute_combat_action_attack_not_in_initiative` | ✓ |
| **G6** | `test_execute_tool_combat_attack_passes_gate` | ✓ |
| **G6b** | `test_execute_combat_action_attack_passes_gate` | ✓ |
| **G7** | `test_app028_t4_regression` | ✓ |
| **G8** | `test_execute_combat_action_lowercase_attack_not_in_initiative` | ✓ |
| APP-028 | `test_combat_failure_narration.py` (11 tests) | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [ ] `python tmp/backlog/claim_ticket.py release APP-026 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes (non-blocking)

- **`orchestrator.py` batch noise:** Working tree may include unrelated APP-022 / APP-034 hunks; APP-026 gate symbols and wire points are isolated.
- **Flow B untested:** When combat active, exploration `combat_attack` blocked by combat-only tool guard before gate — documented in plan; not required for AC.
- **Dual no-combat strings:** ATTACK path returns `"no active combat for session"` via gate; non-ATTACK combat_action path may still return `"no active combat"` — spec-aligned defense-in-depth.
- **Human playtest:** Stage 7 — attack outside combat shows `[Mechanics failed — …]` with no hit fiction; valid combat ATTACK unchanged.
