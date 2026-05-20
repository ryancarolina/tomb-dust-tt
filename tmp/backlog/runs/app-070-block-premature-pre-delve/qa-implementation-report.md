# QA FAIL: Implementation

**Task:** APP-070-block-premature-pre-delve  
**backlog_ticket:** APP-070  
**Round:** 1  
**Tests run:** `cd app && python -m pytest tests/test_creation_flow.py -q` → **4 passed** in 1.18s  
**Targeted T1:** `tests/test_creation_flow.py::test_skills_turn_rejects_premature_completion_flavor` → **not found** (pytest exit 4)

**Diff scope reviewed:** `app/gm/creation.py`, `app/gm/orchestrator.py`, `app/tests/test_creation_flow.py`, `tmp/app-character-creation-spec.md` (spec-only; test contract documented, test not implemented)

## Verdict

**FAIL** — P0 compose + drift code landed; **ticket AC #3 / spec T1 regression test missing**. Dev reflection claims T1 shipped and 7 tests green; repo has 4 tests and no `test_skills_turn_rejects_premature_completion_flavor`.

---

## Ticket AC mapping

| # | Acceptance criterion | Status | Evidence |
|---|----------------------|--------|----------|
| 1 | No `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” in player narration until finalize + non-empty roster | **PASS (code)** | `sanitize_premature_completion_flavor` in `creation.py`; wired in `_compose_creation_narration` when `creation.active or roster_len == 0`; flavor-only (body/footer untouched). Golden path turn 8 still allows legitimate `RECEPTION_CHOICE` + `Phase: preparation` via `footer=` after roster populated (`test_creation_flow.py` L122–124). |
| 2 | `_check_creation_drift` flags `premature_exploration_phase` for PRE_DELVE / preparation reception when `roster_len == 0` | **PASS** | `orchestrator.py`: `_PRE_DELVE_PHASES`, D1b `RECEPTION_CHOICE` + active, D1c `preparation` + active + `step != WORLD_INTRO`; D2 `premature_completion_copy` on registration phrases. |
| 3 | Regression test: mock bad LLM PRE_DELVE prose at SKILLS; FSM/roster/UI unchanged | **FAIL** | No `test_skills_turn_rejects_premature_completion_flavor`. `test_creation_flow.py` diff adds APP-069 tests + golden-path step asserts only. |

---

## Code review (AC 1–2)

### Compose sanitizer (C1–C5)

| Req | Result |
|-----|--------|
| C1 — apply when `active` or `roster_len == 0` | Match (`orchestrator.py` ~593–603) |
| C2 — flavor only, not body/footer | Match; gate skips when `not active` and `roster_len > 0` post-finalize |
| C3 — blank on PRE_DELVE, RECEPTION_CHOICE, registered-delver phrases | Match (`_PREMATURE_FLAVOR_MARKERS`) |
| C4 — `Phase: preparation` in flavor when `active` and `step != WORLD_INTRO` | Match |
| C5 — re-run `strip_llm_status_tags` when sanitizer mutates | Match |

**Note:** `roster_len` is passed into `sanitize_premature_completion_flavor` but unused inside the helper (gate is caller-only); harmless.

### Drift (D1–D2)

| Req | Result |
|-----|--------|
| D1a — `pre_delve` / `pre-delve` when empty roster | Match |
| D1b — `RECEPTION_CHOICE` while `creation.active` | Match |
| D1c — `preparation` while active and not `WORLD_INTRO` | Match |
| D2 — `premature_completion_copy` | Shipped (optional per spec) |

**Telemetry caveat:** If compose strips all leak markers, `parse_narration_status_line` may not see phase/awaiting and drift early-returns — acceptable per plan/qa-plan notes; T1 was meant to lock player-visible behavior.

### Regression guards

| Guard | Result |
|-------|--------|
| `test_full_creation_apprentice_caster` | PASS (4-test suite) |
| APP-009 `_auto_finalize` roster gate | Not modified in APP-070 diff hunk |
| Batch overlap (APP-069/072 in same files) | Present (`_narrate_creation_flavor`, `strip_flavor_race_table`, APP-069 tests); does not satisfy APP-070 T1 |

---

## Required fix (Dev)

Add `test_skills_turn_rejects_premature_completion_flavor` per domain spec § **APP-070: premature completion flavor at SKILLS (T1)** and `plan.md` §3.1:

1. Golden path through turn 4 (`apprentice` → `SKILLS`).
2. Monkeypatch `_narrate_flavor` (or narrow stub) to return bad completion prose before turn 5 (`Lore, Spellcasting, Arcana`).
3. Assert: `creation.step == SPELL_SCHOOLS`, `len(roster) == 0`, no `PRE_DELVE` / `RECEPTION_CHOICE` / `registered Delver` in composed narration, `Awaiting: SPELL_SCHOOLS_INPUT` in footer.

Re-run:

```bash
cd app && python -m pytest tests/test_creation_flow.py::test_skills_turn_rejects_premature_completion_flavor -q
cd app && python -m pytest tests/test_creation_flow.py -q
```

---

## Gates

| Gate | Result |
|------|--------|
| Expected files only | PASS (no out-of-ticket paths in APP-070 core) |
| AC 1–2 implementation | PASS |
| AC 3 / T1 test | **FAIL** |
| Spec ↔ code (T1) | **DRIFT** — spec documents test; code lacks it |
| Full `test_creation_flow.py` | PASS (4/4) — insufficient for APP-070 close |

**Return to Dev** — implement T1, then re-run QA impl (Stage 5).
