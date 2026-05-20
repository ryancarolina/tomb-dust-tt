# QA PASS: Implementation

**Task:** APP-068-name-advance-must-present-race-table  
**backlog_ticket:** APP-068  
**Round:** 2  
**Verdict:** **PASS**

## Summary

IMPL-001 scope blocker from Round 1 is **cleared**: `app/gm/creation.py` has no diff vs `HEAD`. `orchestrator.py` and `test_creation_flow.py` diffs contain **only** APP-068 plan tasks 1–3. Pytest green; spec R1–R3 and ticket acceptance criteria satisfied.

**Blocker count:** 0

---

## Scope gate (Round 2)

| Check | Result |
|-------|--------|
| `git diff HEAD -- app/gm/creation.py` empty | **PASS** |
| `orchestrator.py` diff — APP-068 only (NAME direct `_auto_present_race`; chain RACE fallthrough guard) | **PASS** |
| `test_creation_flow.py` diff — APP-068 only (turn-2 assertions + `test_name_advance_presents_race_table`) | **PASS** |

No APP-066/APP-067 hunks in orchestrator or test diffs (contrast Round 1).

---

## Tests run

| Command | Result |
|---------|--------|
| `cd app; python -m pytest tests/test_creation_flow.py -q` | **pass** — 2 passed in 0.74s |

---

## Ticket AC → code + tests

| Ticket AC | Spec | Implementation | Test |
|-----------|------|----------------|------|
| After NAME, same turn returns `_auto_present_race()` body (code table + footer) | R1 | `_handle_creation_response` NAME success → `return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")` (`orchestrator.py` L724). `_auto_present_race` sets `races_table_shown = True`, body = `format_races_table()`, footer via `_compose_creation_narration` → `Awaiting: RACE_INPUT`. | `test_name_advance_presents_race_table` L71–82; `test_full_creation_apprentice_caster` L50–55 |
| Never bare `"The clerk waits."` when `step == RACE` and race unset | R2 | NAME path bypasses `_chain_after_creation_choice("")`. Pre-default guard: `if self.creation.step == "RACE" and not self.creation.race:` → `_auto_present_race` (L867–869). | Both tests assert `narration.strip() != "The clerk waits."` |
| Integration test: name → race header + `Awaiting: RACE_INPUT` | R3 | — | `test_name_advance_presents_race_table`; turn-2 assertions in `test_full_creation_apprentice_caster` |

### R1 / R2 / R3

| Req | Status | Evidence |
|-----|--------|----------|
| **R1** Same-turn code race table + footer; `races_table_shown` True | **PASS** | Direct `_auto_present_race` on NAME commit; assertions on table intro, header, `Awaiting: RACE_INPUT`, `races_table_shown is True` |
| **R2** No clerk-waits at RACE with race unset | **PASS** | Observed failure path removed; fallthrough guard is belt-and-suspenders (non-blocking note) |
| **R3** Regression test | **PASS** | Focused test + full-flow turn 2; pytest green |

---

## Round 1 follow-up

| Finding | Round 2 status |
|---------|----------------|
| IMPL-001 — `creation.py` out of scope | **Resolved** — diff empty |
| IMPL-002 — redundant RACE fallthrough guard | Note only — harmless |
| IMPL-003 — spec done changelog / ticket checkboxes | Deferred to `release --done` (plan task 4) — **non-blocking** for impl QA |

---

## Handoff

**Ready for:** Drift check + `release APP-068 --done`, domain spec changelog, human playtest per `spec.md` § Human playtest hints.
