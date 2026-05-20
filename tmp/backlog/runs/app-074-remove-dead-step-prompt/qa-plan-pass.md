# QA PASS: plan

**Task:** APP-074-remove-dead-step-prompt  
**backlog_ticket:** APP-074  
**ticket_path:** tmp/backlog/app-074-remove-dead-get-step-prompt.md  
**Round:** 1  
**Reviewer role:** QA (adversarial, code-level)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches plan (`tmp/app-character-creation-spec.md`)
- [x] Acceptance criteria testable via plan steps (delete, grep, pytest trio, changelog on close)
- [x] Code traces match repo (independent verification below)
- [x] AGENTS.md / canon compliance (app-only deletion; no `build/` edits)
- [x] Tests/commands listed and files exist
- [x] Plan files ⊆ ticket Expected files
- [x] registry_gap N/A at plan stage (spec PASS: `not_needed`)

## Independent code traces (round 1)

| Claim | Repo evidence | Result |
|-------|---------------|--------|
| Dead symbol at 742–833 | `app/gm/creation.py:742` `def get_step_prompt` through `:833` `return ""`; next symbol `parse_player_race` at `:836` | **Match** |
| Zero callers under `app/` | `rg "get_step_prompt" app/` → single hit (`creation.py:742` definition only) | **Match** |
| No test references | `rg` under `app/tests/` → no matches | **Match** |
| No `play/` references | `rg` under `play/` → no matches | **Match** |
| Orchestrator live path | `orchestrator.py` imports `format_*`, `parse_player_*`; no `get_step_prompt`; `_creation_turn` → `_creation_turn_body` → `_auto_present_*` / `_handle_creation_response` | **Match** |
| Combat contrast | `orchestrator.py` imports `get_combat_step_prompt` from `combat_fsm` — live, out of scope | **Match** |
| RACE body unchanged | `_auto_present_race` uses `format_races_table()` (`orchestrator.py` ~786); dead prompt duplicates `RACES` inline table (`creation.py` 755–770) | **Match** |

## Plan ↔ spec ↔ ticket mapping

| Ticket AC | Plan coverage |
|-----------|---------------|
| Remove `get_step_prompt()` | Task 1 — delete `creation.py:742–833` (~92 lines) |
| Grep `app/` confirms no references | Task 2 — `rg "get_step_prompt" app/` expect zero matches |
| Spec: prompts in `_auto_present_*` / `format_*` only | Unchanged live-path table + Task 4 changelog finalize; domain § Step content sources already drafted |

| Spec requirement | Plan coverage |
|------------------|---------------|
| R1 delete + grep | Tasks 1–2 |
| R2 live path unchanged | Regression contract table; no `orchestrator.py` edit |
| R3 domain spec sync | Task 4 on `release --done` |

## Scope gate

**Plan files ⊆ ticket Expected files:**

| Path | In plan | In ticket Expected files |
|------|---------|--------------------------|
| `app/gm/creation.py` | Delete `get_step_prompt` | ✓ |
| `tmp/app-character-creation-spec.md` | Changelog finalize on close | ✓ |

**Explicit out of scope (no creep):** `orchestrator.py`, `system_prompt.py`, `tools.py`, `app/tests/*` (unless stray grep in Expected files), APP-059 formatter change, optional negative grep test, APP-059 backlog prose (close hygiene only).

## Test plan adequacy

| Command | File exists | Plan role |
|---------|-------------|-----------|
| `python -m pytest app/tests/test_creation_flow.py -q` | ✓ | Post-delete regression |
| `python -m pytest app/tests/test_creation_tables.py -q` | ✓ | Post-delete regression |
| `python -m pytest play/tomb_gm/tests/test_creation_gating.py -q` | ✓ | Post-delete regression |
| `rg "get_step_prompt" app/` | — | AC verification |

No new tests required — aligned with ticket AC and `qa-spec-pass.md`.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-074 `in_progress`, domain spec linked |
| Plan ⊆ Expected files | **PASS** | Exactly two paths; no unauthorized edits |
| Code-path accuracy | **PASS** | Line range, symbols, import block verified independently |
| Spec alignment | **PASS** | Deletion-only chore; R1–R3 mapped |
| Test commands | **PASS** | Trio + grep sufficient for chore |
| Scope / non-goals | **PASS** | Matches `spec.md` and `qa-spec-pass.md` |
| Drift close contract | **PASS** | Task 4 blocks `release --done` until changelog + grep clean |

## Notes (non-blocking — impl / close)

- **Pre-delete helper name:** Plan cites “validate_skills / related”; immediate predecessor is `validate_skill_picks` (`creation.py:726–739`). Deletion boundary still correct.
- **Domain spec ahead of code:** § Step content sources states “has no” `get_step_prompt` while function still exists — intentional PM draft; impl must finalize changelog per Task 4 before `release --done`.
- **Ticket Evidence line numbers:** Backlog cites ~639–728; live function is **742–833** — plan/spec/research correct; optional ticket prose fix on close.
- **APP-059 backlog:** `app-059-standardize-creation-table-outputs.md` still cites `get_step_prompt` as RACE source — plan defers to close hygiene (not impl-stage files).
- **Human smoke:** Stage 7 NAME→RACE smoke documented in plan — QA playtest agent expands later.

**Verdict:** **PASS** — ready for Stage 4 (workstreams + implementation).
