# Drift Check: APP-067-code-owned-roll-stats-table

**backlog_ticket:** APP-067  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | no | Changelog: added **APP-067 done** row (2026-05-20); behavior § `format_roll_stats_table`, ROLL_STATS orchestration, tests already matched code |
| [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) | no | `roll_attributes` payload shape used by formatter unchanged |
| Run `spec.md` R1–R4 | no | Verified against `creation.py`, `orchestrator.py`, `test_creation_flow.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| `format_roll_stats_table(roll_result)` payload-only | `creation.py` L558–585 | yes |
| Thin `_narrate_flavor` + code tables in `_auto_roll_stats` | `orchestrator.py` L936–954; no `_narrate_only` on roll path | yes |
| HP `10 + STA×5` from `final_attributes` | L582–584; test `**HP:** 60` | yes |
| Chain dedup: ROLL_STATS → `_auto_roll_stats` only | `orchestrator.py` L859–860 | yes |
| `classes_table_shown = True` after roll | L945 | yes |
| Tests: finals + LUC + HP + single class prompt | `test_creation_flow.py` L65–76 | yes |

## Tests run

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

**Result:** 2 passed (0.68s)

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-067 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Optional `test_format_roll_stats_table` unit test not added (spec marks optional).
- Integration test asserts **Final** column and HP, not every intermediate column — sufficient for reported STR mismatch bug.
- Human PyGame playtest not run in drift round; see `spec.md` § Human playtest hints for Stage 7.
