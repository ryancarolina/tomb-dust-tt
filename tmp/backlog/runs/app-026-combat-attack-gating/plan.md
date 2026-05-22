# Implementation Plan: APP-026-combat-attack-gating

**Status:** draft  
**backlog_ticket:** APP-026  
**ticket_path:** [tmp/backlog/app-026-combat-attack-gating.md](../../app-026-combat-attack-gating.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add a single orchestrator helper **`_gate_pc_attack(attacker_id) -> dict | None`** that reads fresh `bridge.status()`, requires `status["combat"]`, resolves the attacker against `combat["combatants"]`, and verifies the resolved id appears in `combat["initiative"][].id`. Wire it into:

1. **Exploration path** — `_execute_tool` → `combat_attack` (before `bridge.combat_attack`).
2. **Combat loop path** — `_execute_combat_action` when **`action.upper().strip() == "ATTACK"`** (before turn check + `bridge.combat_action`).

Gate returns engine-aligned error strings; APP-028 narration/strip paths unchanged.

**Out of scope:** turn-order enforcement (`not your turn`), removing `combat_attack` from exploration `TOOLS`, engine changes (APP-027), monster `monster_attack`, domain spec changelog until impl close.

**Files (ticket Expected files only):**

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_gate_pc_attack`, optional module-level `_resolve_combatant_id_for_gate`, R2/R3 wire points |
| `app/tests/test_combat_attack_gating.py` | **new** G1–G8 + G6b |
| `app/gm/tools.py` | **optional** one-line description tweak (R5) |

---

## Code-path traces (current → planned)

### Flow A — Exploration `combat_attack` with no combat (primary gap)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` | No combat → `_llm_loop` → model calls `combat_attack` | unchanged |
| 2 | `orchestrator.py:_execute_tool` | Combat guard false → `bridge.combat_attack(**args)` (~2530–2531) | **`if err := self._gate_pc_attack(args.get("attacker_id", "")): return err`** then bridge |
| 3 | `orchestrator.py:_gate_pc_attack` | _(missing)_ | `status.combat` null → `{ok: false, error: "no active combat for session"}`; **no bridge call** |
| 4 | `orchestrator.py:_llm_loop` | APP-028 `all_failed` strip on `{ok: false}` | unchanged — gate error feeds same path |
| 5 | `bridge.py:combat_attack` | Engine rejects after DB lookup | **not reached** when gate fails (G1 mock assertion) |

```
process_turn (exploration)
  └─ _llm_loop
       └─ _execute_tool("combat_attack")
            ├─ [NEW] _gate_pc_attack(attacker_id) → err | None
            └─ bridge.combat_attack  # only when gate returns None
```

### Flow B — Exploration `combat_attack` while combat active (existing guard)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_execute_tool` | `combat.active` or `_combat_active_in_db()` → combat-only guard (~2492–2498) | unchanged — returns `During combat only combat_action is available` |
| 2 | Gate | N/A on this path | Gate **not** invoked; AC satisfied by existing guard |

### Flow C — Combat loop `combat_action` ATTACK (partial pre-gate → full gate)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_combat_turn` | `_combat_llm_loop` → `_combat_llm_loop_inner` → `_execute_combat_action` | unchanged |
| 2 | `orchestrator.py:_execute_combat_action` | `if not status.get("combat"): return "no active combat"` (~2324–2325) | For ATTACK: gate runs **first** → `"no active combat for session"` |
| 3 | same | `actor_id != turn_id` → `"not your turn: …"` (~2326–2328) | unchanged — **after** gate on ATTACK path |
| 4 | same | `bridge.combat_action(...)` (~2329–2335) | unchanged after gate + turn check |
| 5 | **[NEW]** ATTACK branch | No initiative check | **`if action.upper().strip() == "ATTACK":`** gate on `actor_id` before step 2 turn logic reorder |

**Case rule (SPEC-001):** Must use `action.upper().strip() == "ATTACK"`, not literal `action == "ATTACK"`. Engine normalizes the same way (`combat.py` ~714–715); `tool_args._normalize_combat_action` does **not** uppercase — LLM may pass `"attack"`.

```
_combat_llm_loop_inner
  └─ _execute_combat_action(action, actor_id, …)
       ├─ [NEW] if action.upper().strip() == "ATTACK":
       │         _gate_pc_attack(actor_id) → err | None
       ├─ (defense-in-depth) if not status.get("combat") …  # non-ATTACK only effective path
       ├─ turn_id check (unchanged)
       └─ bridge.combat_action
```

### Flow D — APP-028 regression (T4)

| Step | Current T4 setup | After gate |
|------|------------------|------------|
| `exploration_ready` | `status.combat` null | unchanged |
| Mock `bridge.combat_attack` | `{ok: false, error: "attacker not in combat"}` | **not called** |
| Gate return | N/A | `{ok: false, error: "no active combat for session"}` |
| `_llm_loop` return | `[Mechanics failed — combat_attack: …]` prefix only | still prefix-only; error text changes to gate message — **T4 still passes** (asserts prefix shape + banned substrings, not exact error) |

---

## Task breakdown

### 1. Module helper — `_resolve_combatant_id_for_gate` (optional, same file)

**Location:** `app/gm/orchestrator.py` — module-level private function placed near other combat helpers (before `Orchestrator` class or just above `_gate_pc_attack`).

Mirror engine `play/tomb_gm/services/simulation/combat.py` `_resolve_combatant_id` (~476–485):

```python
def _resolve_combatant_id_for_gate(combatants: list[dict], ref: str) -> str | None:
    ref_lower = ref.lower().strip()
    for c in combatants:
        cid = str(c.get("id", ""))
        if cid == ref or cid.lower() == ref_lower:
            return cid
        display = str(c.get("displayName", "")).lower()
        if display == ref_lower or ref_lower in display:
            return cid
    return None
```

**Decision:** Inline duplicate in orchestrator (no cross-tree import from `play/tomb_gm`). Do **not** extract shared package unless impl discovers third consumer — keeps diff minimal per user rules.

### 2. R1 — `_gate_pc_attack(attacker_id) -> dict | None`

**Location:** `app/gm/orchestrator.py` — instance method on `Orchestrator`, placed adjacent to `_combat_active_in_db` (~451) or immediately before `_execute_combat_action` (~2315).

**Planned implementation:**

```python
def _gate_pc_attack(self, attacker_id: str) -> dict | None:
    """Return error dict if PC attack context invalid; None if caller may dispatch."""
    status = self.bridge.status()
    combat = status.get("combat")
    if not combat:
        return {"ok": False, "error": "no active combat for session"}

    combatants = combat.get("combatants") or []
    initiative = combat.get("initiative") or []
    resolved = _resolve_combatant_id_for_gate(combatants, attacker_id) or attacker_id

    initiative_ids = {str(row.get("id", "")) for row in initiative}
    if resolved not in initiative_ids:
        return {"ok": False, "error": f"attacker not in combat: {attacker_id}"}

    return None
```

**Notes:**

- Fresh `bridge.status()` every call — no cached combat block.
- Error text uses **raw** `attacker_id` in initiative failure (matches engine / spec G2).
- Initiative check is stricter than engine combatants-only lookup (ticket AC).
- Does **not** call bridge or engine.

### 3. R2 — Wire exploration `combat_attack` — `_execute_tool` ~2530–2531

**Current:**

```python
elif name == "combat_attack":
    return self.bridge.combat_attack(**args)
```

**Planned:**

```python
elif name == "combat_attack":
    if err := self._gate_pc_attack(args.get("attacker_id", "")):
        return err
    return self.bridge.combat_attack(**args)
```

- Runs only when combat-only guard (~2492) is false (exploration path).
- Empty `attacker_id` → resolution fails → `attacker not in combat: ` (engine-compatible).

### 4. R3 — Wire combat `combat_action` ATTACK — `_execute_combat_action` ~2315–2335

**Planned structure:**

```python
def _execute_combat_action(
    self,
    action: str,
    actor_id: str,
    target_id: str | None = None,
    weapon_id: str | None = None,
    spell_id: str | None = None,
) -> dict:
    if action.upper().strip() == "ATTACK":
        if err := self._gate_pc_attack(actor_id):
            return err

    status = self.bridge.status()
    if not status.get("combat"):
        return {"ok": False, "error": "no active combat"}
    turn_id = status["combat"].get("turn_id")
    if actor_id != turn_id:
        return {"ok": False, "error": f"not your turn: expected {turn_id}, got {actor_id}"}
    return self.bridge.combat_action(
        action=action,
        actor_id=actor_id,
        target_id=target_id,
        weapon_id=weapon_id,
        spell_id=spell_id,
    )
```

**Dual no-combat strings (QA note):** Non-ATTACK actions still hit `"no active combat"` from existing check; ATTACK path gate returns `"no active combat for session"` first — documented, APP-028 aligned.

**Turn check unchanged:** Gate does **not** enforce turn order; `_execute_combat_action` + engine remain owners (spec non-goal).

### 5. R5 — Optional `tools.py` description (skip unless trivial)

`combat_attack` description (~174–175) already says “in active combat”. Optional append: “Orchestrator rejects when not in combat.” — Dev discretion; **not required for AC**.

### 6. Domain spec on close — `tmp/app-combat-play-spec.md`

After pytest green:

- Mark checklist **APP-026** done.
- Changelog entry on `release --done`.

No spec edits during impl unless behavior discovery forces PM sync.

---

## Test plan — `app/tests/test_combat_attack_gating.py`

**Run:**

```bash
python -m pytest app/tests/test_combat_attack_gating.py -q
python -m pytest app/tests/test_combat_failure_narration.py -q
python -m pytest play/tomb_gm/tests/test_combat_attack.py play/tomb_gm/tests/test_combat_turn_enforcement.py -q
```

**Fixtures:** `orchestrator` from `app/tests/conftest.py`. Monkeypatch `orchestrator.bridge.status`, `orchestrator.bridge.combat_attack`, `orchestrator.bridge.combat_action`. Do **not** use `play/workspace`.

### Shared status fixture factory

Minimal combat block keys for gate + turn tests:

```python
def _combat_status(
    *,
    turn_id: str = "pc1",
    initiative: list[dict] | None = None,
    combatants: list[dict] | None = None,
) -> dict:
    """Return full bridge.status()-shaped dict with combat block."""
    if initiative is None:
        initiative = [{"id": turn_id, "name": "PC", "initiative": 15}]
    if combatants is None:
        combatants = [{"id": turn_id, "displayName": "Aldric", "kind": "pc", "hp": 10}]
    return {
        "combat": {
            "round": 1,
            "turn_index": 0,
            "turn_id": turn_id,
            "turn_kind": "pc",
            "initiative": initiative,
            "combatants": combatants,
        },
        "awaiting": "COMBAT_TURN",
    }
```

**G6b requires:** `turn_id` matches `actor_id`, actor id in `initiative`, mock `bridge.combat_action` → `{ok: True, …}`.

| ID | Test name (suggested) | Setup | Assertions |
|----|----------------------|-------|------------|
| **G1** | `test_execute_tool_combat_attack_gated_no_combat` | `orchestrator.combat.active = False`; monkeypatch `_combat_active_in_db` → False; `bridge.status()` → `{}` or no `combat`; mock `bridge.combat_attack` | `_execute_tool("combat_attack", {attacker_id: "pc1", target_id: "m1"})` → `{ok: False, error: "no active combat for session"}`; `combat_attack.assert_not_called()` |
| **G2** | `test_gate_pc_attack_rejects_unknown_attacker` | `_combat_status(initiative=[{"id": "pc1"}], combatants=[{"id": "pc1", "displayName": "Aldric"}])` monkeypatched on `bridge.status` | `_gate_pc_attack("unknown")` → `{ok: False, error: "attacker not in combat: unknown"}` |
| **G3** | `test_gate_pc_attack_resolves_display_name` | Same fixture; initiative has `pc1` | `_gate_pc_attack("Aldric")` → `None` |
| **G4** | `test_execute_combat_action_attack_no_combat` | `bridge.status()` → no combat | `_execute_combat_action("ATTACK", actor_id="pc1", target_id="m1")` → `{ok: False, error: "no active combat for session"}`; `combat_action.assert_not_called()` |
| **G5** | `test_execute_combat_action_attack_not_in_initiative` | `_combat_status(turn_id="pc1", initiative=[{"id": "m1"}], combatants=[{"id": "pc1"}, {"id": "m1"}])` | `_execute_combat_action("ATTACK", actor_id="pc1", target_id="m1")` → `{ok: False, error: "attacker not in combat: pc1"}`; `combat_action.assert_not_called()` |
| **G6** | `test_execute_tool_combat_attack_passes_gate` | Valid `_combat_status()`; exploration guards off; mock `combat_attack` → `{ok: True, …}` | Gate path succeeds; `combat_attack.assert_called_once()` |
| **G6b** | `test_execute_combat_action_attack_passes_gate` | Valid `_combat_status(turn_id="pc1")`; mock `combat_action` → `{ok: True, …}` | `_execute_combat_action("ATTACK", actor_id="pc1", target_id="m1")`; `combat_action.assert_called_once()` |
| **G7** | `test_app028_t4_regression` | Run full module or subprocess: `pytest app/tests/test_combat_failure_narration.py -q` | All tests green (gate changes T4 error source, not strip behavior) |
| **G8** | `test_execute_combat_action_lowercase_attack_not_in_initiative` | Same fixture as G5 | `_execute_combat_action("attack", actor_id="pc1", …)` → gate error before `combat_action` |

**G1 note:** Ensure `_execute_tool` reaches `combat_attack` branch — `creation.active = False`, `combat.active = False`, `_combat_active_in_db` false.

**G5/G8 note:** `turn_id="pc1"` satisfies turn check so failure is **initiative gate**, not turn order.

---

## Implementation order

1. Add `_resolve_combatant_id_for_gate` + `_gate_pc_attack` → **G2, G3** (direct unit calls)
2. Wire R2 `_execute_tool` → **G1, G6**
3. Wire R3 `_execute_combat_action` ATTACK branch → **G4, G5, G6b, G8**
4. Run APP-028 regression → **G7**
5. Optional `tools.py` description
6. Domain spec checklist + changelog on `release --done`

---

## Verification checklist (impl agent)

- [ ] `_gate_pc_attack` never calls bridge or engine
- [ ] Exploration `combat_attack`: `bridge.combat_attack` not called when `status.combat` null (G1)
- [ ] ATTACK gate uses `action.upper().strip() == "ATTACK"` (G8)
- [ ] Initiative check uses `initiative[].id`, not combatants alone
- [ ] Error strings: `no active combat for session`, `attacker not in combat: {raw_id}`
- [ ] G1–G8 + G6b green; `test_combat_failure_narration.py` green
- [ ] Engine regression commands run (unchanged behavior)
- [ ] `tmp/app-combat-play-spec.md` checklist + changelog on `release --done`

---

## Pointers

- Research traces A–E: [research-brief.md](./research-brief.md)
- Requirement IDs R1–R5: [spec.md](./spec.md)
- QA gates: [qa-spec-pass.md](./qa-spec-pass.md) (round 2 PASS)
- APP-028 plan (sibling, do not regress): [app-028 plan](../app-028-combat-failure-narration/plan.md)
