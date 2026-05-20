# QA PASS: spec

**Task:** APP-072-llm-truncation-race-tables  
**backlog_ticket:** APP-072  
**ticket_path:** tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; APP-072 sections updated in existing domain spec)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md` — § RACE flavor must not duplicate code table, § Creation tables RACE row, § Tests APP-072)
- [x] Acceptance criteria testable (T1–T6 + `test_creation_tables.py` contract; human playtest hints for live `finish_reason: length`)
- [x] Code traces match repo (`orchestrator.py` `_auto_present_race` ~694–704, `_compose_creation_narration` ~520–537, `_narrate_flavor` ~558–575, `_CREATION_FLAVOR_MAX_TOKENS = 120`; `creation.py` `format_races_table` ~544–555, `strip_llm_status_tags` ~532–535; `conftest.py` stub `"Test narration."` / `finish_reason="stop"`)
- [x] AGENTS.md / canon compliance (app-only; no `build/` mechanics drift)
- [x] Tests/commands listed (`python -m pytest app/tests/test_creation_tables.py -q`, regression `test_creation_flow.py`)
- [x] registry_gap matches reality (`false` — Character creation row in `app-master-spec.md` owns `creation.py` + orchestrator creation branch)
- [x] If registry_gap true: N/A — no § Proposed domain spec in run `spec.md` (correct)

## Ticket AC coverage

| Ticket AC | Spec / domain mapping |
|-----------|------------------------|
| RACE body only `format_races_table()` | **T1 / R1**; `_auto_present_race` `body = err + format_races_table()` (live code); domain § RACE flavor T1 |
| Flavor ≤2 sentences, no markdown tables (prompt + post-check) | **T2 / R2** — existing `_creation_flavor_messages` “1–2 short sentences” + “Do NOT include markdown tables”; **T3–T4 / R3–R4** post-check via `strip_flavor_race_table` before compose |
| Strip `\| Race \|` / token budget → prose only | **T3–T4 / R3–R4** block-scoped strip + line fallback; `_CREATION_FLAVOR_MAX_TOKENS = 120` unchanged; truncated-table failure mode covered; non-goals document no retry on `finish_reason: length` |
| No duplicate race tables in one turn | **T5 / R5** — `count("\| Race \| Adjustments \|") == 1`; domain § Tests APP-072 |
| Mock LLM embedded table test | `test_race_narration_single_table_header` + `test_strip_flavor_race_table_unit`; override default stub documented |
| Spec sync APP-059 (on close) | Domain § Creation tables RACE row (Race + Adjustments target); APP-059 formatter change explicitly non-goal |

## Scope gate

Run `spec.md` **Expected files** ⊆ ticket **Expected files**:

- `app/gm/orchestrator.py` ✓
- `app/gm/creation.py` ✓
- `app/tests/test_creation_tables.py` ✓ (new — not in repo yet; ticket-authorized)
- `tmp/app-character-creation-spec.md` ✓

Non-goals exclude APP-059 formatter change, cross-step table strip, `finish_reason` retry, dead `get_step_prompt` removal (APP-074), history omission (APP-069) — no scope creep.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-072 valid, `in_progress`, domain spec matches |
| registry_gap | **PASS** | false — existing `app-character-creation-spec.md` |
| Drift policy | **PASS** | Ticket AC ↔ run spec ↔ domain T1–T6 aligned |
| Testability — duplicate table regression | **PASS** | Forced bad-LLM stub + unit sanitizer locked; default mock cannot regress |
| Testability — re-prompt (T6) | **PASS** | Same `_auto_present_race` path; human playtest hint; helper unit test covers sanitizer |
| Scope vs APP-059/069/074 | **PASS** | Boundaries in `spec.md` Non-goals + domain § Ticket boundaries |
| Code traces | **PASS** | Research-brief paths A/B/C match live orchestrator |
| Template completeness | **PASS** | Human playtest hints present (NAME→RACE, optional live length, re-prompt) |
| AGENTS.md / canon | **PASS** | App-only |

## Notes (non-blocking — Dev plan)

- **Sanitizer call site:** Run spec allows `_compose_creation_narration` *or* `_auto_present_race`; Dev plan should pick **one** (recommend compose, after `strip_llm_status_tags`, mirroring APP-070 compose pattern) to avoid double-strip or missed chain paths.
- **Stable fingerprint:** Tests use `\| Race \| Adjustments \|` (not full Description header) so APP-059 column removal does not rewrite APP-072 assertions — documented in spec + domain.
- **Optional R6 logging** and **optional** `test_format_races_table_contract` — not required to close ticket.
- Session log evidence (`session-2026-05-20.jsonl`) is gitignored — human playtest + stub tests are the verification path.

**Verdict:** PASS — ready for Stage 3 (Dev plan + QA plan).
