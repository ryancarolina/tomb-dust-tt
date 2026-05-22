# Drift Check: APP-027-validate-monster-id-combat

**backlog_ticket:** APP-027  
**Date:** 2026-05-22  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) | no | § **Monster id validation at combat start (APP-027)** matches code; checklist **APP-027** `[x]`; V1–V9 Pass ✓ (V4 skip); changelog **APP-027 done** added |
| Run [`spec.md`](./spec.md) R1–R6 | no | Verified against `combat.py`, `bridge.py`, `tool_args.py`, `tools.py`, test modules |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Registry row **Combat play** still accurate; no priority-table change required |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** Engine-only `validate_monster_specs(content_root, monster_specs) -> str \| None` | `play/tomb_gm/services/simulation/combat.py` L37–52 | yes |
| **R1** Empty list → `monster_specs required` | L39–40 | yes |
| **R1** Bad format → `invalid monster spec` | L44–47 via `parse_monster_specs` | yes |
| **R1** Missing JSON → `monster JSON not found: {id}` | L49–51 | yes |
| **R1** Engine `start_combat` early return before INSERT | L255–257 | yes |
| **R2** Bridge pre-check before engine dispatch | `app/gm/bridge.py` L229–231 | yes |
| **R2** `start_combat_from_trigger` duplicate guard before validation | L308–311 delegates to `start_combat` | yes |
| **R2** Defense-in-depth `except (ValueError, FileNotFoundError)` retained | L242–243 | yes |
| **R3** `validate_tool_args("start_combat")` empty/missing list | `app/gm/tool_args.py` L217–220 | yes |
| **R3** Non-string entry → `invalid monster_specs entry` | L221–223 | yes |
| **R3** Normalizer strips empty strings before validate | `_normalize_start_combat` L147–160 | yes |
| **R4** Exploration `_llm_loop` validate-before-execute (APP-080) | V5 mock `start_combat` not called | yes |
| **R4** Beat trigger + `pending_start` via bridge R2 | V7 real path; orchestrator unchanged | yes |
| **R5** No fiction; `status.combat` null on fail | V6/V7/V8; APP-028 prefix shapes | yes |
| **R6** Tool schema canon examples (optional) | `app/gm/tools.py` `grave-ghoul:2`, `ash-shade:1` | yes |

## Ticket AC → verification

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Validate monster specs at `start_combat` | R1 engine + R2 bridge + R3 tool args; V1–V3, V5–V6, V9 | ✓ |
| Clear error (no fiction on unknown id) | V1/V6/V7/V8 error substrings; V8 strips pre-tool fiction; `status.combat` null | ✓ |

## Tests run

```bash
python -m pytest app/tests/test_combat_monster_validation.py play/tomb_gm/tests/test_validate_monster_specs.py -v
python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q
```

**Result:** 11 passed, 1 skipped (V4 → APP-030); 1 passed (APP-028 `start_combat` regression)

| ID | Test | Result |
|----|------|--------|
| **V1** | `test_bridge_unknown_monster_id` | ✓ |
| **V2** | `test_bridge_invalid_monster_spec_format` | ✓ |
| **V3** | `test_bridge_empty_monster_specs` | ✓ |
| **V4** | `test_bridge_valid_grave_ghoul` | skip (APP-030) |
| **V5** | `test_llm_loop_empty_monster_specs_blocks_bridge` | ✓ |
| **V6** | `test_execute_tool_unknown_monster_no_combat_state` | ✓ |
| **V7** | `test_handle_combat_trigger_unknown_monster` | ✓ |
| **V8** | `test_llm_loop_start_combat_unknown_strips_fiction` | ✓ |
| **V9** | `test_validate_monster_specs.py` (4 cases) | ✓ |
| APP-028 | `test_combat_failure_narration.py -k start_combat` | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [x] Domain spec changelog **APP-027 done** appended
- [ ] `python tmp/backlog/claim_ticket.py release APP-027 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes (non-blocking)

- **Double validation:** Bridge R2 and engine R1 both call `validate_monster_specs` — defense-in-depth per spec.
- **V4 skipped:** Happy-path `grave-ghoul:1` combat start deferred to APP-030 — spec-allowed.
- **Human playtest:** Stage 7 — unknown monster id → `[Mechanics failed — start_combat: …]` with no combat HUD.
- **Beat content ids:** Non-canon ids in beat regex still fail at R2 — expected; beat engine validation out of scope.
