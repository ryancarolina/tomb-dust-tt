# Research Brief: APP-028-combat-failure-narration

**Date:** 2026-05-21
**Question:** Where do combat tool `ok: false` results still allow success fiction (especially `combat_start` / grave-ghoul triggers with `combat: null`), and what orchestrator patterns already block or should block hit/start narration?

**backlog_ticket:** APP-028
**ticket_path:** tmp/backlog/app-028-combat-tool-failure-narration.md
**domain_spec:** tmp/app-combat-play-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) owns `gm/combat_fsm.py`, combat branch in `orchestrator.py`, and documents the target behavior (“Failed tool → no hit narration”, `[Mechanics failed — …]`). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Combat play** maps to that spec and `play/tomb_gm/services/simulation/combat.py`. Cross-cutting “code state leads narration” also appears in [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) (orchestrator owns the LLM loop); that is a **coordination** spec, not a missing domain owner. Ticket **Expected files** (`app/gm/orchestrator.py`) ⊆ combat + orchestrator ownership — no new `tmp/app-*-spec.md` required.

## Summary

Combat failures are **inconsistently enforced** between code paths. The grave-ghoul / `combat: null` scenario matches **`_handle_combat_trigger`**: `process_beat` returns `ok: true` with a `combat_trigger` mechanical item, orchestrator calls `start_combat_from_trigger`, and on failure **does nothing** — no error in tool result, no `[Mechanics failed — …]`, no system “TOOL FAILED” injection. The exploration LLM then narrates from a successful beat plus its own prose, while `status.combat` stays null.

Direct LLM calls to `start_combat`, `combat_attack`, `combat_end`, `cast_spell`, and `fortune_spend` go through **`_llm_loop`**, which injects a failure system message per failed tool but, when **all** tools fail and the assistant already emitted `content`, returns `[Mechanics failed — …]\n\n{content}` — **appending pre-tool success fiction**. The combat-only path **`_combat_llm_loop_inner`** has the same `all_failed` + `content` pattern and **does not** inject the exploration “TOOL FAILED” system line.

One **good** path exists: `_combat_turn` when `combat.pending_start` is true and `start_combat_from_trigger` fails — it returns a code-owned failure string and clears `combat.active`. **`pending_start` is never set to `True` anywhere in the repo** (only cleared); the live trigger path is `_handle_combat_trigger` after `process_beat`, not `pending_start`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Turn routing | `app/gm/orchestrator.py` `process_turn` | Routes to `_combat_turn` when `combat.active`, `_combat_active_in_db()`, or `awaiting == COMBAT_TURN` |
| Exploration LLM loop | `app/gm/orchestrator.py` `_llm_loop` | All non-creation tools; TOOL FAILED injection; `all_failed` early return with assistant `content` |
| Combat LLM loop | `app/gm/orchestrator.py` `_combat_llm_loop`, `_combat_llm_loop_inner` | `COMBAT_ACTION_TOOL` only; `all_failed` return; second narrate pass on success |
| Combat FSM turn | `app/gm/orchestrator.py` `_combat_turn`, `_combat_auto_chain`, `_combat_mechanical_brief` | Code-driven monster turns; mechanical brief includes `FAILED:` for `ok: false` items |
| Beat → combat trigger | `app/gm/orchestrator.py` `_handle_combat_trigger` | Called from `_execute_tool` after `process_beat`; **silent on start failure** |
| Combat state | `app/gm/combat_fsm.py` | Steps include `COMBAT_ENCOUNTER` etc.; `pending_start` / `pending_monsters` (restore-only in practice) |
| Bridge combat | `app/gm/bridge.py` | `start_combat`, `start_combat_from_trigger`, `combat_attack`, `combat_action`, `combat_end`, `run_combat_monster_turns` |
| Tool schemas | `app/gm/tools.py` | `start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend`; combat mode uses `COMBAT_ACTION_TOOL` |
| LLM rules | `app/gm/system_prompt.py`, `app/gm/context.py` | Prompt: narrate failure on `ok: false`; context shows combat block only when `status.combat` set |
| Engine beat | `play/tomb_gm/services/beat.py` | Emits `combat_trigger` (`ok: true`) — does **not** start combat in DB |
| Engine combat | `play/tomb_gm/services/simulation/combat.py` | `start_combat` → `action: combat_start`; `FileNotFoundError` for missing monster JSON |
| Domain spec | `tmp/app-combat-play-spec.md` | Problem: partial `[Mechanics failed]` enforcement |
| Orchestrator spec | `tmp/app-llm-orchestrator-spec.md` | Mechanical truth; lists APP-028 as open |
| Related tickets | APP-026 (attack gating), APP-027 (monster id at start) | Engine errors exist; app still narrates fiction |
| Session evidence | `app/logs/session-2026-05-20.jsonl` (gitignored) | Referenced in spec/analyze script; **not present** in workspace |

## Code-path traces

### A — Grave-ghoul / `combat_trigger` → `combat_start` fails (`combat: null`) — **primary bug**

1. **Entry:** Exploration `process_turn` → `_llm_loop` → tool `process_beat` (`orchestrator.py:2040–2042`).
2. **Engine:** `beat.process_beat` detects monsters / `auto_combat` → appends mechanical item `{ok: true, action: "combat_trigger", monster_specs: ["grave-ghoul:1"], ...}` (`beat.py:349–361`). DB combat row **not** created (`test_combat_beat_trigger.py` asserts no active combat).
3. **Orchestrator:** `_handle_combat_trigger(beat_result)` iterates `mechanical_summary` (`orchestrator.py:1906–1917`).
4. If `not _combat_active_in_db()`: `start = bridge.start_combat_from_trigger(specs)` (default `grave-ghoul:1`).
5. **On `start.get("ok")` false** (unknown monster, no roster, combat already active, initiative failure, etc.): **no branch** — trigger handler ends with no feedback.
6. **Return to LLM:** `process_beat` tool message is still overall **`ok: true`** with `combat_trigger` in summary — model treats encounter as triggered.
7. **State:** `bridge.status()` → `combat: null`; `build_state_context` has no combat block (`context.py:59–76`).
8. **Exit:** LLM narration may describe ghouls attacking / combat starting — **success fiction without FSM**.

### B — LLM calls `start_combat` directly (exploration loop)

1. **Entry:** `_llm_loop` → `_execute_tool("start_combat")` → `bridge.start_combat` (`orchestrator.py:2054–2055`, `bridge.py:224–239`).
2. **Failure:** `ValueError` / `FileNotFoundError` → `{ok: false, error: "monster JSON not found: hollow-knight"}` (engine `combat.py:30–33`).
3. **Loop:** Failed result logged; system message injected: `TOOL FAILED (start_combat): … You MUST narrate this failure honestly` (`orchestrator.py:1986–1991`).
4. **If `all_failed` and assistant `content` non-empty:** early return `[Mechanics failed — start_combat: …]\n\n{content}` (`1999–2006`) — **content may describe combat starting**.
5. **If depth ≥ 2 and still all failed:** user directive to narrate text only (`2008–2013`) — soft guard, not deterministic strip.

### C — LLM calls `combat_attack` outside combat (exploration loop)

1. **Entry:** `_execute_tool("combat_attack")` when `not combat.active` and `not _combat_active_in_db()` (`orchestrator.py:2056–2057`).
2. **Engine:** `combat_attack` → `combat_status` not ok or `attacker not in combat` → `{ok: false, error: "…"}` (`combat.py:625–640`).
3. **Same as B** for TOOL FAILED injection and `all_failed` + `content` leak.
4. Spec problem line: `attacker not in combat` repeated while GM narrated attacks (`app-combat-play-spec.md`).

### D — Active combat: `combat_action` via `_combat_llm_loop_inner`

1. **Entry:** `_combat_turn` → `_combat_llm_loop` when PC turn (`orchestrator.py:1759–1761`).
2. Tools: only `combat_action` (`1800–1840`); wrong tool name → `{ok: false, error: "During combat only combat_action…"}`.
3. **`_execute_combat_action`:** pre-checks `status.combat`, turn_id (`1884–1904`) before `bridge.combat_action`.
4. **On `all_failed`:** return `[Mechanics failed — …]\n\n{content or 'Your action did not resolve.'}` (`1848–1854`) — **no TOOL FAILED system message**; same content leak risk.
5. **On success:** mechanical brief + second LLM call “Narrate honestly” (`1867–1880`); brief marks failed mechanical rows as `FAILED:` (`1700–1701`).

### E — `pending_start` combat start (code-owned failure — **good, likely unused**)

1. **Entry:** `_combat_turn` if `self.combat.pending_start` (`1710–1717`).
2. `start_combat_from_trigger`; on failure: `combat.active = False`, return `[Mechanics failed — combat start: {error}]\n\nCombat could not begin.`
3. **Gap:** `pending_start = True` **never assigned** in codebase (grep only clears flag / restores from dict). Real starts use path A or B.

### F — Successful trigger start (baseline)

1. `_handle_combat_trigger`: `start.get("ok")` → `combat.active = True`, `run_combat_monster_turns()` (`1913–1917`).
2. Next player input: `_combat_active_in_db()` → `_combat_turn` (775–777).

## Existing specs & docs

- **Ticket:** Success fiction when combat tools return `ok: false`; AC: enforce failure narration for **all** combat tools.
- **Combat spec:** `[Mechanics failed — …]` on failed tools; tests: attack outside combat → visible failure; unknown monster → error before narration.
- **Orchestrator spec:** “Code state leads narration”; combat mode uses `combat_fsm` + combat tools; APP-028 listed as open work.
- **APP-027:** Validate monster id at `start_combat` (engine-side; app narration gap remains).
- **APP-026:** Gate attacks before combat context (overlaps `combat_attack` outside FSM).

## Tests & commands

```bash
# Engine combat (no app narration assertions)
python -m pytest play/tomb_gm/tests/test_combat*.py -q

# Beat emits trigger, does not start combat in DB
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py -q

# Missing monster content CLI
python -m pytest play/tomb_gm/tests/test_world.py -k hollow_knight -q
```

**Test gaps (app layer):**

- No `app/tests/test_*` for orchestrator combat failure narration.
- No test that `_handle_combat_trigger` surfaces `start_combat` failure to the player.
- No test that `all_failed` paths drop assistant pre-tool `content` on combat tool failure.

**Session log:** `tmp/analyze_session_log.py` targets `app/logs/session-2026-05-20.jsonl` — file absent (gitignored); cannot replay grave-ghoul COMBAT_START event locally.

## Risks & unknowns

- **`all_failed` + assistant `content`:** Both `_llm_loop` and `_combat_llm_loop_inner` append model prose from the **same** turn that invoked failing tools — prompt/system injection is not enough; code may need to **discard** success-leaning `content` when `all_failed` (mirror stricter creation sanitizers).
- **`_handle_combat_trigger` silent failure:** Highest-impact fix for beat-driven encounters; may need to merge start result into `process_beat` tool payload or force code-owned failure narration before exploration LLM continues.
- **`pending_start` dead code:** Setting `pending_start` on trigger (instead of immediate `start_combat_from_trigger`) would unify with path E — product decision for PM/plan.
- **Tool inventory ambiguity:** Ticket says “all combat tools” — includes `start_combat`, `combat_attack`, `combat_end`, `combat_action`, and combat-relevant `cast_spell` / `fortune_spend`; `process_beat` is not a combat tool but **starts** the broken path A.
- **APP-027 overlap:** Fixing narration without engine validation still allows wrong ids if LLM calls tools directly; coordinate tickets to avoid duplicate work.
- **Second narrate pass in combat:** On partial tool success, LLM asked to “narrate honestly” — relies on model; less critical than paths that return pre-written hit fiction on total failure.
- **No session log replay:** Human/context “COMBAT_START with combat: null” not verified in-repo; trace matches architecture and spec problem statements.

## Raw notes

- `COMBAT_START` in user context = mechanical `action: "combat_start"` on successful `start_combat`, not an FSM step name (`combat_fsm.py` uses `COMBAT_ENCOUNTER`, `COMBAT_PC_ACTION`, etc.).
- `_combat_mechanical_brief` already formats `item.get("ok") is False` as `FAILED: {error}` for narrate pass — only when mechanical list reaches brief.
- Exploration failure pattern contrast: per-tool `TOOL FAILED` system message (`1986–1991`) vs combat inner loop (absent).
- `bridge.start_combat_from_trigger` returns `{ok: false, error: "combat already active"}` if combat exists (`bridge.py:304–306`).
- Default monster fallback `["grave-ghoul:1"]` in orchestrator (`1711`, `1909`) when specs empty.
- `system_prompt.py:222` and `tools.py:70` document ok:false policy — **not code-enforced** on trigger path.
