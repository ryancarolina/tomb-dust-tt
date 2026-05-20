# QA PASS: spec

**Task:** APP-057-test-creation-flow
**backlog_ticket:** APP-057
**ticket_path:** tmp/backlog/app-057-test-creation-flow.md
**Round:** 2
**domain_spec_creation:** not_needed (registry_gap false; domain spec updated in r2)
**Finding count:** 0
**Verdict:** PASS

## Round 1 finding remediation

| ID | Status | Evidence |
|----|--------|----------|
| SPEC-001 | **Resolved** | R6 + § Table-shown gating: `races_table_shown` / `classes_table_shown`; `_creation_turn_body` gates on `not *_table_shown` (not empty `race` / `chosen_class`); flags set in `_auto_present_*`; serialize in `to_dict` / `from_dict` |
| SPEC-002 | **Resolved** | R6 + R3 turn table: `_chain_after_creation_choice` handlers for `RACE` and post-roll `CLASS`; turn 2 chains race table; turn 3 chains roll + class table in one narration |
| SCOPE-001 | **Resolved** | Non-goals no longer exclude orchestrator/creation; PM decision + ticket Expected files + spec R6 / affected paths align |
| SPEC-003 | **Resolved** | R1: `orchestrator` fixture only (transitive `mock_openrouter_client`); forbid module-level `Orchestrator` import; domain spec § Integration test matches |

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (Expected files, Notes scope r2)
- [x] Acceptance criteria testable (8-input path + pytest gate + post-finalize table)
- [x] AGENTS.md / canon compliance (spell/skill IDs unchanged; no parallel rules)
- [x] Tests/commands listed (`test_creation_flow.py`, related pytest commands)
- [x] registry_gap false; domain spec § Integration test + § Table-shown gating present

## Independent code trace — R6 minimal / correct

Reviewed current `app/gm/orchestrator.py` and `app/gm/creation.py` against R6 (implementation not yet landed; spec matches repo gaps).

| R6 item | Current code | Proposed fix assessment |
|---------|--------------|-------------------------|
| RACE/CLASS auto-present | Lines 590–603 gate on `not self.creation.race` / `not self.creation.chosen_class` | **Correct:** mirror SKILLS (`skills_table_shown` at 604, 862) — two bool fields + gate swap only |
| Flag persistence | `CreationState` has `skills_table_shown` only (208–267) | **Minimal:** add `races_table_shown`, `classes_table_shown` to dataclass + `to_dict` / `from_dict`; optional `advance()` reset into `RACE`/`CLASS` per SKILLS pattern |
| NAME→RACE chain | `_chain_after_creation_choice` (839–858) has no `RACE` branch | **Correct:** one branch calling `_auto_present_race` after NAME commit |
| ROLL_STATS→CLASS chain | `ROLL_STATS` branch calls `_auto_roll_stats` (915–947) which `advance()`s to `CLASS` but returns `_narrate_only` without `format_classes_table` | **Correct:** extend `ROLL_STATS` chain to append `_auto_present_class` when `step == CLASS` (reuses existing 692–704 body); avoids rewriting LLM stats prompt |
| Execute guards | SKILLS guard at 1212–1213 only | **Correct:** add symmetric guards for RACE/CLASS before commit |
| SKILLS+ chain | Already chains SKILLS→schools→spells→equipment (843–854) | Unchanged; R3 turns 4–8 remain valid |

**Achievability:** After R6, the 8-input Apprentice path reaches `_auto_finalize` with roster assertions as specified (round 1 runtime stall at RACE is addressed by design).

## Gates (summary)

| Gate | Result |
|------|--------|
| Ticket ↔ spec AC | PASS |
| Domain spec drift (draft) | PASS — r2 table-shown + integration contract |
| Inputs 5–8 / parsers | PASS (unchanged from round 1) |
| Post-finalize assertion shape | PASS |
| R6 scope minimality | PASS |
| Adversarial | PASS — 0 new findings |

## Notes

- `research-brief.md` still describes pre-fix RACE routing (“if no race yet”); run artifact only — **domain spec + spec.md** are authoritative for Dev.
- Resume mid-creation with old saves lacking new flags is edge-case; APP-010 owns resume — not a spec blocker for APP-057.

## Handoff

**Ready for:** Dev plan (round 1) — implement R1–R6 per spec and ticket Expected files.
