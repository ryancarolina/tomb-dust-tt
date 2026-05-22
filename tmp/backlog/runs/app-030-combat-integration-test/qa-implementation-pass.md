# QA PASS: Implementation — round 1

**Task:** app-030-combat-integration-test  
**backlog_ticket:** APP-030  
**ticket_path:** [tmp/backlog/app-030-combat-integration-test.md](../../app-030-combat-integration-test.md)  
**Round:** 1  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md) § Combat integration golden path (APP-030)

## Verdict

**PASS** — I1 bridge golden path green on real `GameBridge` + isolated workspace + roster PC; APP-027 V4 skip removed; combat regression modules unchanged.

## Automated tests

```text
python -m pytest app/tests/test_combat_integration.py -q
1 passed in 0.20s

python -m pytest app/tests/test_combat_monster_validation.py -q
7 passed in 1.62s

python -m pytest app/tests/test_combat_attack_gating.py -q
9 passed in 3.31s

python -m pytest app/tests/test_combat_failure_narration.py -q
11 passed in 1.56s

python -m pytest play/tomb_gm/tests/test_combat_attack.py -q
2 passed in 0.25s
```

| Step | Module | Tests | Result |
|------|--------|-------|--------|
| 1 | `app/tests/test_combat_integration.py` | I1 `test_bridge_combat_start_attack_end` | ✓ 1 |
| 2 | `app/tests/test_combat_monster_validation.py` | V1–V3, V5–V8 (no V4 skip) | ✓ 7 |
| 3 | `app/tests/test_combat_attack_gating.py` | G1–G8 + G6b regression | ✓ 9 |
| 4 | `app/tests/test_combat_failure_narration.py` | T1–T11 regression | ✓ 11 |
| 5 | `play/tomb_gm/tests/test_combat_attack.py` | Engine contract reference | ✓ 2 |

**Combined run:** 30 passed in 4.52s (verbose batch).

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| **I1** — bridge golden path `start_combat` → PC turn → `combat_attack` → `combat_end`; roster PC + `grave-ghoul:1` | `test_combat_integration.py` L33–68; helpers L10–30 | ✓ |
| **V4 absorption** — remove skipped `test_bridge_valid_grave_ghoul` | Test absent from validation module; repo grep shows references only in docs/plan | ✓ |
| Domain spec § APP-030 + changelog on close | § drafted in domain spec; **done** changelog + open-work removal deferred to Stage 6 (`release --done`) | pending close |

## Spec R1–R7 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | New `test_combat_integration.py` + helpers | Module docstring L1; `_ensure_combat_roster_session`, `_advance_to_pc_turn` | ✓ |
| **R2** | Isolated workspace → campaign → session → roster | `conftest.py` `bridge` uses `make_isolated_workspace`; helper L11–17; `character_create` without explicit `skill_ids` (militia defaults) | ✓ |
| **R3** | I1 golden path assertions | L36–68: start ok + `combat_start`; combatants PC + ghoul; attack ok; end ok; `combat is None` | ✓ |
| **R4** | Turn advance via `run_combat_monster_turns` + cap | L21–30: `is_pc_turn` poll; explicit `pytest.fail` on early end / cap | ✓ |
| **R5** | Resolve ids from combatants, not hardcoded `sammy` | L49–60: re-read combatants post-advance; `turn_id` when PC turn; ghoul prefix match | ✓ |
| **R6** | V4 delete | Validation module ends at V3 (L85–88) then V5 (L91+); 7 tests, 0 skipped | ✓ |
| **R7** | Never mutate `play/workspace` | `conftest.py` isolated fixture only | ✓ |

## I1 step trace (verified)

| Step | Plan | Implementation | Result |
|------|------|----------------|--------|
| 1 | `_ensure_combat_roster_session` | L34 | ✓ |
| 2 | `start_combat(["grave-ghoul:1"])` | L36–38 | ✓ |
| 3 | PC + ghoul in combatants | L40–47 | ✓ |
| 4 | `_advance_to_pc_turn` | L49 | ✓ |
| 5 | Resolve attacker/target | L50–60 | ✓ |
| 6 | `combat_attack` + combat still active | L62–64 | ✓ |
| 7 | `combat_end` + `combat is None` | L66–68 | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/tests/test_combat_integration.py` | **new** — I1 + helpers | ✓ |
| `app/tests/test_combat_monster_validation.py` | V4 skip test deleted; docstring V1–V8 | ✓ |
| `app/gm/bridge.py` | no change (plan) | N/A — correct |
| `tmp/app-combat-play-spec.md` | § APP-030 drafted; impl **done** changelog not yet appended | close stage |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Domain spec close** | Remove APP-030 from § Open work + append dated **done** changelog on `release APP-030 --done`. |
| **Ticket checkboxes** | Backlog AC still `[ ]` — update at close. |
| **Initiative seed** | No `seed` on bridge `start_combat`; turn-advance loop handles monster-first order — passed locally in 0.20s. |
| **I2/I3 stretch** | Orchestrator chain tests explicitly out of scope per plan/spec. |
| **Human playtest** | Stage 7 `human-test-plan.md` not run in QA — test-only ticket. |
| **DRY helper extract** | `_ensure_salt_road_session` duplicated across validation + integration modules — acceptable per plan; optional follow-up. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-030 --done` (domain changelog, ticket AC ticks).  
**Stage 7:** Optional manual PyGame combat smoke — not required for test-only AC.
