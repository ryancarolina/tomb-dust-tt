# Drift Check: APP-069-creation-narration-match-fsm

**backlog_ticket:** APP-069  
**Verdict:** PASS (after spec sync)

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | **yes → remediated** | Domain spec lacked § Flavor must reflect committed FSM state, § Gated-step body contract, § Tests APP-069 Phase 1–2, and changelog row — added during this drift round; now matches code |
| Run [`spec.md`](./spec.md) F1–F4, Phase 2 body contract | no | Verified against `orchestrator.py`, `creation.py`, `test_creation_flow.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **F1** Roll flavor cites committed race | `_auto_roll_stats` L1028–1034: `race_display_title(self.creation.race)` in instruction | yes |
| **F2** ROLL_STATS presentation context | `_narrate_creation_flavor(..., presenting_step="ROLL_STATS")` | yes |
| **F3** Option A flavor sanitizer | `_sanitize_creation_flavor` L595–604; wired in `_compose_creation_narration` L557 | yes |
| **F4** Committed-state block in flavor msgs | `_committed_state_flavor_block` L582–593; appended in `_creation_flavor_messages` L607–608 | yes |
| **F5** No history while `creation.active` | `_creation_flavor_messages` L609: `history_block = [] if self.creation.active else ...` | yes |
| Gated-step bodies code-only (SKILLS→EQUIPMENT) | `_auto_present_skills|schools|spells|equipment` use `format_*` + `_compose_creation_narration`; `_creation_turn_body` L698–726 | yes |
| Phase 2 golden-path keywords turns 4–7 | `test_creation_flow.py` L159–217 | yes |
| Phase 1 Undead/Human repro test | `test_roll_stats_flavor_reflects_committed_race` L329–367 | yes |
| Phase 1 committed class in flavor prompt | `test_creation_flavor_messages_committed_class` L373–421 | yes |
| Stretch `narrated_step_mismatch` | Not in `app/` (deferred per ticket) | yes (intentional deferral) |
| PRE_DELVE before finalize | `test_full_creation_apprentice_caster` L247; mid-FSM → APP-070 `test_skills_turn_rejects_premature_completion_flavor` | yes |

## Tests run

```bash
cd app; python -m pytest tests/test_creation_flow.py tests/test_creation_tables.py -q
```

**Result:** 7 passed (1.41s)

| Module | Count |
|--------|-------|
| `test_creation_flow.py` | 5 |
| `test_creation_tables.py` | 2 |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-069 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Initial drift: implementation QA reported spec updated, but domain spec had no APP-069 sections until this drift round — **remediated** (no code changes required).
- `_auto_present_skills|schools|spells|equipment` call `_narrate_flavor` directly; sanitizer still runs at `_compose_creation_narration` — matches spec compose pipeline.
- `_creation_llm_loop` dead path unchanged (historical wrong-step bodies not live).
- Human PyGame playtest (Rick/Undead session repro) not run in drift round; see run `spec.md` for Stage 7 hints.
