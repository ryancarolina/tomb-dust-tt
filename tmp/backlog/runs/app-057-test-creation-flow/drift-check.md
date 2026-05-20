# Drift Check: APP-057-test-creation-flow

**backlog_ticket:** APP-057  
**Verdict:** **PASS** (no spec ↔ code drift)

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| `tmp/app-character-creation-spec.md` | no | Checklist APP-057 marked done; changelog entry added |
| `tmp/backlog/app-057-test-creation-flow.md` | no | AC checked; status `done`; closed 2026-05-20 |
| `tmp/app-master-spec.md` | no | Registry row unchanged; character-creation spec still owns behavior |

## Code vs domain spec

| Area | Spec expectation | Code / test | Match |
|------|------------------|-------------|-------|
| § Table-shown gating | `races_table_shown` / `classes_table_shown` on `CreationState`; serialize; reset on `advance()` | `creation.py:211-212`, `219-222`, `251-252`, `275-276` | yes |
| RACE/CLASS auto-present gates | `is_system_trigger` or `not *_table_shown` | `orchestrator.py:590`, `597` | yes |
| Flags set in `_auto_present_*` | Set True when table shown | `orchestrator.py:682`, `694` | yes |
| Execute guards | Reject RACE/CLASS commit if table not shown | `orchestrator.py:1200-1201`, `1212-1213` | yes |
| NAME→RACE chain | Race table in same narration after name commit | `_chain_after_creation_choice` RACE branch `843-845` | yes |
| ROLL_STATS→CLASS chain | Stats roll + class table same turn after race pick | `_chain_after_creation_choice` `847-850` | yes |
| § Integration test (APP-057) | Eight `process_turn` inputs; Dumpy apprentice path | `test_creation_flow.py` `INPUTS` + assertions | yes |
| Fixtures (R1) | `orchestrator` only; no module-level `Orchestrator` import | Test + `conftest.py:74-91`; conftest unchanged | yes |
| Roll mock (R2) | `monkeypatch` `bridge.roll_attributes`; `apprentice` eligible; `INT >= 8` | `FIXED_ROLL` + lambda `36-40` | yes |
| Post-finalize assertions (R3) | `active` False, `WORLD_INTRO`, roster non-empty, `PLAYER_ACTIONS`, name/class, status tags | Lines `51-62` | yes |
| Out of scope | Militia spell-skip integration test deferred | Not implemented (documented) | yes (intentional) |

## Test gate (re-run at drift)

```text
python -m pytest app/tests/test_creation_flow.py -q
.                                                                        [100%]
1 passed in 0.60s
```

## Ticket close (QA drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog updated
- [ ] `python tmp/backlog/claim_ticket.py release APP-057 --done` — **orchestrator** (not QA drift agent)

## Non-blocking notes (documented, not drift)

- Test does not assert chained table markdown substrings in narration (spec optional).
- `_creation_turn_body` on standalone `ROLL_STATS` does not chain class table — resume edge; canonical 8-input path uses post-RACE chain.
- `tmp/app-logging-qa-spec.md` checklist still lists APP-057 open — logging spec defers behavioral tests to domain owners; no behavior conflict.

## Finding count

**0** drift blockers · **0** majors · **3** non-blocking notes above
