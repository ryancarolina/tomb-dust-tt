# QA Report: Implementation

**Task:** APP-068-name-advance-must-present-race-table  
**backlog_ticket:** APP-068  
**Round:** 1  
**Verdict:** FAIL

## Summary

APP-068 acceptance criteria (R1–R3) are **implemented and green in pytest**, but the working tree **fails the scope gate**: `app/gm/creation.py` is modified with APP-067 work (`format_roll_stats_table`) and is **not** listed in APP-068 Expected files. Orchestrator and test diffs also contain APP-066/APP-067 batch changes beyond plan §1–2; those paths are allowed files but blur ticket isolation.

**Blocker count:** 1

---

## Tests run

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_creation_flow.py -q` | **pass** — 2 passed in 0.68s |
| `cd app && python -m pytest tests/test_creation_flow.py::test_name_advance_presents_race_table -q` | **pass** |
| `cd app && python -m pytest tests/test_creation_flow.py::test_full_creation_apprentice_caster -q` | **pass** |

---

## Ticket AC → code + tests

| Ticket AC | Spec | Implementation | Test |
|-----------|------|----------------|------|
| After NAME, same turn returns `_auto_present_race()` body (code table + footer) | R1 | `_handle_creation_response` NAME success → `return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")` (`orchestrator.py` L734–737). `_auto_present_race` sets `races_table_shown = True`, body = `format_races_table()`, footer via `_compose_creation_narration` → `Awaiting: RACE_INPUT` (L694–704, L534). | `test_name_advance_presents_race_table` L99–105; `test_full_creation_apprentice_caster` L59–64 |
| Never bare `"The clerk waits."` when `step == RACE` and race unset | R2 | NAME path bypasses `_chain_after_creation_choice("")` (no empty-prior fallthrough). Pre-default guard: `if self.creation.step == "RACE" and not self.creation.race:` → `_auto_present_race` (L876–878). | Both tests assert `narration.strip() != "The clerk waits."` |
| Integration test: name → race header + `Awaiting: RACE_INPUT` | R3 | — | `test_name_advance_presents_race_table` (dedicated); turn-2 assertions in `test_full_creation_apprentice_caster` |

### R1 / R2 / R3 detail

| Req | Status | Evidence |
|-----|--------|----------|
| **R1** Same-turn code race table + footer; `races_table_shown` True | **PASS** | Direct `_auto_present_race` on NAME commit; assertions on `Pick **one race**`, `\| Race \| Adjustments \| Description \|`, `Awaiting: RACE_INPUT`, `races_table_shown is True` |
| **R2** No clerk-waits at RACE with race unset | **PASS** (behavior) | Observed bug path (`_chain_after_creation_choice("")` after NAME) removed. Fallthrough guard is belt-and-suspenders (likely unreachable when `step == "RACE"` at chain entry — see qa-plan-pass note). |
| **R3** Regression test | **PASS** | New focused test + extended full-flow turn 2; pytest green |

---

## Scope gate

**Ticket Expected files:** `app/gm/orchestrator.py`, `app/tests/test_creation_flow.py`, `tmp/app-character-creation-spec.md`

| Path | In Expected files? | In `git diff HEAD`? | Notes |
|------|-------------------|---------------------|-------|
| `app/gm/orchestrator.py` | yes | yes | APP-068: L734–737, L876–878. **Also** APP-066 drift (`_expected_creation_awaiting_label`), APP-067 `_auto_roll_stats` refactor — not in APP-068 plan §1–2 |
| `app/tests/test_creation_flow.py` | yes | yes | APP-068: L59–64, L95–106. **Also** APP-067 human-turn + drift assertions, `FIXED_ROLL` shape |
| `tmp/app-character-creation-spec.md` | yes | yes | APP-068 § draft present; APP-066/067 sections mixed; no APP-068 **done** changelog (deferred to release per plan — OK at impl QA) |
| **`app/gm/creation.py`** | **no** | **yes** | **`format_roll_stats_table` (APP-067)** — **scope violation** |

---

## Findings

### IMPL-001 — blocker (scope)

- **Location:** `app/gm/creation.py` (+58 lines `format_roll_stats_table`)
- **Issue:** File modified in working tree but **not** in APP-068 Expected files. Change is APP-067 (`format_roll_stats_table`), not APP-068 NAME→RACE fix.
- **Spec/plan/ticket reference:** Ticket Expected files; plan § Files touched (orchestrator + tests only for impl); workstreams WS1 “Out of scope: `creation.py`”.
- **Suggested fix:** Revert or re-attribute `creation.py` to APP-067 ticket/claim; keep APP-068 diff limited to orchestrator NAME handler + chain guard + tests. If batch landing is intentional, add `app/gm/creation.py` to APP-068 Expected files **only if** PM approves scope expansion (not recommended — belongs to APP-067).

### IMPL-002 — note (non-blocking)

- **Location:** `orchestrator.py` L876–878
- **Issue:** RACE fallthrough guard is redundant when `self.creation.step == "RACE"` at function entry (L856–858 already returns `_auto_present_race`). Harmless; does not fail R2 given Task 1 fix.
- **Suggested fix:** Optional collapse in follow-up; not required for AC.

### IMPL-003 — note (non-blocking)

- **Location:** `tmp/app-character-creation-spec.md`
- **Issue:** APP-068 AC checkboxes / done changelog not updated (plan task 4 on `release --done`).
- **Suggested fix:** Stage 6 drift check + ticket close.

---

## Verdict rationale

**Behavior:** PASS — fixes match plan §1–2, R1–R3 satisfied, pytest green.  
**Scope:** FAIL — `app/gm/creation.py` edited outside Expected files.  
**Overall:** **FAIL** (1 blocker) until scope is cleaned or ticket Expected files are formally expanded.
