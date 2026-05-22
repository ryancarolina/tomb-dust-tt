# Spec — App Combat Play

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/combat_fsm.py`, combat branch in orchestrator

---

## Spec

- Combat starts via `start_combat` / `start_combat_from_trigger` with valid monster ids from `build/data/monsters/`.
- Turn order from engine; monster turns via `run_combat_monster_turns`.
- After a successful PC **`combat_action`**, orchestrator **`_combat_auto_chain()`** runs monster turns in code until the turn returns to a PC or combat ends (APP-029) — wired from `_combat_turn` and `_combat_llm_loop_inner`.
- PC actions: `combat_attack`, `combat_action`, `cast_spell`, `fortune_spend`.
- UI stays in combat mode until `combat_end` or engine clears combat.
- **Failed tool → no success fiction** — code-owned `[Mechanics failed — …]`; database / tool `ok` leads narration (see § Combat tool failure narration).
- **Attack pre-gating (APP-026):** Before any PC attack dispatch, orchestrator `_gate_pc_attack` requires `status.combat` and attacker in `combat.initiative` — see § Combat attack gating.

### Death

- On PC death: `process_delver_death`, corpse loot, offer `new game` (session-persistence spec).

### Encounter → combat entry (APP-089 handoff)

Combat does **not** begin on `enter_dungeon` alone. See [`app-exploration-delve-spec.md`](app-exploration-delve-spec.md) § Encounter awareness.

| Event | Combat spec behavior |
|-------|---------------------|
| Threat in room, no `start_combat` | Exploration encounter verify only |
| `start_combat` ok | `status.combat` set; orchestrator routes `_combat_turn` |
| Surprise / ambush | Engine flags from encounter contest before round 1 (canon `encounter.md`) |

### Phased combat narration + verify (APP-090) — draft

**Ticket:** [APP-090](backlog/app-090-combat-phased-narration-and-death-beat.md)

After APP-029 auto-chain, narration is **split and verified per phase** — not one LLM pass over the full mechanical list.

| Phase | Verify step | Emit |
|-------|-------------|------|
| `player_resolve` | `build_combat_turn_truth` + slice of PC `combat_action` | Player spell/attack outcome |
| `monster_act` | truth from `monster_attack` rows | Each enemy response |
| `death` | truth from killing blow + HP 0 | Dramatic death beat **required** |
| `run_end` | code-owned (no LLM verify) | Corpse + new game offer |

Uses APP-083 Phase 3: `verify_narration` → retry → publish for each phase. Violations: `damage_without_tool`, `hit_without_tool`, `skipped_killing_blow`.

---

## Combat attack gating (APP-026)

**Ticket:** [APP-026](backlog/app-026-combat-attack-gating.md) · **Run spec:** [`runs/app-026-combat-attack-gating/spec.md`](backlog/runs/app-026-combat-attack-gating/spec.md)

APP-028 owns **visible failure narration** when tools return `ok: false`. APP-026 adds **orchestrator pre-gates** so invalid PC attacks fail **before** bridge/engine dispatch.

### Helper: `_gate_pc_attack(attacker_id) -> dict | None`

**Location:** `app/gm/orchestrator.py`

| Step | Check | On fail |
|------|-------|---------|
| 1 | `bridge.status()` → `combat = status.get("combat")` | `{ok: false, error: "no active combat for session"}` |
| 2 | Resolve `attacker_id` against `combat["combatants"]` by **id** or **displayName** (case-insensitive; mirror engine `_resolve_combatant_id`) | Unresolved → use raw id in error |
| 3 | Resolved id ∈ `combat["initiative"][].id` | `{ok: false, error: f"attacker not in combat: {attacker_id}"}` |
| 4 | Pass | Return **`None`** |

**Out of scope for gate:** turn order (`not your turn`) — `_execute_combat_action` + engine `_assert_actor_turn` remain owners.

### Wire points

| Path | When | Behavior |
|------|------|----------|
| `_execute_tool` → `combat_attack` | Exploration loop (`status.combat` null path) | Run gate; on failure return dict **without** `bridge.combat_attack` |
| `_execute_combat_action` | `action.upper().strip() == "ATTACK"` | Run gate on `actor_id` before turn check + `bridge.combat_action` |

When combat is active in DB, exploration `combat_attack` remains blocked by the existing combat-only tool guard (`During combat only combat_action is available`) — gate applies on the no-combat exploration path and on ATTACK inside combat loop.

**Case rule:** Gate condition must use `action.upper().strip() == "ATTACK"` (engine normalizes the same way; app `tool_args._normalize_combat_action` does not uppercase). Literal `action == "ATTACK"` would skip the gate for lowercase `"attack"` from LLM tool args.

### APP-028 interaction

Gated failures feed the same `_COMBAT_TOOL_NAMES` / `all_failed` strip paths. Error strings **must** stay compatible with existing narration tests (e.g. `no active combat for session`, `attacker not in combat: …`).

### Tests (APP-026)

**Module:** `app/tests/test_combat_attack_gating.py` _(new)_

| ID | Test | Pass |
|----|------|------|
| **G1** | `_execute_tool("combat_attack")` when `status.combat` null | ✓ |
| **G2** | `_gate_pc_attack` — id not in initiative | ✓ |
| **G3** | `_gate_pc_attack` — displayName resolves to initiative id | ✓ |
| **G4** | `_execute_combat_action("ATTACK")` when no combat | ✓ |
| **G5** | `_execute_combat_action("ATTACK")` — not in initiative | ✓ |
| **G6** | Valid gate → `bridge.combat_attack` called | ✓ |
| **G6b** | `_execute_combat_action("ATTACK")` valid initiative + turn | ✓ |
| **G7** | APP-028 T4 regression (`test_combat_failure_narration`) | ✓ |
| **G8** | `_execute_combat_action("attack")` — not in initiative | ✓ |

**Commands:**

```bash
python -m pytest app/tests/test_combat_attack_gating.py -q
python -m pytest app/tests/test_combat_failure_narration.py -q
```

---

## Combat tool failure narration (APP-028)

**Ticket:** [APP-028](backlog/app-028-combat-tool-failure-narration.md) · **Run spec:** [`runs/app-028-combat-failure-narration/spec.md`](backlog/runs/app-028-combat-failure-narration/spec.md)

When any combat mechanic returns `ok: false` or combat never enters the DB, the player must **not** see success-leaning fiction (hits, damage, combat start, initiative, spell effects). Prompt rules in `system_prompt.py` are **not** sufficient — orchestrator enforces deterministically.

### Tool inventory

| Tool | When | On `ok: false` |
|------|------|----------------|
| `start_combat` | Exploration `_llm_loop` | Failure prefix; no combat-start fiction |
| `combat_attack` | Exploration `_llm_loop` | Failure prefix; no hit/damage fiction |
| `combat_end` | Exploration `_llm_loop` | Failure prefix; no “combat ends” fiction unless tool ok |
| `cast_spell` | Exploration `_llm_loop` | Failure prefix; no spell effect fiction |
| `fortune_spend` | Exploration `_llm_loop` | Failure prefix; no Fortune spent fiction |
| `combat_action` | Combat `_combat_llm_loop_inner` only | Failure prefix; no hit/damage/turn fiction |
| Wrong tool in combat loop | Combat inner loop | Same as `combat_action` failure class |

`process_beat` is **not** a combat tool; beat-driven starts are covered under **Beat-trigger start** below.

### Failure message shape

- **Prefix:** `[Mechanics failed — <context>: <error>]`
- Multiple failures in one turn: join with `; ` (e.g. `[Mechanics failed — start_combat: …; combat_attack: …]`).
- **Beat-trigger context:** use `combat start` as context label (matches `_combat_turn` deferred start).
- **Second line (beat-trigger / deferred start only):** short code-owned line, e.g. `Combat could not begin.` — optional for single-tool exploration failures.

### Beat-trigger start (`_handle_combat_trigger`)

After `process_beat`, orchestrator scans `mechanical_summary` for `action: "combat_trigger"` and calls `bridge.start_combat_from_trigger(monster_specs)` when DB has no active combat.

**On `start_combat_from_trigger` → `ok: false`:**

1. **`_handle_combat_trigger` → `str | None`:** returns canonical player string (same shape as `_combat_turn` / `pending_start` failure):
   - `[Mechanics failed — combat start: {error}]`
   - `Combat could not begin.`
   Sets `combat.active = False`. **Must not** silently return with no feedback.
2. **`_execute_tool("process_beat")`:** after beat + trigger, if failure string returned, store on orchestrator (e.g. `self._beat_combat_start_failure`) for the current tool batch.
3. **`_llm_loop` short-circuit:** if beat failure flag set after the batch, return that string **immediately** — no assistant `content` append, no `depth + 1` narrate. Player sees failure **on the same turn** before further `chat_completion`.
4. `status.combat` null; **do not** call `run_combat_monster_turns()`.
5. **Dual-channel:** `process_beat` tool-role JSON may remain `ok: true` with `combat_trigger` in `mechanical_summary` (engine unchanged). **Player channel** is the short-circuit return — tests assert player text, not tool JSON `ok: false`.

**On success:** existing behavior — `combat.active = True`, monster auto-chain as today.

**Optional:** set `pending_start` on trigger instead of inline flag — same message shape required.

### Exploration loop (`_llm_loop`)

Applies to `start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend`.

**Per failed tool:** retain system injection:

`TOOL FAILED ({fn_name}): {result JSON}. You MUST narrate this failure honestly. Do NOT describe success.`

**When every tool call in the turn returns `ok: false`:**

- Return **`[Mechanics failed — {failures}]` only**.
- **Do not** append assistant pre-tool `content` from the same turn (no `\n\n{content}` suffix).
- Player text must not describe hits, combat start, initiative, or spell resolution.

**When some tools succeed:** loop continues; narration may follow tool results and state context.

### Combat loop (`_combat_llm_loop_inner`)

Applies to `combat_action` (and wrong-tool rejections).

**When every tool call in the turn returns `ok: false`:**

- Return **`[Mechanics failed — {failures}]` only** — same content-strip rule as exploration.
- Optional fixed fallback if no model content was captured: `Your action did not resolve.` — **not** success prose from the model.

**Per failed tool (when loop continues):** inject exploration-equivalent `TOOL FAILED` system message before the tool result message.

**When at least one tool succeeds:** existing mechanical brief + second narrate pass; brief marks `ok: false` rows as `FAILED: {error}`.

### `pending_start` path (`_combat_turn`)

When `combat.pending_start` is true, `start_combat_from_trigger` failure already returns:

`[Mechanics failed — combat start: {error}]\n\nCombat could not begin.`

APP-028 requires beat-trigger failures (above) to **match this shape**. Setting `pending_start` on trigger is an optional implementation unification — not required if R1 outcome is met inline.

### State truth

After any failure in this section, `bridge.status()["combat"]` is null unless a tool in the **same** turn successfully started combat. Orchestrator routes to `_combat_turn` only when `combat.active`, `_combat_active_in_db()`, or `awaiting == COMBAT_TURN`.

### Logging

On beat-trigger failure or `all_failed` content strip, log tool names and errors (orchestrator `log_error`) for session debugging — does not change player-visible text.

---

## Problem (from logs)

- `attacker not in combat` repeated while GM narrated attacks
- `monster JSON not found: hollow-knight`
- `[Mechanics failed — combat_attack: …]` only partially enforced
- `combat_trigger` / grave-ghoul: `COMBAT_START` mechanical item with `combat: null` and success fiction (APP-028)

---

## Task checklist

- [x] `combat_fsm.py` + orchestrator `_combat_turn`
- [x] `combat_attack` wired through bridge → `tomb_gm.services.simulation.combat.combat_attack`
- [x] **APP-028** — combat tool failure narration (§ above)
- [x] **APP-029** — monster auto-chain after PC `combat_action` (`_combat_auto_chain`)
- [x] **APP-026** — orchestrator `_gate_pc_attack` before `combat_attack` / `combat_action` ATTACK

**Open work:** [APP-027](backlog/app-027-validate-monster-id-at-combat-start.md), [APP-030](backlog/app-030-combat-integration-test.md), [APP-090](backlog/app-090-combat-phased-narration-and-death-beat.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Tests

```bash
python -m pytest play/tomb_gm/tests/test_combat*.py -q
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py -q
python -m pytest app/tests/test_combat_attack_gating.py -q
```

### APP-028 — combat failure narration (app layer)

**Module:** `app/tests/test_combat_failure_narration.py` _(new)_

| ID | Test | Pass |
|----|------|------|
| **T1** | `_handle_combat_trigger` when start → `ok: false` | ✓ |
| **T2** | `_llm_loop` E2E: `process_beat` + failed `start_combat_from_trigger` + pre-tool ghoul fiction | ✓ |
| **T3** | `_llm_loop` all failed — `start_combat` | ✓ |
| **T4** | `_llm_loop` all failed — `combat_attack` | ✓ |
| **T5** | `_llm_loop` all failed — `combat_end` | ✓ |
| **T6** | `_llm_loop` all failed — `cast_spell` | ✓ |
| **T7** | `_llm_loop` all failed — `fortune_spend` | ✓ |
| **T8** | `_combat_llm_loop_inner` all failed + pre-tool hit fiction | ✓ |
| **T9** | `_combat_llm_loop_inner` wrong tool name during combat | ✓ |
| **T10** | `_combat_llm_loop_inner` partial failure (one fail + one ok, or retry) | ✓ |
| **T11** | _(optional)_ R8 logging on beat short-circuit or `all_failed` strip | ✓ (beat path) |

**Commands:**

```bash
python -m pytest app/tests/test_combat_failure_narration.py -q
```

**Regression (manual / playtest):**

- Attack outside combat → visible failure; GM does not describe a hit.
- Unknown monster id → error before narration.
- Beat-trigger encounter with failed start → no ghoul-attack fiction while `combat: null`.
- APP-026: orchestrator rejects `combat_attack` before engine when `status.combat` null.

### APP-026 — combat attack gating (app layer)

**Module:** `app/tests/test_combat_attack_gating.py` _(new)_

See § **Combat attack gating (APP-026)** for G1–G8 + G6b table.

**Commands:**

```bash
python -m pytest app/tests/test_combat_attack_gating.py -q
python -m pytest app/tests/test_combat_failure_narration.py -q
```

---

## File map

| File | Role |
|------|------|
| `gm/combat_fsm.py` | Combat step state; `pending_start` / `pending_monsters` |
| `gm/orchestrator.py` | `_combat_turn`, `_handle_combat_trigger`, `_llm_loop`, `_combat_llm_loop_inner`, `_combat_auto_chain`, **`_gate_pc_attack`** |
| `gm/bridge.py` | Combat service wrappers |
| `gm/tools.py` | Combat tool schemas |
| `app/tests/test_combat_failure_narration.py` | APP-028 orchestration tests |
| `app/tests/test_combat_attack_gating.py` | APP-026 attack pre-gate tests |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged combat-tool-gating content |
| 2026-05-21 | APP-028 PM draft: § Combat tool failure narration — beat-trigger, `all_failed` content strip, tool inventory, tests T1–T6 |
| 2026-05-21 | APP-028 PM r2: R1 `_llm_loop` short-circuit contract; tests T1–T11 (all five exploration tools, R4 partial-failure injection) |
| 2026-05-21 | **APP-028 done:** `_handle_combat_trigger` failure string + `_beat_combat_start_failure` short-circuit; `_COMBAT_TOOL_NAMES` exploration `all_failed` strip; combat inner strip + partial `TOOL FAILED` injection; `test_combat_failure_narration.py` T1–T11 green |
| 2026-05-22 | **APP-029 done:** `_combat_auto_chain()` runs `run_combat_monster_turns()` after PC action until PC turn or combat end |
| 2026-05-22 | **APP-026 PM draft:** § Combat attack gating — `_gate_pc_attack`, wire `combat_attack` + `combat_action` ATTACK, tests G1–G7 |
| 2026-05-22 | **APP-026 PM r2:** R3 case-normalized ATTACK gate (`action.upper().strip()`); tests G6b, G8; G4/G5 fixture clarity |
| 2026-05-22 | **APP-026 done:** `_gate_pc_attack` + `_resolve_combatant_id_for_gate`; wired `_execute_tool` `combat_attack` and `_execute_combat_action` ATTACK; `test_combat_attack_gating.py` G1–G8 + G6b green; APP-028 regression green |
