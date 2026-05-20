# QA PASS: plan

**Task:** APP-067-code-owned-roll-stats-table  
**backlog_ticket:** APP-067  
**ticket_path:** tmp/backlog/app-067-code-owned-roll-stats-table.md  
**Round:** 1  
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress` (`tmp/backlog/app-067-code-owned-roll-stats-table.md`)
- [x] Ticket domain spec matches spec/plan updates (`tmp/app-character-creation-spec.md` — § `format_roll_stats_table`, ROLL_STATS orchestration, APP-067 tests)
- [x] Acceptance criteria testable (plan tasks 1–4 map to run `spec.md` R1–R4 and ticket AC; task 5 = changelog on close)
- [x] Code traces match repo (independent traces below)
- [x] AGENTS.md / canon compliance (HP `10 + STA×5` from `final_attributes`; display uses authoritative Final column, not recomputed sum)
- [x] Tests/commands listed (`pytest tests/test_creation_flow.py -q`; optional `test_creation_tables.py`; manual greps in plan § Tests)
- [x] Plan files ⊆ ticket Expected files (exact four paths; bridge/system_prompt correctly out of scope)
- [x] registry_gap N/A at plan stage (spec `registry_gap: false` confirmed in qa-spec-pass)

## Independent code traces (plan accuracy)

| Plan claim | Verified location | Result |
|------------|-------------------|--------|
| `_auto_roll_stats` uses `_narrate_only` + JSON table instructions | `orchestrator.py` L924–956 | Confirmed — `context` embeds `json.dumps(result)` and column headers; returns `_narrate_only(messages)` |
| Chain duplicates class table after roll | `orchestrator.py` L846–850 | Confirmed — after `_auto_roll_stats`, `step == "CLASS"` triggers `_auto_present_class` append |
| RACE commit → chain on `ROLL_STATS` | `orchestrator.py` L735–738, L1280–1286 | Confirmed — `_execute_creation_choice("RACE")` calls `advance()` → `ROLL_STATS`, then `_chain_after_creation_choice("")` |
| Reference thin-flavor pattern | `orchestrator.py` L869–880 (`_auto_present_skills`) | Confirmed — `_narrate_flavor` + code body + `_compose_creation_narration` |
| `_compose_creation_narration` adds step footer | `orchestrator.py` L507–524 | Confirmed — `format_creation_status(self.creation)` when step is `CLASS` → `CLASS_INPUT` |
| `classes_table_shown` CLASS guard | `orchestrator.py` L1211–1213 | Confirmed — commit blocked without flag |
| `advance()` resets `classes_table_shown` on CLASS | `creation.py` L221–222 | Confirmed — plan sets flag **after** `advance()` in `_auto_roll_stats` (correct order) |
| Production `roll_attributes` payload | `bridge.py` L118–163 | Confirmed — `genetic_factors[attr] = {"roll", "mod"}`; `base_rolls` STR–SPI only; `final_attributes` includes LUC |
| `format_roll_stats_table` missing | `creation.py` L544–574 | Confirmed — only `format_races_table` / `format_classes_table` today |
| `FIXED_ROLL` fixture drift | `test_creation_flow.py` L5–21 | Confirmed — flat `genetic_factors`, `LUC` in `base_rolls`; plan update required |
| Mock flavor substring | `conftest.py` L54 | Confirmed — `content="Test narration."` supports plan assertion |
| `test_creation_tables.py` absent | repo glob | Confirmed — optional per ticket; plan prefers integration assertions |

## Spec / ticket / plan alignment

| Ticket AC | Plan task | Spec R |
|-----------|-----------|--------|
| `format_roll_stats_table` in `creation.py` | §1 | R1 |
| `_auto_roll_stats` thin flavor + code tables | §2 | R2 |
| HP matches `10 + STA×5` | §1 step 5, §2 | R1, R2 |
| Test cells match monkeypatched roll | §4 | R4 |

Flows A–D in `plan.md` match domain spec § Table-shown gating / ROLL_STATS orchestration / chain dedup. Chain dedup (Flow D) is required to fix the live duplicate-class path traced at L846–850.

## Notes

- `tmp/.active-ticket.json` may still claim APP-066 — impl stage should `claim_ticket.py APP-067` before `app/` edits (qa-spec-pass note; non-blocking for plan content).
- Plan does not spell out `CreationState.advance()` resetting `classes_table_shown` on CLASS entry; implementation order in §2 (set flag after `advance()`) is still correct.
- Intermediate column assertions (Base/Genetic/Life/Racial) are optional per domain spec; plan Final-column + HP + single class-table checks satisfy ticket bug (wrong finals).
