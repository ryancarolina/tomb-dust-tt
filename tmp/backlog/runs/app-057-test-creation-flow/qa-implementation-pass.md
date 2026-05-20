# QA PASS: Implementation

**Task:** APP-057-test-creation-flow  
**backlog_ticket:** APP-057  
**Verdict:** **PASS**  
**Tests run:**

```text
python -m pytest app/tests/test_creation_flow.py -q
.                                                                        [100%]
1 passed in 0.60s

python -m pytest app/tests -q
..                                                                       [100%]
2 passed in 0.72s

python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
............                                                             [100%]
12 passed in 0.03s
```

**Diff scope reviewed:** `app/gm/creation.py`, `app/gm/orchestrator.py`, `app/tests/test_creation_flow.py`  
**Ticket AC:** all four items satisfied  
**Spec R1–R6:** R1–R4 and R6 satisfied in code; R5 deferred to ticket close (not impl blocker)

---

## Ticket acceptance criteria

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `test_creation_flow.py` exercises creation through finalize | PASS | Eight `process_turn` inputs in `INPUTS`; final step `WORLD_INTRO` after equipment confirm chains `_auto_finalize` |
| Non-empty roster after finalize | PASS | `assert len(status["roster"]) >= 1` (`test_creation_flow.py:55`) |
| `pytest app/tests/test_creation_flow.py -q` passes | PASS | 1 passed, exit 0 |
| APP-049 dependency (app/tests package) | PASS | Uses `orchestrator` fixture from `conftest.py`; isolated workspace; no `play/workspace` writes |

---

## Spec R1 — Module and fixtures

| Criterion | Result | Evidence |
|-----------|--------|----------|
| New `app/tests/test_creation_flow.py` | PASS | Present |
| `orchestrator` fixture only | PASS | Sole pytest fixture param on `test_full_creation_apprentice_caster` |
| No module-level `Orchestrator` import | PASS | Grep: no `from gm.orchestrator` / `import Orchestrator` in module |
| No duplicated `mock_openrouter_client` | PASS | Transitive via `conftest.py` `orchestrator` → `mock_openrouter_client` |
| No duplication of `test_creation_gating.py` | PASS | Integration via `process_turn`; no engine parser imports |

---

## Spec R2 — Deterministic roll mock

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `monkeypatch` on `orchestrator.bridge.roll_attributes` | PASS | `test_creation_flow.py:36-40` |
| `FIXED_ROLL` with `ok: True`, `apprentice` in `eligible_classes`, `INT >= 8` | PASS | `INT: 12` in `final_attributes`; six tier-1 classes listed |
| Race echoed in lambda | PASS | `{**FIXED_ROLL, "race": race}` |

---

## Spec R3 — `test_full_creation_apprentice_caster`

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Eight inputs in spec order | PASS | `INPUTS` matches domain spec turn table |
| Per-turn `creation.step` assertions | PASS | Loop asserts expected step after each input |
| `creation.active` False, `step == WORLD_INTRO` | PASS | Lines 51-52 |
| `len(roster) >= 1`, `awaiting == PLAYER_ACTIONS` | PASS | Lines 55-56 |
| `display_name == "Dumpy"`, `base_class == "apprentice"` | PASS | Lines 57-58 |
| Final narration: `Awaiting: RECEPTION_CHOICE`, `Phase: preparation`, no `PRE_DELVE` | PASS | Lines 60-62 |

**8-input walkthrough (code-backed):**

| # | Input | Expected step | Verified mechanism |
|---|--------|---------------|-------------------|
| 1 | `new game` | `NAME` | `setup_new_game` → `_creation_turn` |
| 2 | `Dumpy` | `RACE` | NAME commit → `_chain_after_creation_choice` RACE branch (`orchestrator.py:843-845`) |
| 3 | `human` | `CLASS` | RACE commit → ROLL_STATS chain: `_auto_roll_stats` + `_auto_present_class` (`847-850`) |
| 4–8 | apprentice → yes | SKILLS → … → `WORLD_INTRO` | Existing SKILLS/schools/spells/equipment/FINALIZE chains unchanged |

---

## Spec R4 — conftest.py

| Criterion | Result | Evidence |
|-----------|--------|----------|
| No conftest change unless shared fixture needed | PASS | `conftest.py` unchanged; `FIXED_ROLL` module-local |

---

## Spec R5 — Domain spec sync

| Criterion | Result | Notes |
|-----------|--------|-------|
| Checklist + changelog on ticket close | **Deferred** | `tmp/app-character-creation-spec.md` still has `[ ] Integration test` — correct for **release** step, not implementation QA failure |

---

## Spec R6 — Orchestrator / creation fixes

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `races_table_shown` / `classes_table_shown` on `CreationState` | PASS | `creation.py:211-212` |
| Serialized `to_dict` / `from_dict` | PASS | `creation.py:251-252`, `275-276` |
| Reset on `advance()` into `RACE` / `CLASS` | PASS | `creation.py:219-222` |
| RACE gate: `not races_table_shown` (not `not race`) | PASS | `orchestrator.py:590` — old `not self.creation.race` pattern removed |
| CLASS gate: `not classes_table_shown` | PASS | `orchestrator.py:597` |
| Flags set in `_auto_present_race` / `_auto_present_class` | PASS | `682`, `694` |
| NAME→RACE chain | PASS | `_chain_after_creation_choice` `step == "RACE"` (`843-845`) |
| ROLL_STATS→CLASS chain (stats + class table same turn) | PASS | `847-850`: roll then `_auto_present_class` when `step == CLASS` |
| Execute guards for RACE/CLASS | PASS | `1200-1201`, `1212-1213` |
| 8-input path reaches finalize + roster | PASS | Integration test green |

---

## Adversarial checks

| Check | Result | Notes |
|-------|--------|-------|
| Commit without table shown (RACE/CLASS) | PASS | Guards return error before field assignment |
| Re-present loop on empty `race` / `chosen_class` | PASS | Gating uses `*_table_shown` only |
| `play/workspace` pollution | PASS | Tests use `isolated_workspace` via APP-049 fixtures |
| Regression: engine creation gating | PASS | 12/12 `test_creation_gating.py` |
| Regression: app smoke | PASS | 2/2 `app/tests` |

**Non-blocking (documented, not AC):**

- `_creation_turn_body` on `ROLL_STATS` alone calls `_auto_roll_stats` without class chain (`579-580`) — resume/mid-FSM edge; APP-010 owns resume; canonical 8-input path uses chain after RACE commit.
- Test does not assert chained table substrings in narration (spec optional).
- `_auto_roll_stats` still uses LLM `_narrate_only` for stats flavor; class table is code-owned via `_auto_present_class` in chain — matches spec R6 “or equivalent.”

---

## Finding count

**0** blockers · **0** majors · **2** non-blocking notes above

---

## Handoff

**Ready for:** Stage 6 drift check, domain spec changelog + ticket `done`, `claim_ticket.py release APP-057 --done`  
**Escalate human if:** Product requires militia spell-skip integration test before close (deferred per spec PM decision)
