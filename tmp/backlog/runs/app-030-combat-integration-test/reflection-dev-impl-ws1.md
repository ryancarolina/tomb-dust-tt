# Dev implementation reflection — APP-030 (ws1)

**backlog_ticket:** APP-030  
**Agent:** Dev  
**Date:** 2026-05-22

## What shipped

- **I1 — `app/tests/test_combat_integration.py`** — new module with:
  - `_ensure_combat_roster_session` — `campaign_new` + `session_start` + `character_create(name="Sammy", background="militia")` + pre-combat guard (`status.combat is None`).
  - `_advance_to_pc_turn` — polls `is_pc_turn`, calls `run_combat_monster_turns` until PC turn or explicit `pytest.fail` (max 5 iterations).
  - `test_bridge_combat_start_attack_end` — full golden path: `start_combat(["grave-ghoul:1"])` → advance to PC turn → `combat_attack` → assert combat still active → `combat_end` → assert `combat is None`.
- **V4 absorption** — deleted skipped `test_bridge_valid_grave_ghoul` from `app/tests/test_combat_monster_validation.py` (happy start now covered by I1).

No production code changes; bridge combat API already satisfied AC.

## Verification

```bash
python -m pytest app/tests/test_combat_integration.py -q
# 1 passed

python -m pytest app/tests/test_combat_monster_validation.py -q
# 7 passed (no skips)

python -m pytest app/tests/test_combat_attack_gating.py -q
# 9 passed

python -m pytest app/tests/test_combat_failure_narration.py -q
# 11 passed

python -m pytest play/tomb_gm/tests/test_combat_attack.py -q
# 2 passed
```

## Deviations / notes

- **Attacker/target resolution** — after `_advance_to_pc_turn`, combatants are re-read from returned status (not stale pre-advance list) before picking `attacker_id` / `target_id`; still avoids hardcoding `sammy`.
- **Post-attack guard** — explicit assert `bridge.status().get("combat") is not None` before `combat_end` (plan optional strengthen).
- **Domain spec changelog** — not updated here (close checklist / `release --done` per plan Task 3).

## Risks / follow-ups

- Initiative is seed-driven; `_advance_to_pc_turn` loop handles monster-first order — not flaky in local run (0.31s).
- I2/I3 orchestrator chains and APP-029 auto-chain remain deferred per spec non-goals.
- Optional: extract shared `_ensure_salt_road_session` + roster helper to `app/tests/helpers.py` if more integration tests land.
