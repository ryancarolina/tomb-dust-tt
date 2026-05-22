# Implementation Plan: APP-030-combat-integration-test

**Status:** draft  
**backlog_ticket:** APP-030  
**ticket_path:** [tmp/backlog/app-030-combat-integration-test.md](../../app-030-combat-integration-test.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add **`app/tests/test_combat_integration.py`** with shared fixture helpers that establish the **roster-backed session contract** APP-027 V4 lacked, then exercise the full bridge golden path:

`start_combat(grave-ghoul:1)` → advance to PC turn → `combat_attack` → `combat_end`.

**Layer:** Real `GameBridge` + `conftest.py` `bridge` fixture (`make_isolated_workspace` → repo `build/` content). No orchestrator, no LLM mocks, no hit/damage assertions.

**V4 absorption:** Delete skipped `test_bridge_valid_grave_ghoul` from `test_combat_monster_validation.py`. Happy `start_combat` is **step 2 of I1**, not a duplicate validation-only test.

**Out of scope (this ticket):** I2/I3 orchestrator `_execute_tool` chains, `_combat_turn` + `combat_action`, APP-029 auto-chain, bridge `seed` API, DRY refactor of `_ensure_salt_road_session` into `helpers.py`.

**Files (ticket Expected files only):**

| File | Change |
|------|--------|
| `app/tests/test_combat_integration.py` | **new** — helpers + **I1** `test_bridge_combat_start_attack_end` |
| `app/tests/test_combat_monster_validation.py` | **delete** V4 skip test (L91–94) |
| `tmp/app-combat-play-spec.md` | **on close** — mark APP-030 done, append changelog (no behavior drift) |

_No production code changes._ Bridge combat API already satisfies AC.

---

## Code-path traces (planned)

### Flow A — Fixture `_ensure_combat_roster_session(bridge)` (R2)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `conftest.py:bridge` | Yields `GameBridge(isolated_workspace)` after `init()` — never `play/workspace` |
| 2 | `bridge.py:campaign_new` | `campaign_new("salt-road", "Salt Road")` — tolerate `{ok}` or `"already exists"` in error (mirror validation module L13–15) |
| 3 | `bridge.py:session_start` | `session_start("salt-road")` — assert `{ok: true}` |
| 4 | `bridge.py:character_create` | `character_create(name="Sammy", background="militia")` — **no** explicit `skill_ids` (QA note 2; bridge defaults militia kit) |
| 5 | same L533–538 | Auto `roster_set(campaign_slug, 1, char_id)` on success — assert `created.get("ok")` and `"id" in created` **before** combat (QA adversarial note 1) |
| 6 | `bridge.py:status` | Assert `status.get("combat") is None` — pre-combat guard |

```
bridge (isolated_workspace)
  campaign_new("salt-road")
  session_start("salt-road")
  character_create(name="Sammy", background="militia")
    └─ create_character → roster_set(slot=1)
  assert status.combat is None
```

---

### Flow B — `_advance_to_pc_turn(bridge, max_rounds=5)` (R4)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `bridge.py:status` | Poll nested `status["combat"]` with `turn_id`, `combatants` (shape from `cmd_core.py` handle_status) |
| 2 | `combat_fsm.py:is_pc_turn` | True when `turn_id` combatant has `kind == "pc"` |
| 3 | `bridge.py:run_combat_monster_turns` | Delegates to `run_monster_turns_until_pc_or_end` (`combat.py` L834–864) — breaks on `turn_kind == "pc"` or combat end |
| 4 | Loop | While combat active and not PC turn: call step 3; increment iteration counter |
| 5 | Cap | If `max_rounds` exceeded without PC turn → `pytest.fail("PC turn not reached within N iterations")` |
| 6 | Early end | If combat null mid-loop → `pytest.fail("combat ended before PC turn")` |

Initiative is seed-driven; bridge does not expose `seed` on `start_combat`. Monster-first initiative is normal — loop is required, not flaky.

---

### Flow C — I1 `test_bridge_combat_start_attack_end` (R3, R5)

| Step | File:symbol | Action | Assert |
|------|-------------|--------|--------|
| 1 | test | `_ensure_combat_roster_session(bridge)` | Session + roster ready |
| 2 | `bridge.py:start_combat` L244–261 | `start_combat(monster_specs=["grave-ghoul:1"])` | `ok is True`; `action == "combat_start"` |
| 3 | `bridge.py:status` | Refresh after start | `status["combat"]` non-null |
| 4 | combatants | Scan `status["combat"]["combatants"]` | ≥1 `kind=="pc"`; ≥1 monster id starting with `grave-ghoul` |
| 5 | test | `_advance_to_pc_turn(bridge)` | `is_pc_turn(status)` |
| 6 | R5 resolution | From combatants + `turn_id` | `attacker_id` = PC combatant id (prefer `turn_id` when PC turn); `target_id` = monster with `grave-ghoul` prefix — **do not** hardcode `sammy` |
| 7 | `bridge.py:combat_attack` L265–279 | `combat_attack(attacker_id, target_id)` | `ok is True` (hit or miss); combat still active |
| 8 | `bridge.py:combat_end` L281–284 | `combat_end()` | `ok is True`; `bridge.status().get("combat") is None` |

```
test_bridge_combat_start_attack_end(bridge)
  _ensure_combat_roster_session(bridge)
  start = bridge.start_combat(["grave-ghoul:1"])
    └─ validate_monster_specs (R2 from APP-027)
    └─ engine start_combat(include_party=True, campaign_slug)
  assert PC + grave-ghoul in combatants
  status = _advance_to_pc_turn(bridge)
  attack = bridge.combat_attack(pc_id, ghoul_id)
    └─ engine combat_attack (no auto finalize — QA verified)
  end = bridge.combat_end()
    └─ engine end_combat → active=0
  assert status.combat is None
```

**Contrast (do not duplicate):**

| Module | Proves |
|--------|--------|
| `test_combat_monster_validation` V1–V3, V5–V8 | Failure paths only |
| `test_combat_attack_gating` G1–G8 | Mocked status / gate |
| `test_combat_failure_narration` T3–T7 | Mocked `{ok: false}` |
| `play/tomb_gm/tests/test_combat_attack.py` | Engine-only with `seed=3` |
| **I1 (this ticket)** | App bridge contract + roster + real DB |

---

### Flow D — V4 removal (R6)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `test_combat_monster_validation.py` L91–94 | **Delete** `@pytest.mark.skip` + `test_bridge_valid_grave_ghoul` entirely |
| 2 | Module docstring L1 | Optional: note V1–V3, V5–V8 only (V4 → I1) — only if docstring already lists V4 |
| 3 | Domain spec § APP-027 table | Already points V4 → I1; **done** changelog on ticket close |

Regression: V1–V3, V5–V8 unchanged; test count drops by 1 skipped test (net −1 skip, +1 I1).

---

## Task breakdown

### 1. New module — `app/tests/test_combat_integration.py`

1. Module docstring: `APP-030: bridge combat golden path (I1)`.
2. Imports: `pytest`; `from gm.combat_fsm import is_pc_turn`.
3. Implement `_ensure_combat_roster_session(bridge)` per Flow A.
4. Implement `_combatant_by_kind(combatants, kind)` and `_monster_target(combatants, prefix="grave-ghoul")` (or inline in test — keep minimal).
5. Implement `_advance_to_pc_turn(bridge, max_rounds=5)` per Flow B with explicit `pytest.fail` messages (QA note 4).
6. Implement `test_bridge_combat_start_attack_end(bridge)` per Flow C.
7. After step 5 attack, optionally assert `bridge.status().get("combat")` still active before `combat_end` (strengthens AC vs silent finalize).

**Suggested helper sketch (Dev reference — not prescriptive on private helper names):**

```python
def _ensure_combat_roster_session(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("salt-road")
    assert start.get("ok"), start.get("error")
    created = bridge.character_create(name="Sammy", background="militia")
    assert created.get("ok"), created.get("error")
    assert created.get("id")
    assert bridge.status().get("combat") is None


def _advance_to_pc_turn(bridge, *, max_rounds: int = 5) -> dict:
    for _ in range(max_rounds):
        status = bridge.status()
        if not status.get("combat"):
            pytest.fail("combat ended before PC turn")
        if is_pc_turn(status):
            return status
        adv = bridge.run_combat_monster_turns()
        assert adv.get("ok"), adv
    pytest.fail(f"PC turn not reached within {max_rounds} iterations")


def test_bridge_combat_start_attack_end(bridge):
    _ensure_combat_roster_session(bridge)
    start = bridge.start_combat(monster_specs=["grave-ghoul:1"])
    assert start.get("ok") is True
    assert start.get("action") == "combat_start"
    status = bridge.status()
    combat = status["combat"]
    assert combat is not None
    combatants = combat.get("combatants") or []
    pcs = [c for c in combatants if c.get("kind") == "pc"]
    ghouls = [c for c in combatants if str(c.get("id", "")).startswith("grave-ghoul")]
    assert pcs, "roster PC missing from combatants"
    assert ghouls, "grave-ghoul missing from combatants"
    status = _advance_to_pc_turn(bridge)
    turn_id = status["combat"]["turn_id"]
    attacker_id = turn_id if any(c.get("id") == turn_id and c.get("kind") == "pc" for c in combatants) else pcs[0]["id"]
    target_id = ghouls[0]["id"]
    attack = bridge.combat_attack(attacker_id, target_id)
    assert attack.get("ok") is True
    assert bridge.status().get("combat") is not None
    end = bridge.combat_end()
    assert end.get("ok") is True
    assert bridge.status().get("combat") is None
```

### 2. V4 removal — `app/tests/test_combat_monster_validation.py`

1. Delete lines 91–94 (`@pytest.mark.skip` + `test_bridge_valid_grave_ghoul`).
2. Run validation module pytest — confirm V1–V3, V5–V8 still pass.

### 3. Close — `tmp/app-combat-play-spec.md` (with ticket release)

1. Remove APP-030 from § Open work (L221).
2. Append **done** changelog entry dated close date.
3. Confirm test table lists `test_combat_integration.py` I1 (already drafted PM 2026-05-22).

---

## Files (must ⊆ ticket Expected files)

- `app/tests/test_combat_integration.py` — **new**
- `app/tests/test_combat_monster_validation.py` — V4 delete
- `tmp/app-combat-play-spec.md` — changelog on close

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `python -m pytest app/tests/test_combat_integration.py -q` | I1 green |
| 2 | `python -m pytest app/tests/test_combat_monster_validation.py -q` | V1–V3, V5–V8 green; no skipped V4 |
| 3 | `python -m pytest app/tests/test_combat_attack_gating.py -q` | Regression green |
| 4 | `python -m pytest app/tests/test_combat_failure_narration.py -q` | Regression green |
| 5 | `python -m pytest play/tomb_gm/tests/test_combat_attack.py -q` | Engine contract unchanged (reference) |

**Acceptance mapping:**

| Ticket AC | Plan step |
|-----------|-----------|
| I1 bridge golden path | Task 1 + Test step 1 |
| V4 absorption | Task 2 + Test step 2 |
| Domain spec + changelog | Task 3 |

---

## Rollback / flags

- Revert `test_combat_integration.py` delete if I1 blocked.
- Restore V4 skip in validation module only if I1 deferred — prefer fixing roster fixture over re-skipping.
- No feature flags; test-only change.

---

## Open questions

- **None blocking.** I2/I3 explicitly deferred per spec non-goals.
- **Follow-up (optional):** Extract shared `_ensure_salt_road_session` + roster helper to `app/tests/helpers.py` if a third combat integration test lands (APP-029/090).
