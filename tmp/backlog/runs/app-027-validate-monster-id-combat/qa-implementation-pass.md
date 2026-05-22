# QA PASS: implementation — round 1

**Task:** app-027-validate-monster-id-combat  
**backlog_ticket:** APP-027  
**ticket_path:** [tmp/backlog/app-027-validate-monster-id-at-combat-start.md](../../app-027-validate-monster-id-at-combat-start.md)  
**Round:** 1  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md) § Monster id validation at combat start (APP-027)

## Verdict

**PASS** — Layered validation (R1 engine, R2 bridge, R3 tool args) matches domain spec; stable error strings preserved for APP-028; V1–V9 and start_combat regression green.

## Automated tests

```text
python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -v
4 passed in 0.04s

python -m pytest app/tests/test_combat_monster_validation.py -v
7 passed, 1 skipped in 1.16s

python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -v
1 passed, 10 deselected in 0.53s
```

| Module | Tests | Result |
|--------|-------|--------|
| `play/tomb_gm/tests/test_validate_monster_specs.py` | V9 empty, invalid format, unknown JSON, canon happy | ✓ 4 |
| `app/tests/test_combat_monster_validation.py` | V1–V3 bridge, V5 R3 gate, V6–V8 orchestrator paths; V4 skipped (APP-030) | ✓ 7, skip 1 |
| `app/tests/test_combat_failure_narration.py` | APP-028 `start_combat` all-failed strip regression | ✓ 1 |

**Total:** 12 passed, 1 skipped (V4 per plan).

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Validate monster specs at `start_combat` | `validate_monster_specs` (R1); bridge pre-check (R2); `validate_tool_args("start_combat")` (R3) | ✓ |
| Clear error (no fiction on unknown id) | V1/V6/V7/V8 assert `{ok: false}` + substring; V8 strips pre-tool fiction; `status.combat` null | ✓ |

## Spec R1–R6 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Engine-only `validate_monster_specs` | `play/tomb_gm/services/simulation/combat.py` L37–52; early return in engine `start_combat` L255–257 | ✓ |
| **R2** | Bridge pre-check before engine | `app/gm/bridge.py` L229–231; `start_combat_from_trigger` delegates L311 | ✓ |
| **R3** | `validate_tool_args("start_combat")` before `_execute_tool` | `app/gm/tool_args.py` L147–160, L217–223; V5 mock not called | ✓ |
| **R4** | Wire: `_llm_loop`, beat, `pending_start` | Orchestrator unchanged; beat V7 real `start_combat_from_trigger` path | ✓ |
| **R5** | No fiction; combat null on fail | V6/V7/V8; APP-028 prefix `[Mechanics failed — start_combat:` / beat `combat start:` | ✓ |
| **R6** | Optional tool schema hygiene | `app/gm/tools.py` example uses `grave-ghoul:2`, `ash-shade:1` (no `hollow-knight`) | ✓ |

## Error string contract (APP-028 sibling)

| String | R1/R2/R3 | Test |
|--------|----------|------|
| `monster_specs required` | Empty/missing list | V3, V5, V9 |
| `invalid monster spec` | Bad format | V2, V9 |
| `monster JSON not found: hollow-knight` | Unknown id | V1, V6, V7, V8, V9 |
| `invalid monster_specs entry` | Non-string list element | R3 branch L222–223 |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `play/tomb_gm/services/simulation/combat.py` | R1 + engine `start_combat` early return | ✓ (engine path) |
| `app/gm/bridge.py` | R2 import + pre-check | ✓ |
| `app/gm/tool_args.py` | R3 whitelist, normalizer, validate branch | ✓ (within `app/gm/`) |
| `app/gm/tools.py` | R6 example hygiene | ✓ (within `app/gm/`) |
| `app/tests/test_combat_monster_validation.py` | **new** V1–V8 | ✓ |
| `play/tomb_gm/tests/test_validate_monster_specs.py` | **new** V9 | ✓ (engine tests) |
| `app/gm/orchestrator.py` | no wire change (plan) | N/A — correct |
| `tmp/app-combat-play-spec.md` | § APP-027 drafted; checklist/changelog **done** deferred | close stage |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **V4 skipped** | Happy `grave-ghoul:1` deferred to APP-030 per plan — acceptable. |
| **Double validation** | Bridge R2 + engine R1 both call `validate_monster_specs` — defense-in-depth per plan. |
| **Domain spec close** | § behavior matches impl; add impl-done changelog + tick checklist on `release APP-027 --done`. |
| **Ticket checkboxes** | Backlog AC still `[ ]` — update at close. |
| **Human playtest** | Stage 7 `human-test-plan.md` not run in QA. |
| **Beat content ids** | Non-canon ids in beat regex still fail at R2 — expected non-goal. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-027 --done` (domain changelog, ticket AC ticks).  
**Stage 7:** Manual PyGame repro — bogus `start_combat` id → mechanics-failed prefix, no combat HUD.
