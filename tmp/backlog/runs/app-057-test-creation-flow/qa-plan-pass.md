# QA PASS: plan

**Task:** APP-057-test-creation-flow
**backlog_ticket:** APP-057
**ticket_path:** tmp/backlog/app-057-test-creation-flow.md
**Round:** 1
**domain_spec_creation:** not_needed
**Finding count:** 0
**Verdict:** PASS

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (Expected files, scope r2 notes)
- [x] Acceptance criteria testable — R1–R6 mapped to concrete edits and assertions
- [x] Code traces match repo — line refs verified against current `creation.py` / `orchestrator.py`
- [x] AGENTS.md / canon compliance — no new spell/skill IDs; d20 canon untouched
- [x] Tests/commands listed — primary + regression pytest gates
- [x] Plan files ⊆ ticket Expected files — four paths only; conftest no-change default
- [x] registry_gap false — domain spec owns behavior; R5 deferred to ticket close

## Spec ↔ plan coverage (R1–R6)

| Requirement | Plan section | Assessment |
|-------------|--------------|------------|
| R1 fixtures / import discipline | §3.1 | `orchestrator` fixture only; no module-level `Orchestrator`; no duplicated mock |
| R2 deterministic roll mock | §3.2–3.3 | `FIXED_ROLL` + `monkeypatch` on `orchestrator.bridge.roll_attributes`; race echo via lambda |
| R3 8-input test + post-finalize asserts | §3.4–3.5 | Turn table matches spec/domain spec; roster + `awaiting` + footer strings covered |
| R4 conftest | §4 | Explicit no-change unless duplication |
| R5 domain spec sync | §5 | Correctly out of impl PR |
| R6 table-shown + chain + execute guards | §1–2 | Mirrors SKILLS pattern; NAME→RACE branch; ROLL_STATS→CLASS nested chain |

## Independent code trace — plan correctness

Reviewed current code at cited symbols; plan edits are minimal and sufficient for the canonical Apprentice path.

| Area | Current code (verified) | Plan fix | Trace result |
|------|-------------------------|----------|--------------|
| RACE/CLASS auto-present gates | `orchestrator.py:590–603` gates on `not race` / `not chosen_class` | Swap to `not *_table_shown` | Unblocks turn 3 commit after chained table on turn 2 |
| Flag fields | `creation.py:208–267` — only SKILLS/SCHOOLS/SPELLS flags | Add `races_table_shown`, `classes_table_shown` + serialize + `advance()` reset into RACE/CLASS | Matches domain spec § Table-shown gating |
| Flag set on present | `_auto_present_skills` sets flag at L862; race/class do not | Set at start of `_auto_present_race` / `_auto_present_class` | Symmetric with SKILLS |
| NAME→RACE chain | `_chain_after_creation_choice` L839–858 — no RACE branch | Insert before ROLL_STATS | Turn 2 ends on `RACE` with table in same narration |
| ROLL_STATS→CLASS chain | L841–842 calls `_auto_roll_stats` only; L915–947 advances to CLASS, returns `_narrate_only` | Extend ROLL_STATS branch to append `_auto_present_class` when `step == CLASS` | Turn 3 ends on `CLASS` with stats + `format_classes_table()` |
| Execute guards | SKILLS guard L1212–1213; RACE/CLASS unguarded | Mirror guards before parse | Prevents commit without table shown |
| Post-finalize asserts | `_auto_finalize` L1023–1048; `cmd_core.py` L160–184 roster/`awaiting` | Assert `display_name`, `base_class`, `PLAYER_ACTIONS`, footer substrings | Field names confirmed in engine payload |

**8-input walkthrough (planned behavior):** After R6, NAME→RACE chain (turn 2) sets `races_table_shown=True`; turn 3 `"human"` routes to `_handle_creation_response` (not re-present); RACE commit chains roll + class table; turns 4–8 reuse existing SKILLS→FINALIZE chains unchanged. Finalize sets `active=False`, `step=WORLD_INTRO`, populates roster via `character_create` + `roster_set` (`bridge.py:509–514`).

## Gates (summary)

| Gate | Result |
|------|--------|
| Ticket ↔ plan files | PASS |
| Spec R1–R6 completeness | PASS |
| Line-level trace accuracy | PASS |
| Achievability of integration test | PASS |
| Scope minimality (no drive-by refactors) | PASS |
| Adversarial | PASS — 0 blockers |

## Notes (non-blocking)

- ROLL_STATS→CLASS is implemented by nesting `_auto_present_class` inside the ROLL_STATS chain branch rather than a standalone `step == "CLASS"` branch — spec-valid, avoids double-present; Dev reflection documents tradeoff.
- `advance()` reset clears only table-shown flags for RACE/CLASS (not `race`/`chosen_class`) — correct; resume edge cases remain APP-010.
- Plan §2.5 guard placement wording (“before parsing ~L1190”) is slightly imprecise — guards belong at the top of each `elif step == "RACE"|"CLASS"` block; implementation intent is clear.
- Pytest not run (plan phase; no implementation yet). Impl QA must run gates in §Tests.

## Handoff

**Ready for:** Dev workstreams → parallel impl (WS1 orchestrator/creation, WS2 test module)
