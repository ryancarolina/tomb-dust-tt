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
- **Monster id validation (APP-027):** Before combat enters the DB, every `monster_specs` entry must resolve to `build/data/monsters/{id}.json` — see § Monster id validation at combat start.

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
- [x] **APP-027** — monster id validation at combat start (`validate_monster_specs`, bridge/tool_args gates, tests V1–V9)

**Open work:** [APP-030](backlog/app-030-combat-integration-test.md), [APP-090](backlog/app-090-combat-phased-narration-and-death-beat.md) in [`tmp/backlog/README.md`](backlog/README.md).

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

## Monster id validation at combat start (APP-027)

**Ticket:** [APP-027](backlog/app-027-validate-monster-id-at-combat-start.md) · **Run spec:** [`runs/app-027-validate-monster-id-combat/spec.md`](backlog/runs/app-027-validate-monster-id-combat/spec.md)

Unknown or malformed monster ids must fail **before** `combat_state` is written and **before** any LLM narrates combat start. APP-028 already strips success fiction when `start_combat` / beat-trigger start returns `ok: false` on an all-failed turn; APP-027 adds **explicit validation, stable error shapes, and tests** so failures are deterministic and not dependent on engine exceptions alone.

### Validation layers

| Layer | Owner | When | On fail |
|-------|-------|------|---------|
| **Tool args** | `app/gm/tool_args.py` | Exploration `_llm_loop`: `validate_tool_args` **before** `_execute_tool` (APP-080; same as `enter_dungeon`) | `{ok: false, error: "<validate_tool_args message>"}` — bridge **not** called |
| **Monster specs** | Engine `validate_monster_specs` (R1) | Top of `bridge.start_combat` / `start_combat_from_trigger` | `{ok: false, error: …}` — **must not** write `combat_state` |
| **Engine spawn** | `play/tomb_gm/services/simulation/combat.py` | `_spawn_instances` → `parse_monster_specs` + `load_monster_json` | `ValueError` / `FileNotFoundError` → bridge catch (defense-in-depth after R1) |

Research confirms engine validation already runs before INSERT; APP-027 **documents and tests** that contract and adds app-layer gates so empty/malformed LLM args never reach spawn.

### R1 — `validate_monster_specs(content_root, monster_specs) -> str | None`

**Location:** **`play/tomb_gm/services/simulation/combat.py` only** — sole implementation (reuse `MONSTER_SPEC_RE`, `parse_monster_specs`, `load_monster_json`). `app/gm/bridge.py` imports from `tomb_gm.services.simulation.combat`; **no** duplicate regex or parser in `app/gm/`.

| Step | Check | On fail (return error string) |
|------|-------|-------------------------------|
| 1 | `monster_specs` is a non-empty `list` | `"monster_specs required"` or `"monster_specs must be non-empty"` |
| 2 | Each element is a non-empty string | `"invalid monster spec: …"` (match engine `parse_monster_specs` message) |
| 3 | Each spec matches `id` or `id:count` (`MONSTER_SPEC_RE`); count ≥ 1 | Same `ValueError` text as engine: `invalid monster spec: …`, `monster count must be >= 1: …` |
| 4 | For each parsed `monster_id`, `{content_root}/data/monsters/{id}.json` exists | **`monster JSON not found: {monster_id} ({path})`** — preserve substring `monster JSON not found: {id}` for APP-028 tests |
| 5 | Pass | Return **`None`** |

**Empty list:** `monster_specs: []` is **invalid** for `start_combat` — return step-1 error. Do **not** start combat with zero monsters via LLM tool or beat default unless a future ticket explicitly allows it.

**Duplicate ids in one list:** Allowed (engine spawns multiple instances); validation only checks format + file presence per entry.

### R2 — Bridge `start_combat` / `start_combat_from_trigger`

**File:** `app/gm/bridge.py`

1. After session/campaign resolution, call `validate_monster_specs(self.ctx.config.content_root, monster_specs)`.
2. If error string returned: **`{"ok": False, "error": err}`** immediately — **do not** call engine `start_combat`.
3. On success, call engine `start_combat` as today; retain existing `except (ValueError, FileNotFoundError)` as defense-in-depth.

**`start_combat_from_trigger`:** Unchanged duplicate-combat guard (`combat already active`) runs **before** monster validation. Monster validation runs inside delegated `start_combat`.

**Success shape (unchanged):** `{ok: true, …, action: "combat_start"}` plus engine fields.

**Failure shape (canonical):**

```json
{"ok": false, "error": "<human-readable reason>"}
```

No `action` key on failure. Error text for missing JSON **must** include `monster JSON not found: {id}` (path suffix optional but id substring required).

### R3 — `validate_tool_args("start_combat", …)`

**File:** `app/gm/tool_args.py`

| Rule | On fail (`validate_tool_args` return) |
|------|--------------------------------------|
| `monster_specs` missing, not a list, or empty list | `"monster_specs required"` (or equivalent stable string used in tests) |
| Any list element not a non-empty string after strip | `"invalid monster_specs entry"` or delegate to R1 on dispatch |

Exploration `_llm_loop` calls `normalize_tool_args` → `validate_tool_args`; on non-`None` error, sets `result = {ok: false, error: msg}` **without** calling `_execute_tool` — same as `enter_dungeon` (APP-080). Do **not** add validation inside `_execute_tool` for `start_combat`.

### R4 — Wire points

| Path | Entry | Behavior |
|------|-------|----------|
| Exploration `_llm_loop` | Tool batch: R3 → `_execute_tool("start_combat")` → R2 | On `{ok: false}` → APP-028 `all_failed` / `[Mechanics failed — start_combat: …]` |
| Beat trigger | `_handle_combat_trigger` → `start_combat_from_trigger` | R2 only (specs from beat); failure string + short-circuit per APP-028 |
| `pending_start` | `_combat_turn` → `start_combat_from_trigger` | Same failure shape as beat |
| Engine CLI | `cmd_combat.handle_start` | **Out of scope** — may still raise; bridge contract is app canonical |

### R5 — No fiction on unknown id

When validation or engine load fails:

1. **`bridge.status()["combat"]` remains null** (no partial combat row).
2. **Player channel:** APP-028 rules apply — all-failed exploration turn returns `[Mechanics failed — start_combat: {error}]` only; beat path returns `[Mechanics failed — combat start: {error}]` + `Combat could not begin.`
3. **Do not** narrate initiative, charges, or monster presence from pre-tool assistant `content` on all-failed turns.
4. **Mixed-tool turns** (failed `start_combat` + successful tool in same batch): APP-028 allows depth+1 narrate — **non-goal** for APP-027; optional follow-up ticket.

### R6 — Tool schema hygiene (optional Dev)

**File:** `app/gm/tools.py` — remove or replace `hollow-knight:1` in `start_combat` examples with canon ids (`grave-ghoul`, `ash-shade`, `thornwolf`, `ether-larva`). Not required for AC if validation tests pass.

### APP-028 interaction

Failed validation returns `{ok: false, error: …}` into existing `_COMBAT_TOOL_NAMES` / `_beat_combat_start_failure` paths. **Do not** change failure prefix format. Regression: `app/tests/test_combat_failure_narration.py` **T1–T3** must stay green; error substrings `monster JSON not found: grave-ghoul` / `hollow-knight` are contractual.

### Tests (APP-027)

**New module:** `app/tests/test_combat_monster_validation.py` _(or extend `test_combat_failure_narration.py` — prefer dedicated module)_

Use real `content_root` from test fixture (repo `build/` or tomb_gm test root). **Do not** use `play/workspace`.

| ID | Test | Pass |
|----|------|------|
| **V1** | `bridge.start_combat(monster_specs=["hollow-knight:1"])` | ✓ |
| **V2** | `bridge.start_combat(monster_specs=["not a spec"])` | ✓ |
| **V3** | `bridge.start_combat(monster_specs=[])` | ✓ |
| **V4** | `bridge.start_combat(monster_specs=["grave-ghoul:1"])` with valid session | skip (APP-030) |
| **V5** | `_dispatch_like_llm_loop(orch, "start_combat", {"monster_specs": []})` — helper from `app/tests/test_tool_args.py` (APP-080) | ✓ |
| **V6** | `_execute_tool("start_combat", {monster_specs: ["hollow-knight:1"]})` | ✓ |
| **V7** | `_handle_combat_trigger` with mocked beat `monster_specs: ["hollow-knight:1"]` | ✓ |
| **V8** | `_llm_loop` **integration:** real `content_root`, **unmocked** `bridge.start_combat`, single tool `start_combat` + `hollow-knight:1`, assistant pre-tool success fiction | ✓ |

**Engine (required, same ticket):**

| ID | Test | Pass |
|----|------|------|
| **V9** | `play/tomb_gm/tests/test_validate_monster_specs.py`: `validate_monster_specs(root, ["hollow-knight:1"])` | ✓ |

**Optional unit (same ticket):** `validate_tool_args("start_combat", {"monster_specs": []})` in `app/tests/test_tool_args.py` — may duplicate V5; not required if V5 green.

**Optional CLI regression (not V9):** `test_simulation.py -k unknown_monster` — asserts non-zero exit only; run after V9 if desired

**Commands:**

```bash
python -m pytest app/tests/test_combat_monster_validation.py -q
python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q
python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -q
```

End-to-end golden path may extend [APP-030](backlog/app-030-combat-integration-test.md).

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
| `app/tests/test_combat_monster_validation.py` | APP-027 monster spec validation (V1–V8) |
| `play/tomb_gm/tests/test_validate_monster_specs.py` | APP-027 V9 engine unit tests |
| `play/tomb_gm/services/simulation/combat.py` | `parse_monster_specs`, `load_monster_json`, `validate_monster_specs` |

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
| 2026-05-22 | **APP-027 PM draft:** § Monster id validation at combat start — `validate_monster_specs`, bridge/tool_args contracts, empty `monster_specs`, tests V1–V9, APP-028 error substring stability |
| 2026-05-22 | **APP-027 PM r2:** Engine-only R1; R3/R4 `_llm_loop` validate-before-execute (not `_execute_tool`); V5 `_dispatch_like_llm_loop`; V8 unmocked `_llm_loop` integration; V9 `test_validate_monster_specs.py`; ticket Expected files + test module |
| 2026-05-22 | **APP-027 done:** `validate_monster_specs` (engine R1); bridge pre-check (R2); `validate_tool_args("start_combat")` (R3); `tools.py` canon examples (R6); `test_combat_monster_validation.py` V1–V8 + `test_validate_monster_specs.py` V9 green; V4 skipped for APP-030 |
| 2026-05-22 | **APP-092:** R3 `tool_args.py` implementation landed (`normalize`/`validate` for `start_combat`); closes spec/code drift from APP-027 close |
