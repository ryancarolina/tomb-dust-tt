# QA PASS: implementation — round 1

**Task:** app-022-hint-enterdungeon-on-failed-setphasedelve  
**backlog_ticket:** APP-022  
**ticket_path:** [tmp/backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md](../../app-022-hint-enterdungeon-on-failed-setphasedelve.md)  
**Round:** 1  
**domain_spec:** synced (§ Failed set_phase(delve) hint in `tmp/app-exploration-delve-spec.md`; ticket AC ticks deferred to `release APP-022 --done`)

## Verdict

**PASS** — Failed `set_phase(delve)` failures inject code-owned `compass_exits` + `enter_dungeon` hints on R1 (tool JSON), R2 (system `TOOL FAILED`), and R3 (player banner at depth 0); negative and partial-success paths match spec; automated tests green.

## Automated tests

```text
cd app && python -m pytest tests/test_exploration_set_phase_delve_hint.py -q
......                                                                   [100%]
6 passed in 2.09s

cd app && python -m pytest tests/test_exploration_site_entry_gate.py -q
.......                                                                  [100%]
7 passed in 2.29s

python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q
..                                                                       [100%]
2 passed in 0.18s
```

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_exploration_set_phase_delve_hint.py` | T1–T6 (hint on fail, player banner, ingress no-hint, success no-hint, partial success no R3, system inject) | ✓ 6 |
| `app/tests/test_exploration_site_entry_gate.py` | APP-024 regression | ✓ 7 |
| `play/tomb_gm/tests/test_site_resolve.py` | Phase FSM unchanged | ✓ 2 |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| On failed `set_phase(delve)`, orchestrator hints `enter_dungeon` + `compass_exits` | `_delve_entry_tool_hint` L115–123; R1 `_last_tool_results["set_phase"]["hint"]` (T1); R2 system append L2483–2488 (T6); R3 player path L2521–2523 (T2) | ✓ |

## Spec R1–R5 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | `"hint"` on failed tool JSON | `_llm_loop` L2467–2473 before `log_tool_call`; `json.dumps(result)` in tool message | ✓ T1 |
| **R2** | System `TOOL FAILED` append | L2483–2491 `Hint: {result['hint']}` | ✓ T6 |
| **R3** | Player banner at depth 0 | L2521–2523 sticky `_delve_entry_hint_this_turn`; combat early return L2517–2518 unchanged | ✓ T2 |
| **R4** | Optional below suffix from `compass_exits` | `_build_delve_entry_hint` L631–642 try/except; suffix in `_delve_entry_tool_hint` L120–122 | ✓ (no dedicated test — non-blocking) |
| **R5** | No hint on wrong phase / success | `_should_delve_entry_hint` L126–131; T3 ingress, T4 success | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/gm/orchestrator.py` | `_delve_entry_tool_hint`, `_should_delve_entry_hint`, `_build_delve_entry_hint`, `_delve_entry_hint_this_turn`, R1–R3 in `_llm_loop` | ✓ |
| `app/tests/test_exploration_set_phase_delve_hint.py` | **new** — 6 tests (T1–T6) | ✓ (untracked `??`) |

No edits to bridge, tools, prompt, FSM, or APP-024 sanitizer — matches plan non-goals.

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| Hint helper at module scope | `_delve_entry_tool_hint`, `_should_delve_entry_hint` after `_SITE_ENTRY_REFUSAL_LINE` | ✓ |
| Sticky turn flag reset at depth 0 | L2402 `_delve_entry_hint_this_turn = None` | ✓ |
| Hint uses `site_address` not `site_id` | Core copy L118 | ✓ |
| TurnTruth bypass appropriate | Code-owned inject; not LLM verify path | ✓ |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Untracked test module** | `app/tests/test_exploration_set_phase_delve_hint.py` must be staged before commit. |
| **Optional R4 test** | No assert for `Below from current cell:` suffix — hub fixture may lack `below`; core hint satisfies AC. |
| **Combat-batch R3 suppress** | Spec Flow E — no dedicated test; existing `_COMBAT_TOOL_NAMES` early return verified in code review only. |
| **Domain spec / ticket close** | Domain spec § + changelog draft present; backlog ticket AC still `[ ]` and Status `in_progress` — update on `release APP-022 --done`. |
| **Orchestrator spec checklist** | Plan §6 notes open-work sync in `tmp/app-llm-orchestrator-spec.md` at close — not impl Expected files. |
| **Human playtest** | Surface “delve now” repro not run in QA; defer to Stage 7 `human-test-plan.md`. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-022 --done` (ticket AC ticks, confirm domain changelog).  
**Stage 7:** Manual playtest — failed `set_phase(delve)` shows hint; recovery via `compass_exits` → `enter_dungeon`.
