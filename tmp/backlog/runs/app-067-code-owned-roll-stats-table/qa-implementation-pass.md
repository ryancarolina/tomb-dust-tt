# QA PASS: implementation

**Task:** APP-067-code-owned-roll-stats-table  
**backlog_ticket:** APP-067  
**ticket_path:** tmp/backlog/app-067-code-owned-roll-stats-table.md  
**Round:** 1  
**domain_spec_creation:** not_needed (spec already updated in `tmp/app-character-creation-spec.md` draft)

## Verdict

**PASS** — implementation matches ticket AC, run `spec.md` R1–R4, and domain spec § APP-067.

## Automated tests

```text
cd app && python -m pytest tests/test_creation_flow.py -q
.                                                                        [100%]
1 passed in 0.62s
```

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| `format_roll_stats_table(roll_result)` in `creation.py` from payload only | `creation.py` L558–585: columns, life event intro, STR–SPI + LUC rows, HP from `final_attributes["STA"]` | ✓ |
| `_auto_roll_stats()` thin flavor + code tables — no `_narrate_only` stat math | `orchestrator.py` L933–951: `_narrate_flavor` + `format_roll_stats_table` + `format_classes_table`; no `_narrate_only` in path | ✓ |
| Narrated HP matches `10 + STA×5` | `format_roll_stats_table` L582–584; test asserts `**HP:** 60` and `(10 + STA 10 × 5)` | ✓ |
| Test asserts table cells match monkeypatched `roll_result` | `test_creation_flow.py` L5–24 `FIXED_ROLL` shape; L53–65 assertions after `"human"` | ✓ |

## Spec R1–R4 → code

| Spec | Requirement | Evidence | Result |
|------|-------------|----------|--------|
| **R1** | Code-owned attribute table | `format_roll_stats_table`: header row, life event line, per-attr cells from `base_rolls` / `genetic_factors.mod` / `life_event.mods` / `racial_adjustments` / `final_attributes`; LUC dashes | ✓ |
| **R1** | Final from `final_attributes` only (no recompute) | Display uses `final_attributes.get(attr, 0)`; tests assert `| {final} |` from fixture finals | ✓ |
| **R2** | Thin-flavor roll presentation | `_auto_roll_stats` mirrors `_auto_present_skills` pattern | ✓ |
| **R2** | `classes_table_shown = True` after roll | L942 before return | ✓ |
| **R2** | Footer `CLASS_INPUT` via `_compose_creation_narration` | `advance()` → step `CLASS` before compose; `format_creation_status` → `CLASS_INPUT` (L534) | ✓ |
| **R3** | Chain dedup — no duplicate class table | `_chain_after_creation_choice` L859–860: `ROLL_STATS` returns `_auto_roll_stats` only; test `last.count("Pick **one tier-1 class**") == 1` | ✓ |
| **R3** | `_auto_present_class` unchanged for direct CLASS | L706–719: `**Final attributes:**` + `format_classes_table` only | ✓ |
| **R4** | `FIXED_ROLL` production shape | `genetic_factors[attr] = {"roll", "mod"}`; no LUC in `base_rolls`; LUC in `final_attributes` | ✓ |
| **R4** | Post-`human` narration assertions | Table header, life event, finals, LUC row, HP 60, single class prompt, no `**Final attributes:**` on roll path | ✓ |
| **R4** | Optional `test_format_roll_stats_table` | Not added — optional per spec | N/A |

## Independent code traces (pre-impl bugs fixed)

| Prior bug (plan/spec) | Post-impl location | Result |
|-----------------------|-------------------|--------|
| `_auto_roll_stats` used `_narrate_only` + JSON table instructions | L933–951 — code body only | Fixed |
| Chain appended `_auto_present_class` after roll | L859–860 — `_auto_roll_stats` only | Fixed |
| `format_roll_stats_table` missing | `creation.py` L558–585 | Added |

## Scope

Edits confined to ticket **Expected files** under `app/`:

- `app/gm/creation.py` — `format_roll_stats_table`
- `app/gm/orchestrator.py` — `_auto_roll_stats`, chain dedup
- `app/tests/test_creation_flow.py` — `FIXED_ROLL` + APP-067 assertions

Domain spec `tmp/app-character-creation-spec.md` already documents APP-067 behavior (draft changelog). Ticket **Closed** date / spec “done” changelog line remain for release stage.

## Notes (non-blocking)

- Integration test asserts **Final** column and HP, not every intermediate Base/Genetic/Life/Racial cell — sufficient for reported STR off-by-one bug; optional column asserts per domain spec.
- No dedicated `test_format_roll_stats_table` unit test (optional).
- Human playtest (session log parity) not run in this QA round.

## Handoff

**Ready for:** Ticket close (`release --done`), domain spec changelog “APP-067 done” entry, human playtest per run `spec.md` § Human playtest hints.
