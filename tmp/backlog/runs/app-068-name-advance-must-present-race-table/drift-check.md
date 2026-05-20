# Drift Check: APP-068-name-advance-must-present-race-table

**backlog_ticket:** APP-068  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | no | Changelog: added **APP-068 done** row (2026-05-20); § NAME→RACE same-turn (R1/R2), § Tests APP-068, table-shown gating already matched code |
| Run `spec.md` R1–R3 | no | Verified against `orchestrator.py`, `creation.py`, `test_creation_flow.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** NAME success → same-turn `_auto_present_race()` (table + `Awaiting: RACE_INPUT`; `races_table_shown = True`) | `_handle_creation_response` NAME ok → `return self._auto_present_race(...)` (`orchestrator.py` L721–724); `_auto_present_race` L681–691 | yes |
| **R2** No bare `"The clerk waits."` at RACE with race unset | NAME path bypasses empty `_chain_after_creation_choice("")`; chain RACE branch L843–845; belt-and-suspenders guard L867–869 | yes |
| **R3** Integration test: name → race header + footer | `test_name_advance_presents_race_table` L71–82; turn-2 assertions in `test_full_creation_apprentice_caster` L50–55 | yes |
| `format_races_table()` intro + header | `creation.py` L544–555 | yes |

## Tests run

```bash
cd app; python -m pytest tests/test_creation_flow.py -q
```

**Result:** 2 passed (0.76s)

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-068 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Implementation uses **direct** `_auto_present_race` on NAME commit (spec R2 allows direct path or chain branch — both valid).
- Redundant RACE fallthrough guard at L867–869 is unreachable after L843–845; harmless, not spec drift.
- Human PyGame playtest not run in drift round; see run `spec.md` § Human playtest hints for Stage 7.
