# Spec: APP-026-combat-attack-gating

**Status:** draft  
**backlog_ticket:** APP-026  
**ticket_path:** [tmp/backlog/app-026-combat-attack-gating.md](../../app-026-combat-attack-gating.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-combat-play-spec.md`

## Problem

PC attack tools are **dispatched without orchestrator pre-validation**. In exploration, the LLM can call `combat_attack` while `status.combat` is null; `_execute_tool` forwards to `bridge.combat_attack` and the engine rejects after DB lookup. APP-028 strips success fiction on failure, but attacks are still **attempted at the engine layer** and the model may retry wastefully.

In the combat loop, `_execute_combat_action` checks `status.combat` and `actor_id == turn_id` before bridge dispatch but does **not** verify the actor appears in **`combat.initiative`**. Wrong or stale ids may reach the engine and surface as `attacker not in combat` only after bridge call.

**Evidence:** Research brief traces + [`app-combat-play-spec.md`](../../../app-combat-play-spec.md) problem lines (`attacker not in combat` while GM narrated hits).

## Goals

- **Fail fast at orchestrator** before `bridge.combat_attack` / `bridge.combat_action` (ATTACK path) when combat context is invalid.
- **Single helper** `_gate_pc_attack(attacker_id)` shared by exploration `combat_attack` and combat `combat_action` ATTACK.
- **Error strings aligned with engine** so APP-028 narration tests and player-visible `[Mechanics failed — …]` prefixes stay stable.

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Turn-order enforcement (`not your turn`) | Already in `_execute_combat_action` + engine `_assert_actor_turn` — **not** part of `_gate_pc_attack` |
| Remove `combat_attack` from exploration `TOOLS` | Stronger UX change; gate satisfies AC; optional future ticket |
| Monster `monster_attack` auto-chain | Out of scope (PC tools only) |
| Engine-side validation changes | [APP-027](../../app-027-validate-monster-id-at-combat-start.md) |
| Full combat golden-path fixture | [APP-030](../../app-030-combat-integration-test.md) |
| Target-in-initiative / target living checks | Engine owns after gate passes |

## Requirements (summary)

Full behavior: domain spec § **Combat attack gating (APP-026)**.

### R1 — `_gate_pc_attack(attacker_id) -> dict | None`

**Location:** `app/gm/orchestrator.py`

| Step | Check | On fail |
|------|-------|---------|
| 1 | `status = bridge.status()`; `combat = status.get("combat")` | `{ok: false, error: "no active combat for session"}` |
| 2 | Resolve `attacker_id` against `combat["combatants"]` by **id** or **displayName** (case-insensitive), same semantics as engine `_resolve_combatant_id` | If no match, use raw `attacker_id` for error text |
| 3 | Resolved id must appear in `combat["initiative"][].id` | `{ok: false, error: f"attacker not in combat: {attacker_id}"}` |
| 4 | All checks pass | Return **`None`** (caller proceeds to bridge) |

**Notes:**

- Read fresh `bridge.status()` inside the helper (no cached combat block).
- Initiative check is **stricter than engine combatants-only lookup** — satisfies ticket AC “attacker in initiative”.
- Do **not** call bridge or engine from the gate.

### R2 — Wire exploration `combat_attack`

In `_execute_tool`, branch `name == "combat_attack"` (exploration path only — combat-active path still hits combat-only guard first):

1. `if err := self._gate_pc_attack(args.get("attacker_id", "")): return err`
2. Else `return self.bridge.combat_attack(**args)`

When `status.combat` is null, **`bridge.combat_attack` must not be called** (mock assertion in G1).

### R3 — Wire combat `combat_action` ATTACK

In `_execute_combat_action`, when **`action.upper().strip() == "ATTACK"`** (mirror engine `play/tomb_gm/services/simulation/combat.py` ~714–715 — app `tool_args._normalize_combat_action` does **not** uppercase):

1. `if err := self._gate_pc_attack(actor_id): return err`
2. Keep existing `turn_id` check unchanged (after gate).
3. Then `bridge.combat_action(...)`.

**Case rule:** Gate must run for lowercase `"attack"` and mixed-case variants — literal `action == "ATTACK"` would bypass initiative check on the combat-loop path while bridge/engine still resolve the attack.

Existing `if not status.get("combat"): return {"ok": False, "error": "no active combat"}` may remain as defense-in-depth for non-ATTACK actions; on the ATTACK path the gate runs first and returns **`no active combat for session`** to match engine `combat_status`.

### R4 — APP-028 compatibility

Gated failures return `{ok: false, error: …}` into the same `_llm_loop` / `_combat_llm_loop_inner` paths as today. **No change** to `_COMBAT_TOOL_NAMES`, `all_failed` content strip, or beat-trigger short-circuit.

Regression: `app/tests/test_combat_failure_narration.py` **T4** (and full module) must stay green after gate lands.

### R5 — `tools.py` (optional doc touch)

`combat_attack` remains in exploration `TOOLS`. Description already says “in active combat”. **No schema removal** required for AC. Optional one-line description tweak: orchestrator rejects when not in combat — Dev discretion.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Before attack: require `status.combat` | R1 step 1; G1, G4 |
| Attacker in initiative | R1 step 3; G2, G5, G8, G6b |
| Wire `combat_attack` + `combat_action` ATTACK | R2, R3 |
| Spec sync on close | Domain spec § APP-026 + changelog |

## Test plan

```bash
# New — APP-026
python -m pytest app/tests/test_combat_attack_gating.py -q

# Regression — APP-028 narration (gate must not break T4)
python -m pytest app/tests/test_combat_failure_narration.py -q

# Engine (unchanged)
python -m pytest play/tomb_gm/tests/test_combat_attack.py -q
python -m pytest play/tomb_gm/tests/test_combat_turn_enforcement.py -q
```

**New module:** `app/tests/test_combat_attack_gating.py`

| ID | Test | Setup | Pass |
|----|------|-------|------|
| **G1** | `test_execute_tool_combat_attack_gated_no_combat` | `status.combat` null; `_execute_tool("combat_attack", {attacker_id, target_id})` | `{ok: false, error: "no active combat for session"}`; `bridge.combat_attack` **not called** |
| **G2** | `test_gate_pc_attack_rejects_unknown_attacker` | Mock status with combat + initiative `[pc1]`; `_gate_pc_attack("unknown")` | `{ok: false, error: "attacker not in combat: unknown"}` |
| **G3** | `test_gate_pc_attack_resolves_display_name` | Combatants `[{id: pc1, displayName: Aldric}]`, initiative `[{id: pc1}]`; gate `"Aldric"` | Returns `None` |
| **G4** | `test_execute_combat_action_attack_no_combat` | `status.combat` null; `_execute_combat_action("ATTACK", actor_id=…)` | `{ok: false, error: "no active combat for session"}` before `bridge.combat_action` |
| **G5** | `test_execute_combat_action_attack_not_in_initiative` | Monkeypatch `bridge.status()` with `turn_id="pc1"` and `initiative=[{id:"m1"}]` (actor `pc1` requested but not listed); `_execute_combat_action("ATTACK", actor_id="pc1", …)` | `{ok: false, error: "attacker not in combat: pc1"}` before `bridge.combat_action` |
| **G6** | `test_execute_tool_combat_attack_passes_gate` | Valid combat + initiative; mock bridge success | Gate returns None path; `bridge.combat_attack` called once |
| **G6b** | `test_execute_combat_action_attack_passes_gate` | Valid combat + actor in initiative + `turn_id` match; `_execute_combat_action("ATTACK", actor_id=…)` | Gate passes; `bridge.combat_action` called once |
| **G7** | `test_app028_t4_regression` | Re-run or import T4 scenario: exploration `combat_attack` all_failed strip | Prefix only; `bridge.combat_attack` mocked **or** gate returns same error shape APP-028 expects |
| **G8** | `test_execute_combat_action_lowercase_attack_not_in_initiative` | Same status fixture as G5; `_execute_combat_action("attack", actor_id="pc1", …)` | Gate error before `bridge.combat_action` (proves R3 case-normalized ATTACK path) |

Use `orchestrator` fixture from `app/tests/conftest.py`; monkeypatch `bridge.status`, `bridge.combat_attack`, `bridge.combat_action`. Do not use `play/workspace`.

## Affected paths

_Must match ticket **Expected files**._

- `app/gm/orchestrator.py` — `_gate_pc_attack`, R2/R3 wire points
- `app/gm/tools.py` — optional description only (R5)
- `app/tests/test_combat_attack_gating.py` — **new** (G1–G8, G6b)
- `tmp/app-combat-play-spec.md` — § Combat attack gating (APP-026)

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- Outside combat, provoke LLM to attack (or use suggestion if any) → player sees `[Mechanics failed — combat_attack: no active combat for session]` (or equivalent); **no hit fiction**.
- In combat, valid PC turn + ATTACK via `combat_action` → attack resolves as today.
- In combat, wrong actor id not on initiative → failure before narrated hit; `[Mechanics failed — combat_action: …]` or inner-loop strip.

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | PM draft: `_gate_pc_attack`, R1–R5, tests G1–G7, domain spec § APP-026 |
| 2026-05-22 | PM r2 (QA SPEC-001): R3 `action.upper().strip() == "ATTACK"`; G4 gate error explicit; G5 setup; G6b combat-loop happy path; G8 lowercase attack gate test |
