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
- **Failed tool → no success fiction** — code-owned `[Mechanics failed — …]`; database / tool `ok` leads narration (see § Combat tool failure narration).

### Death

- On PC death: `process_delver_death`, corpse loot, offer `new game` (session-persistence spec).

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

**Open work:** [APP-026](backlog/app-026-combat-attack-gating.md)–[APP-030](backlog/app-030-combat-integration-test.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Tests

```bash
python -m pytest play/tomb_gm/tests/test_combat*.py -q
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py -q
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

---

## File map

| File | Role |
|------|------|
| `gm/combat_fsm.py` | Combat step state; `pending_start` / `pending_monsters` |
| `gm/orchestrator.py` | `_combat_turn`, `_handle_combat_trigger`, `_llm_loop`, `_combat_llm_loop_inner` |
| `gm/bridge.py` | Combat service wrappers |
| `gm/tools.py` | Combat tool schemas |
| `app/tests/test_combat_failure_narration.py` | APP-028 orchestration tests |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged combat-tool-gating content |
| 2026-05-21 | APP-028 PM draft: § Combat tool failure narration — beat-trigger, `all_failed` content strip, tool inventory, tests T1–T6 |
| 2026-05-21 | APP-028 PM r2: R1 `_llm_loop` short-circuit contract; tests T1–T11 (all five exploration tools, R4 partial-failure injection) |
| 2026-05-21 | **APP-028 done:** `_handle_combat_trigger` failure string + `_beat_combat_start_failure` short-circuit; `_COMBAT_TOOL_NAMES` exploration `all_failed` strip; combat inner strip + partial `TOOL FAILED` injection; `test_combat_failure_narration.py` T1–T11 green |
