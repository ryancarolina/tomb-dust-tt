# Drift Check: APP-022-hint-enterdungeon-on-failed-setphasedelve

**backlog_ticket:** APP-022  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) | no | § Failed set_phase(delve) hint (APP-022), checklist `[x]`, changelog **APP-022 done** (2026-05-22) match `orchestrator.py` + tests |
| Run [`spec.md`](./spec.md) R1–R5 | no | Verified against `_delve_entry_tool_hint`, `_should_delve_entry_hint`, `_build_delve_entry_hint`, `_llm_loop` R1–R3 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Exploration domain row unchanged; no registry gap |
| [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) | yes (open-work list) | **Defer:** APP-022 still listed under open work L609 — orchestrator should remove on `release APP-022 --done` (not in ticket Expected files) |

## Code ↔ domain spec (APP-022 scope)

| Requirement | Code | Match |
|-------------|------|-------|
| Trigger: failed `set_phase` + `phase=delve` | `_should_delve_entry_hint` L130–135 | yes |
| Core hint names `compass_exits` + `enter_dungeon(site_address)` | `_delve_entry_tool_hint` L119–127 | yes |
| Optional below suffix from live `compass_exits` | `_build_delve_entry_hint` L664–675 | yes |
| **R1** `"hint"` on failed tool JSON | `_llm_loop` L2577–2583, tool message L2603–2607 | yes |
| **R2** System `TOOL FAILED` append | L2593–2602 `Hint: {result['hint']}` | yes |
| **R3** Player banner at depth 0 | Sticky `_delve_entry_hint_this_turn` L2511 reset, L2580–2581 set, L2631–2633 insert | yes |
| **R5** No hint on wrong phase / success | T3 ingress, T4 success | yes |
| Partial success: R1 ok, no R3 player banner | T5 — loop continues, no `[Mechanics failed` | yes |
| Combat batch suppress R3 | `failed_names & _COMBAT_TOOL_NAMES` L2627–2628 unchanged | yes |
| Compose order with APP-024 | prefix → hint → `_compose_exploration_narration` L2629–2633 | yes |

## Ticket AC ↔ verification

| Ticket AC | Result |
|-----------|--------|
| On failed `set_phase(delve)`, orchestrator hints `enter_dungeon` + `compass_exits` | ✓ R1 tool JSON (T1), R2 system inject (T6), R3 player banner (T2) |

## Run spec R1–R5 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | `"hint"` on failed tool JSON | ✓ T1 |
| **R2** | System `TOOL FAILED` append | ✓ T6 |
| **R3** | Player banner at depth 0 | ✓ T2 |
| **R4** | Optional below suffix | ✓ code; no dedicated test (non-blocking) |
| **R5** | No hint on wrong phase / success | ✓ T3, T4 |

## Tests run

```bash
cd app; python -m pytest tests/test_exploration_set_phase_delve_hint.py tests/test_exploration_site_entry_gate.py -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q
```

**Result:** 13 app passed (4.16s); 2 engine passed (0.17s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_exploration_set_phase_delve_hint.py` | T1–T6 | ✓ 6 |
| `app/tests/test_exploration_site_entry_gate.py` | APP-024 regression | ✓ 7 |
| `play/tomb_gm/tests/test_site_resolve.py` | Phase FSM unchanged | ✓ 2 |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [x] Domain spec checklist + changelog — APP-022 done row present
- [ ] `python tmp/backlog/claim_ticket.py release APP-022 --done` — **orchestrator** (QA drift: not run)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § Failed set_phase(delve) hint matched implementation before drift; ticket AC and Status were the only lagging artifacts.
- **Untracked test module:** `app/tests/test_exploration_set_phase_delve_hint.py` must be staged at Stage 7 commit.
- **Orchestrator spec open-work list:** remove APP-022 link when orchestrator runs release (ancillary hygiene).
- **Human playtest:** Surface “delve now” / failed `set_phase(delve)` recovery deferred to Stage 7 `human-test-plan.md`.
