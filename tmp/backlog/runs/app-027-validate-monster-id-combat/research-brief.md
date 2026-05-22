# Research Brief: APP-027-validate-monster-id-combat

**Date:** 2026-05-22  
**Question:** Where does `start_combat` resolve monster ids today, what happens on unknown or invalid specs, and what validation or narration gaps remain after APP-028?

**backlog_ticket:** APP-027  
**ticket_path:** tmp/backlog/app-027-validate-monster-id-at-combat-start.md  
**domain_spec:** tmp/app-combat-play-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) owns combat FSM, orchestrator combat branch, bridge combat wrappers, and already lists APP-027 under open work with the problem line `monster JSON not found: hollow-knight` and manual test “Unknown monster → error before narration.” [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Combat play** maps to that spec and `play/tomb_gm/services/simulation/combat.py`. Ticket **Expected files** (`app/gm/`, `play/tomb_gm/`) ⊆ combat spec ownership — no new `tmp/app-*-spec.md` required.

## Summary

Monster id validation **already exists in the engine** at combat start: `_spawn_instances` → `parse_monster_specs` + `load_monster_json` reject invalid formats and missing JSON **before** any `combat_state` DB write. The app bridge converts `ValueError` / `FileNotFoundError` into `{ok: false, error: …}` so LLM tool paths get structured failures.

The ticket problem (“unknown ids produce fiction instead of errors”) was **partially addressed by APP-028**: beat-trigger and direct `start_combat` failures now surface `[Mechanics failed — …]` and strip pre-tool success fiction when **all** tools in the turn fail. Gaps remain: **no app-layer pre-validation** of `monster_specs` (empty list, malformed args), **no integration tests** that exercise real bridge/engine rejection (APP-028 mocks errors), **CLI throws** on unknown ids instead of returning `{ok: false}`, and **mixed-tool turns** (failed `start_combat` + successful tool) can still loop to a second LLM narrate pass with combat-start fiction.

Canon drift encourages bad ids: `hollow-knight` and `rust-slime` appear in `beat.py` `MONSTER_ID_RE` and `tools.py` examples but have **no** `build/data/monsters/*.json` (only `grave-ghoul`, `ash-shade`, `thornwolf`, `ether-larva` exist). `ContentService.load_monster` already exposes a non-throwing `MISSING_MONSTER_JSON` blocker pattern the combat path does not reuse.

**Recommended fix (Dev):** Add explicit `validate_monster_specs` (engine or shared helper) called at the top of `start_combat` / bridge entry; extend `validate_tool_args` for `start_combat` (non-empty `monster_specs`, per-spec format); add app + engine tests with real `hollow-knight:1`; document error shapes in combat spec. Optional: align error text with `ContentService` blocker codes; remove or gate fictional monster ids in tool schema examples.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Spec parsing | `play/tomb_gm/services/simulation/combat.py` | `MONSTER_SPEC_RE`, `parse_monster_specs`, `_spawn_instances`, `load_monster_json`, `start_combat` |
| Non-throwing content check | `play/tomb_gm/services/content.py` | `load_monster` → `(data, blocker)` with `MISSING_MONSTER_JSON` |
| Bridge wrapper | `app/gm/bridge.py` | `start_combat`, `start_combat_from_trigger`; catches `ValueError`, `FileNotFoundError` |
| Tool dispatch | `app/gm/orchestrator.py` | `_execute_tool` → `start_combat`; `_handle_combat_trigger` → `start_combat_from_trigger`; `_combat_turn` `pending_start` path |
| Failure narration | `app/gm/orchestrator.py` | `_COMBAT_TOOL_NAMES`, `_llm_loop` all_failed strip (APP-028); beat short-circuit via `_beat_combat_start_failure` |
| Tool schema | `app/gm/tools.py` | `start_combat` params; example includes `hollow-knight:1` |
| Tool arg validation | `app/gm/tool_args.py` | **No** `start_combat` rules — only `combat_action`, `enter_dungeon`, etc. |
| Beat monster detection | `play/tomb_gm/services/beat.py` | `MONSTER_ID_RE` hard-coded ids; emits `combat_trigger` with `monster_specs` |
| CLI combat start | `play/tomb_gm/cli/cmd_combat.py` | `handle_start` calls `start_combat` directly — exceptions propagate |
| FSM | `app/gm/combat_fsm.py` | `pending_start`, `pending_monsters` (cleared on use; rarely set) |
| Domain spec | `tmp/app-combat-play-spec.md` | Problem + manual test for unknown monster; APP-027 open |
| Related (done) | APP-028 | Failure narration when `start_combat` returns `ok: false` |
| Related (open) | APP-030 | Integration test fixture — natural home for end-to-end validation tests |

## Code-path traces

### A — LLM calls `start_combat` directly (exploration loop)

1. **Entry:** `_llm_loop` → model tool call `start_combat` → `_execute_tool` (`orchestrator.py` ~2684–2685).
2. **Arg validation:** `validate_tool_args("start_combat", …)` returns **None** today — empty or missing `monster_specs` not blocked at app layer (~2573–2576).
3. **Bridge:** `start_combat(**args)` → engine `start_combat` (`bridge.py` ~224–239).
4. **Engine:** `_spawn_instances` → for each spec: `parse_monster_specs` then `load_monster_json(content_root, monster_id)` (`combat.py` ~16–27, ~113–124, ~237).
5. **Unknown id:** `FileNotFoundError("monster JSON not found: {id} ({path})")` → bridge `{ok: false, error: str(exc)}`.
6. **Invalid format:** `ValueError("invalid monster spec: …")` or count/tier errors — same bridge catch.
7. **DB:** No `combat_state` row on failure (spawn happens before INSERT).
8. **Narration (APP-028):** If **all** tools fail and `start_combat` ∈ `_COMBAT_TOOL_NAMES`, return `[Mechanics failed — start_combat: …]` only — no initiative/charge fiction (`orchestrator.py` ~2615–2628; `test_combat_failure_narration.py` T3).
9. **Gap:** If another tool in the same turn succeeds (`all_failed = False`), loop continues at depth+1 with `TOOL FAILED` injection — model may still narrate combat starting.

### B — Beat `combat_trigger` → `start_combat_from_trigger`

1. **Entry:** `_execute_tool("process_beat")` → `bridge.process_beat` → `_handle_combat_trigger(result)` (`orchestrator.py` ~2668–2672, ~2480–2499).
2. **Engine beat:** `MONSTER_ID_RE.finditer` extracts ids like `hollow-knight:1` from player text; if no match but combat verbs + `auto_combat`, defaults `["grave-ghoul:1"]` (`beat.py` ~344–361).
3. **Start:** `bridge.start_combat_from_trigger(specs)` → same engine path as A; also rejects if combat already active (`bridge.py` ~302–307).
4. **Failure:** Returns canonical two-line string; `_llm_loop` short-circuits on `_beat_combat_start_failure` before further narrate (`orchestrator.py` ~2609–2613; T1–T2).
5. **Gap:** Beat emits `combat_trigger` with **ok: true** even when monster id is unknown — validation only happens at orchestrator post-hook, not in beat engine.

### C — `pending_start` path (`_combat_turn`)

1. **Entry:** `_combat_turn` when `combat.pending_start` (`orchestrator.py` ~2266–2273).
2. **Start:** `start_combat_from_trigger(specs)`; on failure same `[Mechanics failed — combat start: …]` + `Combat could not begin.`
3. **Note:** `pending_start` is cleared on use; no code path currently sets it `True` — live traffic uses path B.

### D — CLI `combat start --monsters …`

1. **Entry:** `handle_start` → `start_combat(...)` with no try/except (`cmd_combat.py` ~111–127).
2. **Unknown id:** Exception propagates → non-zero exit (`test_simulation.py` `test_combat_unknown_monster` asserts `returncode != 0` only).
3. **Gap:** Inconsistent with bridge `{ok: false}` contract used by the app.

### E — Content CLI pre-check (reference pattern, not wired to combat)

1. **Entry:** `content monster hollow-knight` (`test_world.py` `test_content_monster_missing_blocks`).
2. **Result:** `{ok: false, blocked: true, blockers: [{code: "MISSING_MONSTER_JSON", monster_id: "hollow-knight", …}]}` via `ContentService.load_monster`.
3. **Combat does not call this** — uses throwing `load_monster_json` instead.

## Existing specs & docs

- **Ticket:** Validate monster specs at `start_combat`; clear error; no fiction on unknown id.
- **Combat spec:** “Combat starts via `start_combat` … with **valid monster ids** from `build/data/monsters/`”; problem lists `hollow-knight`; manual regression “Unknown monster → error before narration.”
- **APP-028 (done):** Ensures failed `start_combat` / beat-trigger start does not append success fiction on all-failed turns — **does not add validation**.
- **Engine integration doc:** `build/docs/engine-integration.md` — resolve monster **`id`** slugs from `data/monsters/*.json`.
- **Content:** `build/systems/monsters/hollow-knight.md` exists; **no** matching JSON (canon drift).

## Tests & commands

```bash
# Engine combat (unknown monster: CLI exit != 0 only)
python -m pytest play/tomb_gm/tests/test_simulation.py -k unknown_monster -q

# Content missing-monster blocker (non-throwing reference)
python -m pytest play/tomb_gm/tests/test_world.py -k hollow_knight -q

# Beat trigger (does not assert monster validity)
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py -q

# App failure narration (mocks start_combat errors — not real validation)
python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q

# Full combat suites
python -m pytest play/tomb_gm/tests/test_combat*.py -q
python -m pytest app/tests/test_combat_attack_gating.py app/tests/test_combat_failure_narration.py -q
```

**Test gaps:**

- No test asserts engine/bridge `start_combat(["hollow-knight:1"])` returns `{ok: false, error: …}` with **real** content root.
- No test for invalid spec format through bridge (`"not a spec"`, empty `monster_specs`).
- No app test that mixed-tool turn (failed `start_combat` + ok tool) does not narrate combat start.
- `test_combat_unknown_monster` does not assert error message or JSON shape.

## Risks & unknowns

- **APP-028 overlap:** Narration fixes may make ticket appear done while validation/tests remain thin — PM should separate “validate + test” AC from narration (already done).
- **Mixed-tool batch:** Failed `start_combat` + successful `memory_recall` / `get_status` allows depth+1 narrate — possible combat-start fiction despite `status.combat` null; may need orchestrator rule beyond APP-027 scope.
- **Empty `monster_specs`:** `parse_monster_specs([])` returns `[]`; combat can start with **zero monsters** if party included — unclear if in scope; no ticket AC mention.
- **Beat hard-coded ids:** `MONSTER_ID_RE` includes non-JSON ids (`hollow-knight`, `rust-slime`); fixing validation alone still routes bad ids into `combat_trigger` — content/beat update may be follow-up (outside Expected files unless ticket expanded).
- **Error string stability:** APP-028 tests expect `monster JSON not found: grave-ghoul` / `hollow-knight` substrings — changing message shape breaks narration tests.
- **CLI vs bridge contract:** Engine refactor to `{ok: false}` instead of raise affects CLI handlers and `test_combat_unknown_monster`.
- **No session log replay:** Problem statement cites logs; `app/logs/session-*.jsonl` gitignored — architecture trace only.

## Raw notes

- Live probe: `start_combat(..., monster_specs=['hollow-knight:1'], include_party=False)` raises `FileNotFoundError` at engine layer; bridge converts to `{ok: false}`.
- Canon JSON monsters (2026-05-22): `grave-ghoul`, `ash-shade`, `thornwolf`, `ether-larva`.
- `tools.py` L163 example: `['grave-ghoul:2', 'hollow-knight:1']` — trains LLM on non-existent id.
- `start_combat_from_trigger` duplicate guard: `{ok: false, error: "combat already active"}` before monster validation.
- APP-026 pattern: orchestrator pre-gate before bridge — candidate mirror for `_validate_monster_specs` at `_execute_tool` / bridge entry.
- Domain spec changelog has no APP-027 entry yet — PM adds § Monster id validation at combat start on close.
