# Drift Check: APP-030-combat-integration-test

**backlog_ticket:** APP-030  
**Date:** 2026-05-22  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) | no | § **Combat integration golden path (APP-030)** matches code; checklist **APP-030** `[x]`; I1 Pass ✓; APP-030 removed from § Open work; changelog **APP-030 done** appended |
| Run [`spec.md`](./spec.md) R1–R7 | no | Verified against `test_combat_integration.py`, `test_combat_monster_validation.py`, `conftest.py` |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Registry row **Combat play** still accurate; no priority-table change required |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** New `test_combat_integration.py` + helpers | `app/tests/test_combat_integration.py` L1–30 | yes |
| **R2** Isolated workspace → campaign → session → roster | `conftest.py` `bridge` via `make_isolated_workspace`; `_ensure_combat_roster_session` L10–18 | yes |
| **R3** I1 golden path assertions | L33–68: start ok + `combat_start`; PC + ghoul combatants; attack ok; end ok; `combat is None` | yes |
| **R4** Turn advance via `run_combat_monster_turns` + cap | L21–30: `is_pc_turn` poll; `pytest.fail` on early end / cap | yes |
| **R5** Resolve ids from combatants, not hardcoded | L49–60: `turn_id` when PC turn; ghoul prefix match | yes |
| **R6** V4 delete — no skipped happy-start test | `test_combat_monster_validation.py` V1–V3 then V5–V8; 7 tests, 0 skipped | yes |
| **R7** Never mutate `play/workspace` | `conftest.py` isolated fixture only | yes |

## Ticket AC → verification

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| **I1** — bridge golden path `start_combat` → PC turn → `combat_attack` → `combat_end`; roster PC + `grave-ghoul:1` | `test_bridge_combat_start_attack_end` L33–68 | ✓ |
| **V4 absorption** — remove skipped `test_bridge_valid_grave_ghoul` | Test absent from validation module; happy start is I1 step 2 | ✓ |
| Domain spec § APP-030 + changelog on close | § drafted; checklist + **done** changelog synced at drift close | ✓ |

## Tests run

```bash
python -m pytest app/tests/test_combat_integration.py app/tests/test_combat_monster_validation.py app/tests/test_combat_attack_gating.py app/tests/test_combat_failure_narration.py -q
```

**Result:** 28 passed in 4.14s

| ID | Test | Result |
|----|------|--------|
| **I1** | `test_bridge_combat_start_attack_end` | ✓ |
| APP-027 | V1–V3, V5–V8 (7 tests, no V4 skip) | ✓ |
| APP-026 | G1–G8 + G6b (9 tests) | ✓ |
| APP-028 | T1–T11 (11 tests) | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [x] Domain spec changelog **APP-030 done** appended; APP-030 removed from § Open work
- [ ] `python tmp/backlog/claim_ticket.py release APP-030 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes (non-blocking)

- **Initiative seed:** No `seed` on bridge `start_combat`; `_advance_to_pc_turn` handles monster-first order — passed locally.
- **I2/I3 stretch:** Orchestrator chain tests explicitly out of scope per spec.
- **DRY helper:** `_ensure_salt_road_session` duplicated across validation + integration modules — acceptable per plan.
- **Human playtest:** Stage 7 optional PyGame combat smoke — test-only ticket; not required for AC.
