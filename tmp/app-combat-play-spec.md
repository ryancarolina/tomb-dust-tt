# Spec — App Combat Play

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/combat_fsm.py`, combat branch in orchestrator

---

## Spec

- Combat starts via `start_combat` / `start_combat_from_trigger` with valid monster ids from `build/data/monsters/`.
- Turn order from engine; monster turns via `run_combat_monster_turns`.
- PC actions: `combat_attack`, `combat_action`, `cast_spell`, `fortune_spend`.
- UI stays in combat mode until `combat_end` or engine clears combat.
- **Failed tool → no hit narration** (`[Mechanics failed — …]`).

### Death

- On PC death: `process_delver_death`, corpse loot, offer `new game` (session-persistence spec).

---

## Problem (from logs)

- `attacker not in combat` repeated while GM narrated attacks
- `monster JSON not found: hollow-knight`
- `[Mechanics failed — combat_attack: …]` only partially enforced

---

## Task checklist

- [x] `combat_fsm.py` + orchestrator `_combat_turn`
- [x] `combat_attack` wired through bridge → `tomb_gm.services.simulation.combat.combat_attack`
- [ ] Before attack: require `status.combat` and attacker in initiative
- [ ] Validate monster specs at `start_combat` with clear error (no fiction on unknown id)
- [ ] Enforce failure narration for **all** combat tools (no success fiction on `ok: false`)
- [ ] Auto-chain monster turns after PC action
- [ ] Integration test: combat start → attack → end

---

## Tests

```bash
python -m pytest play/tomb_gm/tests/test_combat*.py -q
```

- Attack outside combat → visible failure; GM does not describe a hit.
- Unknown monster id → error before narration.

---

## File map

| File | Role |
|------|------|
| `gm/combat_fsm.py` | Combat step state |
| `gm/orchestrator.py` | `_combat_turn`, tool handlers |
| `gm/bridge.py` | Combat service wrappers |
| `gm/tools.py` | Combat tool schemas |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged combat-tool-gating content |
