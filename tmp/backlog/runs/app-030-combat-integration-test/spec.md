# Spec: APP-030-combat-integration-test

**Status:** draft  
**backlog_ticket:** APP-030  
**ticket_path:** [tmp/backlog/app-030-combat-integration-test.md](../../app-030-combat-integration-test.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-combat-play-spec.md`

## Problem

The app test suite has **strong failure-path coverage** for combat (APP-026 gating, APP-027 monster validation V1–V3/V5–V8, APP-028 narration strip) but **no happy-path integration** that exercises real `GameBridge` + isolated DB + repo `build/` content for `start_combat → combat_attack → combat_end`.

APP-027 **V4** (`test_bridge_valid_grave_ghoul`) was deliberately skipped with reason `APP-030 golden-path combat start with roster`. Research confirms a session-only fixture is **insufficient**: without a roster PC, combat can start with monsters only and `combat_attack` from a PC is impossible — the golden path requires **campaign + session + roster slot 1**.

Engine tests in `play/tomb_gm/tests/test_combat_attack.py` cover engine `combat_attack` but not the **app bridge contract** or optional orchestrator wiring.

**Evidence:** [research-brief.md](./research-brief.md) paths A–D; domain spec § Combat integration golden path (APP-030).

## Goals

- **I1 (required):** Bridge-level golden path — real `GameBridge`, isolated workspace, roster PC, canon `grave-ghoul:1`, PC attack, clean end.
- **Absorb APP-027 V4:** Remove the skipped `test_bridge_valid_grave_ghoul` from `test_combat_monster_validation.py`; happy `start_combat` coverage lives in I1 (start is one step of the full path, not a duplicate-only test).
- **Spec-owned fixture contract:** Shared helpers document roster + turn-advance requirements so future combat tests do not repeat the session-only mistake.

## Non-goals

| Deferred | Note |
|----------|------|
| Orchestrator `_execute_tool` chain (I2) | Optional stretch; exploration guard blocks start+attack in one batch when DB combat active |
| `_dispatch_like_llm_loop` start-only (I3) | V5 already covers empty-spec gate; I1 subsumes V4 happy start |
| `_combat_turn` + mocked `combat_action` + auto-chain | APP-029 / APP-090 territory; not ticket AC |
| Live LLM / narration verify | No `chat_completion` in I1; mechanical integration only |
| Hit/damage assertions | Attack `{ok: true}` sufficient (miss or hit both pass) |
| `bridge.start_combat(seed=…)` API | Optional future stability; I1 uses turn-advance loop |
| Engine golden-path duplication | Engine already covered; app ticket is bridge contract |

## Requirements (summary)

**Authoritative behavior:** domain spec § **Combat integration golden path (APP-030)**.

| Req | Summary |
|-----|---------|
| **R1** | New module `app/tests/test_combat_integration.py` with shared fixture helpers |
| **R2** | Fixture: `make_isolated_workspace` → `GameBridge.init()` → `campaign_new("salt-road")` → `session_start` → `character_create` (roster slot 1) |
| **R3** | **I1** `test_bridge_combat_start_attack_end`: `start_combat(["grave-ghoul:1"])` → assert combat active → advance to PC turn → `combat_attack` → `combat_end` → assert `status.combat` null |
| **R4** | Turn advance: poll `bridge.status()`; while combat active and not PC turn (`is_pc_turn` from `gm.combat_fsm`), call `run_combat_monster_turns()`; cap iterations (e.g. 5 rounds) and fail if PC turn never reached |
| **R5** | Resolve attacker (PC id from combatants/`turn_id`) and monster target from `status["combat"]["combatants"]` — do not hardcode ids except canon monster prefix `grave-ghoul` |
| **R6** | Remove APP-027 V4 skip: delete `test_bridge_valid_grave_ghoul` from `test_combat_monster_validation.py`; update APP-027 test table in domain spec to reference I1 |
| **R7** | Never mutate `play/workspace`; use `app/tests/conftest.py` `bridge` / `isolated_workspace` fixtures |

### I1 step trace (Dev reference)

1. `_ensure_combat_roster_session(bridge)` — salt-road + session + `character_create(name="Sammy", background="militia", skill_ids=[...])`; assert `bridge.status()["combat"] is None`.
2. `start = bridge.start_combat(monster_specs=["grave-ghoul:1"])`.
3. Assert `start["ok"] is True`; `action == "combat_start"`; combat row present; combatants include PC + grave-ghoul.
4. `_advance_to_pc_turn(bridge)` — loop `run_combat_monster_turns()` until `is_pc_turn(status)` or cap.
5. Resolve `attacker_id` (current `turn_id` when PC turn) and `target_id` (monster combatant).
6. `attack = bridge.combat_attack(attacker_id, target_id)` — assert `attack["ok"] is True`; combat still active.
7. `end = bridge.combat_end()` — assert `end["ok"] is True`; `bridge.status().get("combat") is None`.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Integration test: combat start → attack → end | **I1** `test_bridge_combat_start_attack_end` (R3) |
| Spec sync on close | Domain spec § APP-030 + changelog **done** entry |
| APP-027 V4 absorption | R6 — no skipped happy-start duplicate in validation module |

## Test plan

```bash
# Primary (APP-030)
python -m pytest app/tests/test_combat_integration.py -q

# Regression — existing combat app tests must stay green
python -m pytest app/tests/test_combat_monster_validation.py -q
python -m pytest app/tests/test_combat_attack_gating.py -q
python -m pytest app/tests/test_combat_failure_narration.py -q

# Engine reference (unchanged contract)
python -m pytest play/tomb_gm/tests/test_combat_attack.py -q
```

See domain spec test table **I1** (required); **I2–I3** optional stretch documented there only.

## Affected paths

_Must match ticket **Expected files**._

- `app/tests/test_combat_integration.py` — **new** (I1 + shared helpers)
- `app/tests/test_combat_monster_validation.py` — remove V4 skip test (R6)
- `tmp/app-combat-play-spec.md` — § Combat integration golden path (APP-030); APP-027 V4 row update

## Optional stretch (not AC)

| ID | Test | Layer | Notes |
|----|------|-------|-------|
| **I2** | `test_execute_tool_combat_start_attack_end` | `orchestrator_with_session` | Three **separate** `_execute_tool` calls across steps; mock LLM if needed |
| **I3** | `test_dispatch_llm_loop_start_combat_happy` | `_dispatch_like_llm_loop` | Start-only parity; attack/end remain separate |

Dev may land I1 only and close ticket if AC met.

## Pointers

| Artifact | Path |
|----------|------|
| Research | [research-brief.md](./research-brief.md) |
| Domain spec § | [app-combat-play-spec.md § Combat integration golden path](../../../app-combat-play-spec.md) |
| APP-027 V4 deferral | [app-combat-play-spec.md § APP-027 tests](../../../app-combat-play-spec.md) |
| Bridge API | `app/gm/bridge.py` — `start_combat`, `combat_attack`, `combat_end`, `run_combat_monster_turns`, `character_create` |
| Turn helper | `app/gm/combat_fsm.py` — `is_pc_turn` |
| Engine reference fixture | `play/tomb_gm/tests/test_combat_attack.py` — `combat_ctx` (engine-only) |
| Related (separate tickets) | APP-029 auto-chain, APP-090 phased verify, APP-025 registry hub |

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- Start a campaign with a roster PC, trigger or dev-force combat with `grave-ghoul:1` → initiative resolves, PC can attack, combat ends cleanly.
- Confirms production path matches I1 mechanics (no pytest required for sign-off, but I1 is the automated gate).

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | PM draft: I1 bridge golden path, R1–R7, V4 absorption, domain spec § APP-030 |
