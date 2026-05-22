# Dev implementation reflection — APP-027 (ws1)

**backlog_ticket:** APP-027  
**Agent:** Dev  
**Date:** 2026-05-22

## What shipped

- **R1 — `validate_monster_specs`** in `play/tomb_gm/services/simulation/combat.py`; early return in engine `start_combat` (defense-in-depth).
- **R2 — Bridge pre-check** in `app/gm/bridge.py` `start_combat` after session/campaign resolution, before engine call.
- **R3 — Tool args** in `app/gm/tool_args.py`: `_ALLOWED_KEYS`, `_normalize_start_combat`, `validate_tool_args` branch for `start_combat`.
- **R6 — Example hygiene** in `app/gm/tools.py`: `hollow-knight` → `ash-shade` in schema description.
- **Tests** — `play/tomb_gm/tests/test_validate_monster_specs.py` (V9); `app/tests/test_combat_monster_validation.py` (V1–V8, V4 skipped); session bootstrap via `bridge_with_session` / `orchestrator_with_session` (`campaign_new` + `session_start`).

## Verification

```bash
python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -q
# 4 passed

python -m pytest app/tests/test_combat_monster_validation.py -q
# 7 passed, 1 skipped

python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q
# 1 passed
```

## Deviations / notes

- **Stable error string** — `"monster_specs required"` used in R1 and R3 for empty/missing lists (QA adversarial lock).
- **V6 intentionally bypasses R3** — `_execute_tool` direct path exercises bridge R2 only.
- **V4 skipped** — happy `grave-ghoul:1` deferred to APP-030 per plan.
- **Orchestrator wire unchanged** — existing `normalize → validate → _execute_tool` activates R3 without edits.
- **Domain spec changelog** — not updated here (close checklist / `release --done`).

## Risks / follow-ups

- Beat `MONSTER_ID_RE` still lists non-canon ids in content; validation fails at start (expected).
- Double validation (R3 + R2 + optional engine R1) on rare combat starts — acceptable per plan.
