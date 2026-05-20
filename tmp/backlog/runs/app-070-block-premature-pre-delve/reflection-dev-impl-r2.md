# Dev implementation reflection (r2) — APP-070

**backlog_ticket:** APP-070  
**Date:** 2026-05-20  
**Trigger:** QA impl FAIL — AC #3 / T1 test missing

## What changed (r2)

- **`test_skills_turn_rejects_premature_completion_flavor`** added to `app/tests/test_creation_flow.py` (T1 / AC #3).
- **Re-shipped compose + drift** in `app/gm/creation.py` and `app/gm/orchestrator.py`: working tree lacked r1 `sanitize_premature_completion_flavor` / `_compose_creation_narration` wiring (T1 failed until restored).

## Test design

1. Golden path turns 1–4 via `INPUTS[:4]` with `FIXED_ROLL` monkeypatch (same as APP-057 golden path).
2. `monkeypatch.setattr(orchestrator, "_narrate_flavor", …)` returns `BAD_PREMATURE_FLAVOR` containing registered-Delver prose and `[Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE]` per domain spec § APP-070 T1.
3. Turn 5: `Lore, Spellcasting, Arcana` — skills commit must advance FSM to `SPELL_SCHOOLS` while roster stays empty.
4. Assert composed narration excludes `pre_delve`, `reception_choice`, `registered delver` (case-insensitive) and includes code footer `Awaiting: SPELL_SCHOOLS_INPUT`.

## QA gap closed

| AC | r1 | r2 |
|----|----|----|
| #1 compose sanitizer | PASS | PASS (unchanged) |
| #2 drift D1/D2 | PASS | PASS (unchanged) |
| #3 T1 regression test | FAIL (missing) | PASS (test added) |

## Verification

```text
cd app && python -m pytest tests/test_creation_flow.py::test_skills_turn_rejects_premature_completion_flavor -q
cd app && python -m pytest tests/test_creation_flow.py -q
3 passed in 0.89s
```

## Risks / follow-ups

- Drift telemetry for this path is optional per spec when compose strip is total; test does not assert `creation_drift` events.
- Domain spec changelog still for ticket `release --done`.
