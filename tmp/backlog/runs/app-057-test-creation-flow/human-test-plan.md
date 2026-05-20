# Human Playtest Plan: APP-057-test-creation-flow

**backlog_ticket:** APP-057  
**Commit:** pending (Stage 7 — use latest commit with APP-057 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** Primary gate is automated pytest from repo root. Manual PyGame replay mirrors the same eight inputs as `app/tests/test_creation_flow.py` to confirm end-to-end UX (roster panel, reception phase) after orchestrator table-shown gating fixes.

## Prerequisites

- [ ] Python 3.11+ with project deps (`pip install -r app/requirements.txt`; pytest available)
- [ ] Shell cwd = **repo root** (`ttTomb-Dust/`) for pytest TCs
- [ ] OpenRouter API key in `app/.env` for manual PyGame play (TC-3)
- [ ] Fresh session: start with `new game` (no Continue from mid-creation save)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`

## Test cases

### TC-1: Primary pytest gate — full creation FSM (maps to ticket AC)

**Goal:** `test_creation_flow.py` drives eight `process_turn` inputs through finalize and asserts non-empty roster.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_creation_flow.py -q` | Exit code **0**; **1 passed** | [ ] |
| 2 | Inspect output | `test_full_creation_apprentice_caster` **PASSED** | [ ] |
| 3 | Confirm test module exists | `app/tests/test_creation_flow.py` present with eight-input `INPUTS` table | [ ] |

**Failure signals:** Exit code non-zero; step assertion failure (stuck on RACE/CLASS/SKILLS); `len(roster) == 0`; import errors for `gm.*` / `tomb_gm.*`.

### TC-2: Regression — app and engine suites remain green (maps to APP-049 dependency AC)

**Goal:** APP-057 changes do not break existing test scaffold or engine creation gating.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests -q` | Exit code **0**; ≥ **2 passed** (smoke + creation flow) | [ ] |
| 2 | From repo root: `python -m pytest play/tomb_gm/tests/test_creation_gating.py -q` | Exit code **0**; all parser gating tests pass | [ ] |
| 3 | After pytest runs: `git status -- play/workspace` | No new/modified files under `play/workspace` from tests | [ ] |

**Failure signals:** Smoke test regression; engine parser failures; SQLite writes to canonical `play/workspace`.

### TC-3: Manual PyGame — Dumpy Apprentice caster path to reception (maps to ticket AC + spec R3/R6)

**Goal:** Same eight inputs as pytest replay in the live client; confirm non-empty roster and Registry reception phase (not pre-delve).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for delver name; creation active | [ ] |
| 3 | Type `Dumpy` and submit | Race table appears in narration (NAME committed) | [ ] |
| 4 | Type `human` and submit | Stats roll + class table in same response; eligible classes include apprentice | [ ] |
| 5 | Type `apprentice` and submit | Skills table appears | [ ] |
| 6 | Type `Lore, Spellcasting, Arcana` and submit | Spell schools table appears | [ ] |
| 7 | Type `pyromancy, ether` and submit | Tier-1 spells table appears | [ ] |
| 8 | Type `ember-touch, static-lash` and submit | Equipment / starting kit summary appears | [ ] |
| 9 | Type `yes` and submit | Creation completes; narration includes **Phase: preparation** | [ ] |
| 10 | Read final narration footer | Contains **Awaiting: RECEPTION_CHOICE**; does **not** contain `PRE_DELVE` or delve phase tags | [ ] |
| 11 | Check left character / roster panel | Shows **Dumpy** with class **apprentice** (non-empty roster) | [ ] |
| 12 | Confirm game state | At Registry reception — player can proceed with reception choices, not dropped into a delve | [ ] |

**Failure signals:** Stuck re-showing race/class table without accepting pick; empty roster after finalize; wrong phase (`PRE_DELVE`, exploration); crash on any creation step; LLM-only tables with no code markdown.

### TC-4: Table-shown gating sanity (maps to spec R6 — optional adversarial)

**Goal:** Player cannot commit race/class before seeing code-owned tables (orchestrator execute guards).

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Start fresh `new game`, enter name `Test` | Race table shown | [ ] |
| 2 | Before table renders, if UI allows rapid submit of `human` on same turn | Error or re-prompt — race not committed without table | [ ] |

**Failure signals:** Race/class silently accepted with empty `*_table_shown`; infinite re-present loop on empty field. **Skip if UI cannot reproduce — pytest guards are authoritative.**

## Acceptance criteria sign-off

| AC | Criterion | Verified by | Pass |
|----|-----------|-------------|------|
| AC-1 | `test_creation_flow.py` exercises creation steps through finalize | TC-1 | [ ] |
| AC-2 | Test asserts engine roster non-empty after finalize | TC-1 (pytest assertions); TC-3 step 11 | [ ] |
| AC-3 | `python -m pytest app/tests/test_creation_flow.py -q` passes | TC-1 | [ ] |
| AC-4 | Depends on APP-049 (`app/tests` package, fixtures) | TC-2 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- Militia spell-skip integration test deferred per spec PM decision — not required for APP-057 sign-off.
- Domain spec checklist + changelog (spec R5) should be ticked on ticket close / release, not in this human gate.
- Follow-ups: APP-059 table column standardization; APP-066+ creation narration/awaiting sync if manual play shows drift between footer and UI badges.
