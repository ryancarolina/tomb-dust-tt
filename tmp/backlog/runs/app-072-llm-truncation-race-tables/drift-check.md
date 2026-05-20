# Drift Check: APP-072-llm-truncation-race-tables

**backlog_ticket:** APP-072  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | was yes (missing § APP-072) | **Synced:** § RACE flavor must not duplicate code table, `strip_flavor_race_table`, § Tests APP-072, APP-059 RACE catalog note, changelog **APP-072 done** (2026-05-20) |
| Run `spec.md` R1–R6 | no | Verified against `creation.py`, `orchestrator.py`, `test_creation_tables.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** RACE body = `err + format_races_table()` only | `_auto_present_race` L775–787: `body = err + format_races_table()`; body never sanitized | yes |
| **R2** RACE flavor prompt forbids listing races / tables | Instruction L780–782; global `_creation_flavor_messages` L621–622 | yes |
| **R3** Block-scoped strip on flavor before compose | `creation.py` `strip_flavor_race_table` L548–568; `_compose_creation_narration` L555–556 | yes |
| **R4** Line fallback if `\| Race \|` remains | L566: `[ln for ln in keep if "\| Race \|" not in ln]` | yes |
| **R5** Exactly one `\| Race \| Adjustments \|` in composed narration | `test_race_narration_single_table_header` | yes |
| **R6** Re-prompt path uses same compose hook | Invalid race turn in integration test; `count == 1` | yes |
| Token budget unchanged (`120`) | `_CREATION_FLAVOR_MAX_TOKENS = 120` L75; integration uses `finish_reason="length"` | yes |

## Tests run

```bash
cd app; python -m pytest tests/test_creation_tables.py tests/test_creation_flow.py -q
```

**Result:** 7 passed (1.47s)

| Module | Tests | Result |
|--------|-------|--------|
| `test_creation_tables.py` | 2 (APP-072 unit + integration) | ✓ |
| `test_creation_flow.py` | 5 (regression) | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-072 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- **Pre-drift gap:** Domain spec had no APP-072 behavior section despite green impl tests — resolved in this drift round.
- **Compose order (flavor path):** `strip_llm_status_tags` → `strip_flavor_race_table` (APP-072) → `_sanitize_creation_flavor` (APP-069) → `sanitize_premature_completion_flavor` (APP-070 when active).
- **Optional items not in code (non-blocking):** `test_format_races_table_contract`; R6 debug log on strip — both deferred per run `spec.md`.
- **APP-059:** Description column still in `format_races_table()` cells; catalog target documented; APP-072 tests use `\| Race \| Adjustments \|` fingerprint.
- Human PyGame playtest not run in drift round; see run `spec.md` § Human playtest hints for Stage 7.
