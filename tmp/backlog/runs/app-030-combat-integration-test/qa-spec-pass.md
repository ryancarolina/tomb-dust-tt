# QA PASS: spec — round 1

**Task:** app-030-combat-integration-test  
**backlog_ticket:** APP-030  
**ticket_path:** [tmp/backlog/app-030-combat-integration-test.md](../../app-030-combat-integration-test.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-combat-play-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (`test_combat_integration.py`, V4 removal in validation module, domain spec § APP-030)
- [x] Acceptance criteria testable — I1 bridge golden path, V4 absorption, spec sync on close
- [x] Code traces match repo — `bridge.start_combat` / `combat_attack` / `combat_end` / `run_combat_monster_turns` (`bridge.py` L244–324); `is_pc_turn` reads `status["combat"]["turn_id"]` + combatant `kind` (`combat_fsm.py` L62–70); `handle_status` nests combat with `turn_id` (`cmd_core.py` L204–218); V4 skip present (`test_combat_monster_validation.py` L91–94)
- [x] Roster requirement documented — session-only insufficient; `_ensure_combat_roster_session` + step-2 PC-in-combatants assert catches silent roster failure
- [x] Initiative nondeterminism handled — `_advance_to_pc_turn` + `run_combat_monster_turns()` loop with cap (R4); no bridge `seed` required for AC
- [x] Non-goals scoped — no LLM, no hit/damage asserts, no APP-029 auto-chain, no orchestrator I2/I3 for close
- [x] V4 absorption explicit — delete skipped `test_bridge_valid_grave_ghoul`; domain APP-027 V4 row → absorbed I1
- [x] registry_gap false — combat-play domain spec owns § Combat integration golden path (APP-030)
- [x] Domain spec sync — run spec R1–R7 mirrors domain § APP-030 fixture contract, I1 table, tests, regression commands

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress; Expected files complete |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | I1 + V4 removal + changelog process mappable to pytest |
| Code traces | **PASS** | Research paths A–D verified; bridge `combat_attack` does not auto-finalize (direct `combat_attack` service) |
| Expected files ⊆ plan scope | **PASS** | No TICKET-001 gap (contrast APP-027/065) |
| Wire / test design | **PASS** | Bridge-level I1 avoids APP-026 orchestrator gate and exploration batch guard |
| Domain spec sync | **PASS** (draft) | PM draft changelog 2026-05-22; done entry on close per ticket |
| AGENTS.md drift policy | **PASS** | Test-only ticket; behavior already in combat spec; no canon edits |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| **I1** — `test_combat_integration.py` golden path with isolated workspace, roster PC, `grave-ghoul:1` | R1–R5, I1 step trace; domain § I1 table | `pytest app/tests/test_combat_integration.py` | **PASS** |
| **V4 absorption** — remove skipped `test_bridge_valid_grave_ghoul` | R6; domain § APP-027 V4 absorption | validation module minus skip; I1 step 2 covers happy start | **PASS** |
| Domain spec § APP-030 + changelog on close | Ticket § Spec sync; domain § + draft changelog | process | **PASS** (draft stage) |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| V4 skipped awaiting APP-030 | `test_combat_monster_validation.py` L91–94 |
| Session-only fixture exists (no roster) | `_ensure_salt_road_session` L13–17; `bridge_with_session` L20–23 |
| Party spawn needs roster | `start_combat` L261–269 `spawn_roster_combatants` |
| `bridge.combat_attack` is direct service call (no turn advance / finalize) | `bridge.py` L265–279 → `combat_attack` L625–719 returns without `finalize_combat_if_ended` |
| Monster turn advance helper | `run_monster_turns_until_pc_or_end` L834–864 breaks on `turn_kind == "pc"` |
| `is_pc_turn` compatible with `bridge.status()` shape | `cmd_core.py` L211–217 exposes `turn_id`, `combatants` under `combat` |
| Isolated workspace pattern | `conftest.py` L24–36 `bridge` + `make_isolated_workspace` |
| Engine reference (out of AC) | `play/tomb_gm/tests/test_combat_attack.py` — engine-only, seed=3 |

## Adversarial notes (non-blocking)

1. **Fixture fail-fast** — `_ensure_combat_roster_session` should assert `character_create(...)` returns `{ok: true}` (and optionally roster slot 1) before combat start; step-2 PC-in-combatants catches failure but explicit assert aids Dev debug (`bridge.py` L535–538 swallows `roster_set` errors).
2. **`skill_ids=[...]` placeholder** — I1 step trace uses `[...]`; domain fixture table omits skill_ids. Dev should follow minimal pattern from `test_setup_new_game_lifecycle.py` (name + background only) or document one stable skill list — do not require copying engine `novice` skills while spec says `militia`.
3. **Combatant resolution** — R5 forbids hardcoded PC id; Dev should pick PC via `kind == "pc"` and monster via `kind == "monster"` or `id.startswith("grave-ghoul")`, not assume `sammy`.
4. **Turn-cap failure message** — `_advance_to_pc_turn` should `pytest.fail` with a clear message (cap exceeded vs combat ended during monster chain) per PM risk note.
5. **DRY** — New module will duplicate `_ensure_salt_road_session`; acceptable v1; optional follow-up: shared helper in `app/tests/helpers.py` or import from validation module.
6. **Domain § Open work** — L221 still lists APP-030 until ticket release; remove on close (process, not spec blocker).

## Summary

Ticket AC, run `spec.md`, and domain spec § Combat integration golden path (APP-030) are aligned and implementation-ready. Expected files are complete; I1 bridge path is the correct layer (real DB + roster + turn advance) without duplicating APP-026/028 failure coverage or requiring LLM mocks. Proceed to Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
