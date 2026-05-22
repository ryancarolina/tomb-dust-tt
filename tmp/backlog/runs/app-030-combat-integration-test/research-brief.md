# Research Brief: APP-030-combat-integration-test

**Date:** 2026-05-22  
**Question:** What app-layer test patterns exist for combat today, what does a real `start_combat → attack → end` golden path require (fixtures, turn order, bridge vs orchestrator), and how should APP-030 relate to APP-027 V4 and APP-028/026 failure tests?

**backlog_ticket:** APP-030  
**ticket_path:** tmp/backlog/app-030-combat-integration-test.md  
**domain_spec:** tmp/app-combat-play-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) owns combat FSM, orchestrator combat branch, bridge combat wrappers, and already lists **APP-030** under open work with engine test commands and the note “End-to-end golden path may extend APP-030.” [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Combat play** maps to that spec and `play/tomb_gm/services/simulation/combat.py`. Ticket **Expected files** (`app/tests/`) ⊆ combat spec ownership — no new `tmp/app-*-spec.md` required.

## Summary

The app suite has **strong unit and failure-path coverage** for combat (APP-026 gating, APP-028 narration strip, APP-027 monster validation V1–V8) but **no happy-path integration** that exercises real bridge + DB + `build/` content for `start_combat → combat_attack → combat_end`. APP-027 deliberately **skipped V4** (`test_bridge_valid_grave_ghoul`) with reason `APP-030 golden-path combat start with roster` — that skip is the natural anchor for this ticket.

A live probe on `GameBridge` + `make_isolated_workspace` confirms the golden path works when the fixture includes **campaign, session, and a roster PC** (`character_create` → slot 1). `start_combat(monster_specs=["grave-ghoul:1"])` succeeds; initiative often opens on a **monster** turn (`grave-ghoul-1`), so the test must call `run_combat_monster_turns()` (or loop) before `combat_attack`. Attack returns `{ok: true}` (miss or hit); `combat_end()` clears `status.combat`. Without a roster PC, combat can start with **monsters only** — `combat_attack` from a PC is impossible; V4’s “valid session” wording is insufficient without roster setup.

**Recommended fix (Dev):** Add `app/tests/test_combat_integration.py` (name per PM) with a shared fixture mirroring `test_combat_monster_validation._ensure_salt_road_session` plus `character_create` (same skills/class pattern as `play/tomb_gm/tests/test_combat_attack.py`). Primary test **I1**: bridge-level golden path; optionally **I2**: `_dispatch_like_llm_loop` tool chain (APP-080/027 pattern) for exploration `_execute_tool` wiring; optionally **I3**: `_combat_turn` + mocked `combat_action` (APP-028/029). Remove or relocate APP-027 V4 skip into I1. Update combat spec § Tests + changelog on close. **Do not** require live LLM for AC — mock `chat_completion` if orchestrator paths are included.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Test fixtures | `app/tests/conftest.py`, `app/tests/helpers.py` | `bridge`, `orchestrator`, `isolated_workspace`; never `play/workspace` |
| APP-027 validation | `app/tests/test_combat_monster_validation.py` | V1–V3 failure; **V4 skipped** for APP-030; V5–V8 orchestrator/LLM failure |
| APP-028 failure narration | `app/tests/test_combat_failure_narration.py` | Mocks bridge tools; `_mock_chat_completion_once`, `exploration_ready` |
| APP-026 attack gating | `app/tests/test_combat_attack_gating.py` | Mocks `status` / bridge; G6 calls real `_execute_tool` with mocked `combat_attack` |
| Tool dispatch helper | `app/tests/test_tool_args.py` | `_dispatch_like_llm_loop` — normalize/validate → `_execute_tool` |
| Bridge combat API | `app/gm/bridge.py` | `start_combat`, `combat_attack`, `combat_end`, `combat_action`, `run_combat_monster_turns`, `character_create` |
| Orchestrator combat | `app/gm/orchestrator.py` | `_combat_turn`, `_combat_llm_loop_inner`, `_combat_auto_chain`, `_execute_tool`, `_execute_combat_action` |
| Combat FSM helpers | `app/gm/combat_fsm.py` | `is_pc_turn`, `CombatState` |
| Engine combat (reference) | `play/tomb_gm/services/simulation/combat.py` | `start_combat`, `combat_attack`, `end_combat`, `validate_monster_specs` |
| Engine golden fixture | `play/tomb_gm/tests/test_combat_attack.py` | `combat_ctx`: DB + roster + `start_combat` + `combat_attack` — **not** app bridge |
| Domain spec | `tmp/app-combat-play-spec.md` | Open APP-030; V4 deferral documented |
| Related batch | APP-025 (registry hub integration), APP-029 (auto-chain) | Separate tickets; APP-030 need not assert auto-chain for AC |

## Code-path traces

### A — Bridge golden path (recommended primary — unblocks V4)

1. **Fixture:** `make_isolated_workspace` → `GameBridge.init()` → `campaign_new("salt-road")` → `session_start` → `character_create(...)` (roster slot 1).
2. **Start:** `bridge.start_combat(monster_specs=["grave-ghoul:1"])` — R2 `validate_monster_specs` + engine `start_combat` (`bridge.py` ~244–261).
3. **Assert:** `result["ok"] is True`; `bridge.status()["combat"]` non-null; `action` / combatants include `grave-ghoul` and PC id (e.g. `sammy`).
4. **Turn prep:** If `turn_kind != "pc"`, `bridge.run_combat_monster_turns()` until `is_pc_turn(status)` or cap iterations (initiative is seed-driven; bridge does not expose `seed` today).
5. **Attack:** Resolve `turn_id` (PC) and monster target from `status["combat"]["combatants"]` → `bridge.combat_attack(attacker_id, target_id)` — engine `combat_attack` (`bridge.py` ~265–279).
6. **Assert:** `attack["ok"] is True` (hit optional); combat row still active.
7. **End:** `bridge.combat_end()` → `end_combat` sets `active = 0` (`combat.py` ~967–995).
8. **Assert:** `end["ok"] is True`; `bridge.status().get("combat") is None`.

### B — Exploration orchestrator: `_execute_tool` chain (optional integration)

1. **Entry:** `_dispatch_like_llm_loop(orch, "start_combat", {"monster_specs": ["grave-ghoul:1"]})` (`test_tool_args.py` ~33–39) — same validate-before-execute as `_llm_loop`.
2. **Attack:** `_execute_tool("combat_attack", {attacker_id, target_id})` — APP-026 `_gate_pc_attack` then `bridge.combat_attack` (`orchestrator.py` ~2686–2689). Requires combat active and attacker in initiative (G6 pattern uses mocked status; integration uses **real** status after start).
3. **End:** `_execute_tool("combat_end", {})` → `bridge.combat_end()` (~2690–2691).
4. **Note:** During active combat, `_execute_tool("combat_attack")` is **blocked** if `combat.active` or `_combat_active_in_db()` — error `"During combat only combat_action is available"`. So a single exploration turn cannot call `start_combat` then `combat_attack` in one batch after combat is active. Integration must use **separate** dispatches (or set `combat.active = False` only when not in DB — unrealistic). **PM decision:** AC “start → attack → end” at orchestrator layer likely means **sequential `_execute_tool` calls across steps**, not one LLM tool batch.

### C — Combat FSM: `_combat_turn` + `combat_action` (optional; APP-029 adjacent)

1. **Entry:** `process_turn` → `_combat_turn` when `combat.active` or `_combat_active_in_db()` or `awaiting == COMBAT_TURN` (`orchestrator.py` ~1131–1133).
2. **PC action:** `_combat_llm_loop_inner` → `_execute_combat_action("ATTACK", ...)` → `bridge.combat_action` → `resolve_pc_action_and_advance` (`orchestrator.py` ~2454–2477).
3. **Auto-chain:** On success, `_combat_auto_chain()` → `run_combat_monster_turns()` until PC or end (APP-029).
4. **End:** Exploration tool `combat_end` only in `_llm_loop` when **not** in combat guard; ending during FSM may require bridge `combat_end` directly or engine end from defeated monsters — **not** the same as exploration `combat_end` tool during `combat.active`. Ticket AC “end” maps cleanly to **bridge `combat_end`** / exploration `_execute_tool("combat_end")` when not in inner combat-only guard.

### D — APP-028 / APP-027 patterns (contrast, not duplicate)

| Pattern | Module | What it proves |
|---------|--------|----------------|
| All-failed strip | `test_combat_failure_narration.py` T3–T7 | **Mocked** `{ok: false}`; no real combat row |
| Unknown monster | `test_combat_monster_validation.py` V1, V8 | Real bridge; **failure** only |
| Attack gating | `test_combat_attack_gating.py` G1–G8 | Mocked status/bridge; not golden path |
| V4 skip | `test_combat_monster_validation.py` | Happy `start_combat` deferred to APP-030 |

## Existing specs & docs

- **Ticket AC:** Integration test: combat start → attack → end.
- **Combat spec:** Lists pytest modules for APP-026/027/028; “End-to-end golden path may extend APP-030”; V4 explicitly skipped for this ticket.
- **APP-027 close:** V4 `bridge.start_combat(grave-ghoul:1)` with valid session — implement as APP-030 I1 + roster.
- **APP-028 (done):** Failure paths; T4 `combat_attack` all-failed uses mock — orthogonal to happy path.
- **Engine:** `play/tomb_gm/tests/test_combat_attack.py` already covers engine `combat_attack` — app ticket still needed for **GameBridge** contract and optional orchestrator wiring.

## Tests & commands

```bash
# Existing combat app tests (no happy-path integration)
python -m pytest app/tests/test_combat_monster_validation.py -q
python -m pytest app/tests/test_combat_failure_narration.py -q
python -m pytest app/tests/test_combat_attack_gating.py -q

# Engine reference (bridge should stay consistent)
python -m pytest play/tomb_gm/tests/test_combat_attack.py -q

# After APP-030 implementation
python -m pytest app/tests/test_combat_integration.py -q
```

**Proposed APP-030 test matrix (for PM spec):**

| ID | Test | Layer | Pass criteria |
|----|------|-------|----------------|
| **I1** | `test_bridge_combat_start_attack_end` | Real `bridge` + roster + `grave-ghoul:1` | start ok; combat set; after monster chain PC attack ok; end ok; `status.combat` null |
| **I2** | `test_execute_tool_combat_start_attack_end` | `orchestrator_with_session` + real bridge | Three `_execute_tool` calls; same end state as I1 |
| **I3** | (optional) `test_dispatch_llm_loop_start_combat` | `_dispatch_like_llm_loop` start only | Unblocks V4 parity via R3 path; attack/end separate dispatches |
| **V4** | Remove skip on `test_bridge_valid_grave_ghoul` | Merge into I1 or delete duplicate | APP-027 spec table updated |

**Fixture sketch (shared):**

```python
def _ensure_combat_roster_session(bridge) -> None:
    # campaign_new + session_start (salt-road)
    # character_create(name="Sammy", background="militia", skill_ids=[...])
    # assert bridge.status()["combat"] is None

def _advance_to_pc_turn(bridge, max_rounds: int = 5) -> dict:
    # poll status; while monster turn and combat active: run_combat_monster_turns()
```

## Risks & unknowns

- **Initiative nondeterminism:** Without `seed` on `bridge.start_combat`, monster may act first; test must advance turns in code — not a flake if capped loop asserts PC turn reached.
- **Roster vs “valid session”:** V4 skip text implies session only; probe shows **roster PC required** for `combat_attack` — PM should not document session-only V4.
- **Orchestrator `combat_attack` during combat:** Blocked when DB combat active — integration must not pack start+attack in one exploration tool batch after start succeeds.
- **`combat_action` vs `combat_attack`:** AC says “attack”; bridge exposes both. I1 should use `combat_attack` to match exploration tool name; optional test for `combat_action` ATTACK + APP-029 auto-chain is out of AC unless PM expands.
- **LLM in scope:** `_combat_turn` / `_combat_llm_loop_inner` call `chat_completion` — any orchestrator E2E needs monkeypatch (APP-028 pattern); not required for minimal AC if I1+I2 suffice.
- **APP-090:** Phased combat verify will add more tests later — keep APP-030 focused on mechanical integration, not narration verify.
- **No new bridge API required** for I1; exposing `seed` on `start_combat` would stabilize initiative but is optional enhancement.

## Raw notes

- Live probe (2026-05-22): no roster → start ok, only `grave-ghoul-1`, monster turn, `combat_end` ok without attack; with roster → `sammy` + ghoul, monster first, `run_combat_monster_turns` → PC turn, `combat_attack` ok (miss), `combat_end` ok.
- Canon monster JSON: `grave-ghoul`, `ash-shade`, `thornwolf`, `ether-larva` under `build/data/monsters/`.
- `bridge.start_combat` default `include_party=True`; party spawn requires `campaign_slug` + roster entries (`combat.py` ~261–269).
- `_combat_active_in_db()` (~488): gates exploration vs combat tool sets.
- APP-027 V4: `@pytest.mark.skip(reason="APP-030 golden-path combat start with roster")` at `test_combat_monster_validation.py` ~91–94.
- G6 `test_execute_tool_combat_attack_passes_gate` proves gate + mock dispatch — not substitute for I1.
- Batch board links APP-025 + APP-030 + APP-077 — APP-025 registry hub test is separate domain spec (`app-exploration-delve-spec.md`).
