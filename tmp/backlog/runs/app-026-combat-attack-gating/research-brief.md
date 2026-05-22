# Research Brief: APP-026-combat-attack-gating

**Date:** 2026-05-22  
**Question:** Where are PC attacks dispatched today, what validation runs before the engine, and how should orchestrator enforce `status.combat` + attacker-in-initiative before any attack resolves?

**backlog_ticket:** APP-026  
**ticket_path:** tmp/backlog/app-026-combat-attack-gating.md  
**domain_spec:** tmp/app-combat-play-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) owns combat FSM, orchestrator combat branch, bridge combat wrappers, and already lists APP-026 under open work with the problem statement (`attacker not in combat` while GM narrates hits). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Combat play** maps to that spec and `play/tomb_gm/services/simulation/combat.py`. Ticket **Expected files** (`app/gm/orchestrator.py`, `app/gm/tools`) ⊆ combat + tool-schema ownership — no new `tmp/app-*-spec.md` required. PM will add § attack gating behavior + tests to the combat spec on close.

## Summary

**Attacks are not pre-gated at the orchestrator layer.** The exploration LLM can call `combat_attack` whenever routing is in `_llm_loop` (no active combat in orchestrator/DB). The call falls through `_execute_tool` → `bridge.combat_attack` → engine `combat_attack()`, which validates combat state and combatant membership **after** dispatch. Failures return `ok: false` (`no active combat for session`, `attacker not in combat`, `not your turn`), and APP-028 now strips success fiction on all-failed turns — but the tool is still **reachable and executable** outside valid combat context.

During active combat, `combat_attack` is **blocked** at `_execute_tool` (`During combat only combat_action is available`). PC attacks go through `_execute_combat_action`, which pre-checks `status.combat` and `actor_id == turn_id` but **does not** explicitly verify initiative membership (turn_id is derived from initiative in `handle_status` / `combat_status`).

There is **no `app/gm/tools/` package** — tool schemas live in `app/gm/tools.py` (`combat_attack` remains in exploration `TOOLS`; combat loop uses `COMBAT_ACTION_TOOL` only). `app/gm/tool_args.py` normalizes/validates `combat_action` required fields but has **no** rules for `combat_attack`.

**Recommended fix (Dev):** Add a shared orchestrator helper (e.g. `_gate_pc_attack(attacker_id) -> dict | None`) that reads `bridge.status()`, requires `status["combat"]`, resolves `attacker_id` against `combat["initiative"]` ids (reuse engine `_resolve_combatant_id` pattern on `combat["combatants"]` if needed), and returns `{ok: false, error: …}` before bridge dispatch. Wire it into (1) `_execute_tool` `combat_attack` branch and (2) `_execute_combat_action` when `action == "ATTACK"`. Keep error strings aligned with engine messages for APP-028 narration tests. Optional PM decision: deprecate exploration `combat_attack` in `tools.py` / prompt (system already says use `process_beat` outside combat, `combat_action` inside) — not required by ticket AC.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Turn routing | `app/gm/orchestrator.py` `process_turn` | Routes to `_combat_turn` when `combat.active`, `_combat_active_in_db()`, or resume `COMBAT_TURN` |
| Exploration tool dispatch | `app/gm/orchestrator.py` `_llm_loop`, `_execute_tool` | `combat_attack` only when **not** in combat (lines ~2492–2531) |
| Combat tool dispatch | `app/gm/orchestrator.py` `_combat_llm_loop_inner`, `_execute_combat_action` | `COMBAT_ACTION_TOOL` only; ATTACK → `bridge.combat_action` → engine `combat_attack` |
| Combat failure strip | `app/gm/orchestrator.py` `_COMBAT_TOOL_NAMES`, `_llm_loop` all_failed | APP-028: `combat_attack` failures return prefix-only (no hit fiction) |
| Bridge | `app/gm/bridge.py` | `combat_attack`, `combat_action`, `status()` → `handle_status` |
| Tool schemas | `app/gm/tools.py` | `combat_attack` in exploration `TOOLS`; `COMBAT_ACTION_TOOL` separate |
| Tool arg validation | `app/gm/tool_args.py` | `combat_action` only — no `combat_attack` normalize/validate |
| Status / combat block | `play/tomb_gm/cli/cmd_core.py` `handle_status` | Sets `payload["combat"]` with `initiative`, `combatants`, `turn_id`, `turn_kind` |
| Engine attack | `play/tomb_gm/services/simulation/combat.py` | `combat_attack`, `execute_combat_action`, `combat_status`, `_assert_actor_turn`, `_resolve_combatant_id` |
| LLM guidance | `app/gm/system_prompt.py`, `app/gm/context.py` | Combat: `combat_action` only when `Awaiting: COMBAT_TURN`; context lists initiative + combatant ids |
| Domain spec | `tmp/app-combat-play-spec.md` | Problem: attacks outside valid context; APP-026 open |
| Related (done) | APP-028 | Failure narration when tools fail — does **not** replace pre-gate |
| Related (open) | APP-030 | Integration test fixture — can host APP-026 app tests |

## Code-path traces

### A — Exploration LLM calls `combat_attack` with no combat (**primary gap**)

1. **Entry:** `process_turn` → no combat → `_llm_loop` → model tool call `combat_attack` (`orchestrator.py` ~1064–1103, 2420–2431).
2. **`_execute_tool`:** `combat.active` and `_combat_active_in_db()` both false → passes combat-only guard → `bridge.combat_attack(**args)` (~2530–2531).
3. **Engine:** `combat_status` → `{ok: false, error: "no active combat for session"}` (`combat.py` ~625–627) **or**, if DB somehow has combat but attacker unknown, `{ok: false, error: "attacker not in combat: …"}` (~638–640).
4. **No orchestrator pre-check** of `status.combat` or initiative before step 2.
5. **Exit:** APP-028 `_llm_loop` injects `TOOL FAILED`, and on `all_failed` returns `[Mechanics failed — combat_attack: …]` only (`test_combat_failure_narration.py` T4). Player sees failure, but attack was still **attempted** at engine layer.

### B — Exploration LLM calls `combat_attack` while combat active (**already blocked, different error**)

1. Combat started (e.g. `_handle_combat_trigger` success) → `combat.active = True` or DB row exists.
2. Same-turn or next `_execute_tool("combat_attack")` hits combat guard (~2492–2498): `{ok: false, error: "During combat only combat_action is available. Got: combat_attack"}`.
3. Engine `combat_attack` **not** called. AC’s `status.combat` + initiative check is **not** the error the model sees today.

### C — Combat loop: `combat_action` ATTACK (**partial pre-gate**)

1. **Entry:** `_combat_turn` → `_combat_llm_loop` → `_combat_llm_loop_inner` → `_execute_combat_action` (~2262, 2315–2335).
2. **Orchestrator pre-checks:** `status.get("combat")` else `"no active combat"`; `actor_id != turn_id` → `"not your turn: expected …"`.
3. **Bridge:** `combat_action` → `resolve_pc_action_and_advance` → `execute_combat_action` → `combat_attack` (`combat.py` ~714–727).
4. **Engine re-validates:** `combat_status`, `_assert_actor_turn`, `find_combatant` (combatants list, not initiative list explicitly).
5. **Gap vs AC:** No explicit “attacker in initiative” check at orchestrator; relies on `turn_id` match. Wrong display-name id without resolution may still fail at engine with `attacker not in combat`.

### D — Engine validation reference (post-dispatch)

| Check | Location | Error |
|-------|----------|-------|
| Active combat row | `combat_status` | `no active combat for session` |
| Actor turn | `_assert_actor_turn` | `not your turn: expected …` |
| Attacker in combatants | `find_combatant` | `attacker not in combat: {id}` |
| PC-only via `combat_attack` | `combat_attack` | `only PC attacks are supported via combat_attack` |
| Living attacker/target | `combat_attack` | `attacker is defeated` / `target already defeated` |

Initiative ids are built from living combatants at round start (`roll_initiative_for_round`, ~174–190); in normal flow initiative ids ⊆ combatant ids. AC wording “in initiative” is stricter than engine’s combatants lookup — orchestrator gate should check `initiative[].id` to match ticket.

### E — Status shape for gating

`handle_status` when `combat_state.active = 1` (`cmd_core.py` ~204–218):

```python
payload["combat"] = {
    "round", "turn_index", "turn_id", "turn_kind",
    "initiative": [{"id", "name", "initiative", "natural", …}, …],
    "combatants": [{"id", "displayName", "kind", "hp", …}, …],
}
payload["awaiting"] = "COMBAT_TURN"
```

Orchestrator `_combat_active_in_db()` is `bool(bridge.status().get("combat"))` (~451–455).

## Existing specs & docs

- **Ticket AC:** Before attack → require `status.combat` and attacker in initiative.
- **Combat spec:** Problem logs include `attacker not in combat` + partial `[Mechanics failed]`; manual regression “Attack outside combat → visible failure”; APP-026 listed open.
- **APP-028 spec (non-goal):** Pre-check gating deferred to APP-026; APP-028 owns visible failure when `ok: false` — **both** apply after APP-026 lands.
- **System prompt:** Outside combat, aggression via `process_beat`; in combat, `combat_action` only (`system_prompt.py` ~219).
- **Tool description:** `combat_attack` says “in active combat” (`tools.py` ~174–175) — schema still exposed in exploration tool list.

## Tests & commands

```bash
# Engine attack + turn enforcement (no app orchestrator gating)
python -m pytest play/tomb_gm/tests/test_combat_attack.py -q
python -m pytest play/tomb_gm/tests/test_combat_turn_enforcement.py -q

# APP-028 — combat_attack all_failed narration (mock bridge, no pre-gate)
python -m pytest app/tests/test_combat_failure_narration.py -k combat_attack -q
python -m pytest app/tests/test_combat_failure_narration.py -q
```

**Test gaps (app layer — APP-026 / APP-030):**

| ID | Scenario | Assert |
|----|----------|--------|
| **G1** | `_execute_tool("combat_attack")` when `status.combat` is null | Returns `ok: false` **without** calling `bridge.combat_attack` (mock) |
| **G2** | `status.combat` set, `attacker_id` not in `initiative` | Orchestrator gate fails before bridge |
| **G3** | `status.combat` set, attacker in initiative, wrong turn | Existing engine / `_execute_combat_action` turn error (document expected owner) |
| **G4** | `_execute_combat_action(action="ATTACK")` with no combat | `"no active combat"` at orchestrator (already present — regression) |
| **G5** | After gate, APP-028 T4 still passes (failure prefix, no hit fiction) | Regression when gate returns same error shape |

No existing `app/tests/test_combat_attack_gating.py`.

## Risks & unknowns

- **Paradox path B:** Pre-gating `status.combat` on exploration `combat_attack` is redundant with the combat-only tool guard when DB combat exists — main value is **fail-fast without engine** when `combat` is null and clearer errors when PM also loosens/removes the “only combat_action” block (unlikely).
- **Initiative vs combatants:** Engine uses combatants for membership; ticket says initiative — use initiative ids at orchestrator to satisfy AC; document if they diverge after future engine changes.
- **ID resolution:** LLM may pass display names; engine `_resolve_combatant_id` matches id/displayName — orchestrator gate should mirror or call shared helper to avoid false “not in initiative” rejects.
- **Remove `combat_attack` from TOOLS?** Stronger than AC; would reduce mistaken LLM calls but changes exploration tool surface — PM call.
- **APP-028 overlap:** Gating returns `ok: false`; narration path unchanged. Do not regress T4/T8 all_failed strip behavior.
- **Turn enforcement scope:** Ticket AC does not mention “must be actor’s turn” — engine + `_execute_combat_action` already enforce; PM may scope APP-026 to context membership only.
- **Historical logs:** Spec cites repeated `attacker not in combat` with success fiction — APP-028 mitigates fiction leak; APP-026 addresses **reachability** and early rejection.

## Raw notes

- User prompt referenced `app/gm/tools` — only `app/gm/tools.py` exists (no tools package).
- `combat_attack` in `_COMBAT_TOOL_NAMES` (~100–107) — gated failures participate in APP-028 content strip.
- Monster attacks use `monster_attack` in auto-chain (`run_combat_monster_turns`) — out of ticket scope (PC attack tools only).
- `_execute_combat_action` turn check uses `status["combat"].get("turn_id")` — same source as initiative row at `turn_index`.
- `test_combat_attack_unknown_attacker` asserts engine-level reject only (`play/tomb_gm/tests/test_combat_attack.py`).
