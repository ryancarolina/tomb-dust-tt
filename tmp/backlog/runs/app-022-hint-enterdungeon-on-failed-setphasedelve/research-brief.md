# Research Brief: APP-022-hint-enterdungeon-on-failed-setphasedelve

**Date:** 2026-05-22  
**Question:** Where should the orchestrator inject `enter_dungeon` + `compass_exits` guidance when `set_phase(delve)` fails, and what failure paths exist today?

**backlog_ticket:** APP-022  
**ticket_path:** tmp/backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) already owns delve entry rules (`enter_dungeon` not `set_phase(delve)` alone), documents the log problem (`set_phase(delve)` rejected from `preparation`), and lists APP-022 as open work. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Exploration & delve** maps to that spec and `play/tomb_gm/services/site.py` / `world.py`. Ticket **Expected files** (`app/gm/orchestrator.py`) ⊆ registered owner. Cross-cutting LLM loop behavior is noted in [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) (APP-022 listed as open); that is coordination, not a missing domain owner.

## Summary

When the LLM calls `set_phase(phase="delve")` from **`preparation`** (the common log failure), the engine rejects the transition — only `preparation→ingress` is legal; **`enter_dungeon`** is the correct entry path and internally runs `advance_phase_for_dungeon_entry` (`preparation→ingress→delve`). Today the orchestrator surfaces the raw engine error (`Cannot transition from preparation to delve`) via a generic `TOOL FAILED` system message and optional `[Mechanics failed — …]` banner. **No code-owned hint** names `compass_exits` or `enter_dungeon` on this failure path.

Prompt/schema guidance already exists (`tools.py` set_phase description, `system_prompt.py` delve rules, APP-021 `enter_dungeon(site_address)` schema) but is **not enforced** when the wrong tool fails. `_build_exploration_context` / `build_state_context` may already list **Below:** addresses from compass data — hints can reinforce tool calls rather than duplicate state.

APP-022 is **hints only** (per APP-024 research): it does not block site-entry fiction (APP-024 sanitizer) or replace exploration footers (APP-077). Implementation should live in `orchestrator.py` — likely enriching failed `set_phase(delve)` tool results and/or the `all_failed` early-return prefix when that tool appears in `_last_tool_results`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Exploration turn | `app/gm/orchestrator.py` `process_turn` | Surface path → `_llm_loop` → `_compose_exploration_narration` → `_emit_narration` |
| LLM tool loop | `app/gm/orchestrator.py` `_llm_loop` | Per-failure system inject; `all_failed and content` early return with APP-024 sanitize |
| Tool dispatch | `app/gm/orchestrator.py` `_execute_tool` | `set_phase` → `bridge.set_phase`; no special-case hint today |
| Bridge phase | `app/gm/bridge.py` `set_phase` | Catches `ExtractionError` → `{ok: false, error: str(exc)}` |
| Bridge entry | `app/gm/bridge.py` `enter_dungeon` | Resolves site → `ExplorationService.enter_site` → `advance_phase_for_dungeon_entry` |
| Bridge compass | `app/gm/bridge.py` `compass_exits` | Returns `{ok: true, address, exits}`; `exits.below` lists UG child addresses |
| Engine FSM | `play/tomb_gm/services/extraction.py` | `PHASE_TRANSITIONS`; `set_phase`; `advance_phase_for_dungeon_entry` |
| Compass data | `play/tomb_gm/services/exploration.py` `compass_exits` | Surface cells: N/S/E/W + `below` from `childAddresses` |
| LLM context | `app/gm/orchestrator.py` `_build_exploration_context`, `app/gm/context.py` | Compass already rendered as `Below: {name} ({address})` in state context |
| Tool schemas | `app/gm/tools.py` | `set_phase` warns against dungeon entry; `enter_dungeon` references `compass_exits` |
| Prompt rules | `app/gm/system_prompt.py` L235–238 | Never `set_phase` to enter; use `compass_exits` then `enter_dungeon` |
| Site-entry gate | `app/gm/orchestrator.py` APP-024 | `_SITE_ENTRY_REFUSAL_LINE` mentions `enter_dungeon`/`site_enter` on fiction strip — **not** tied to `set_phase` failure |
| Related tickets | APP-024 (fiction gate), APP-021 (enter_dungeon arg), APP-077 (footer), APP-028 (all_failed pattern) | APP-022 complements APP-024; no overlap with APP-034 logging |

## Code-path traces

### A — Failed `set_phase(delve)` from preparation (primary log case)

1. **Entry:** Exploration `process_turn` → `_llm_loop(messages, depth=0)` (`orchestrator.py:1103`, `2358+`).
2. **Depth 0 init:** Resets `_last_tool_results`, `_entry_committed_this_turn`, snapshots `_exploration_pre_turn_mode` (`2364–2372`).
3. **Model:** Returns `tool_calls` including `set_phase` with `{"phase": "delve"}` (often alongside assistant `content` describing entry).
4. **Normalize:** `set_phase` has no APP-080 normalizer — args pass through as-is (`tool_args.py:156–157`).
5. **Dispatch:** `_execute_tool("set_phase", args)` → `bridge.set_phase(phase="delve")` (`2548–2549`).
6. **Engine:** `extraction.set_phase` — current `preparation`, allowed `{ingress}` only → raises `ExtractionError("Cannot transition from preparation to delve")` (`extraction.py:48–51`).
7. **Bridge:** Exception → `{ok: false, error: "Cannot transition from preparation to delve"}` (`bridge.py:561–566`).
8. **Loop handling:** Logs tool call; stores in `_last_tool_results["set_phase"]`; `all_failed` stays true (`2432–2437`).
9. **System inject:** Generic line only — `TOOL FAILED (set_phase): {"ok": false, "error": "..."}. You MUST narrate this failure honestly. Do NOT describe success.` (`2443–2448`) — **no enter_dungeon / compass_exits hint**.
10. **Recursion or early exit:** If assistant had pre-tool `content` and all tools failed → `[Mechanics failed — set_phase: Cannot transition…]\n\n{sanitized content}` (`2462–2478`). Hint absent from prefix.
11. **Player state:** `party.mode` still `surface`; phase still `preparation`; no dungeon entry.

### B — Correct path contrast: `enter_dungeon` (what hint should steer toward)

1. **Dispatch:** `_execute_tool("enter_dungeon", {"site_address": "32-C-UG-1"})` → `bridge.enter_dungeon` (`2560–2561`).
2. **Resolve:** `resolve_site_address` → `ExplorationService.enter_site` sets `mode=dungeon` (`bridge.py:648–657`, `exploration.py:376–398`).
3. **Phase advance:** `advance_phase_for_dungeon_entry` — if `preparation`, calls `set_phase(ingress)` then `set_phase(delve)` (`extraction.py:65–79`).
4. **Turn flag:** Successful entry sets `_entry_committed_this_turn = True` (`2434–2435`).
5. **Narration:** APP-024 gate bypassed; entry fiction allowed.

### C — `compass_exits` (second hint target)

1. **Tool path:** `_execute_tool("compass_exits")` → `bridge.compass_exits()` → `{ok: true, address, exits}` (`2558–2559`, `bridge.py:616–626`).
2. **Data shape:** `exits["below"]` = list of `{address, displayName}` for UG children (`exploration.py:362–368`).
3. **Context path (no tool call):** `_build_exploration_context` embeds same compass into exploration dict; `build_state_context` renders **Below:** lines (`orchestrator.py:974–979`, `context.py:99–104`).
4. **Gap:** Failed `set_phase(delve)` does not suggest calling `compass_exits` even when below list is empty in context (e.g. layer-stack cell returns `{}` from `compass_exits`).

### D — Other `set_phase(delve)` failure modes (secondary)

| Current phase | `set_phase(delve)` | Notes |
|---------------|-------------------|-------|
| `preparation` | **Fails** | Primary APP-022 case |
| `ingress` | Succeeds | Legal transition |
| `delve` | Succeeds (no-op update) | Same phase |
| `extract` | Succeeds | Re-enter delve allowed |
| `aftermath` | **Fails** | Allowed: `{preparation}` only |

Ticket AC says **failed `set_phase(delve)`** generally — PM should confirm whether hint applies to all failures (e.g. `aftermath→delve`) or only the **preparation skip** anti-pattern.

### E — Partial / multi-tool turns

1. Model calls `set_phase(delve)` (fail) + `enter_dungeon` (success) same batch → `all_failed = False`; loop continues; hint less critical.
2. Model calls `set_phase(delve)` only at depth 0, fails, recurses at depth 1 — enriched tool result at depth 0 still visible in transcript for retry.
3. `all_failed and content` at depth 0 with only failed `set_phase` — player sees failure banner; **best player-visible hint injection point** alongside APP-024 sanitize.

## Existing specs & docs

- **Ticket:** Failed `set_phase(delve)` should guide correct tool usage; AC: hint `enter_dungeon` + `compass_exits`.
- **Domain spec:** Delve play — enter via `enter_dungeon`, not `set_phase(delve)` alone; Problem log bullet for preparation rejection; APP-022 in open checklist.
- **Orchestrator spec:** APP-022 listed under open work; tool arg normalization table includes `enter_dungeon`.
- **APP-021 (done):** `site_address` primary; orchestrator maps `site_id` alias before bridge.
- **APP-024 (done):** Site-entry fiction gate; human test plan notes APP-022 hints may appear in failure banner — separate concern from fiction strip.
- **APP-077 (open):** Code-owned exploration footer — compose order after APP-024; hints should not fight footer append.

## Tests & commands

```bash
# Engine: phase FSM rejects preparation→delve
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve -q

# Engine: enter_dungeon advances phase correctly
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q

# App: site-entry gate (mock LLM); no set_phase hint coverage
python -m pytest app/tests/test_exploration_site_entry_gate.py -q

# Full app tests — no APP-022 cases
python -m pytest app/tests/ -q
```

**Test gap:** No `app/tests/*` asserts hint text on failed `set_phase(delve)`. PM should require mock-LLM test (pattern in `test_exploration_site_entry_gate.py`: `_patch_llm_sequence`, `_surface_exploration_orchestrator`) asserting:

- Tool result or player-visible output mentions `enter_dungeon` and `compass_exits` when `set_phase(delve)` returns `ok: false`.
- Hint does **not** fire on failed `set_phase(ingress)` or successful `set_phase` calls.
- Hint does not regress APP-024 refusal/sanitize on same turn.

## Risks & unknowns

- **Audience:** Hint for **LLM only** (tool payload / system message) vs **player-visible** (failure banner / code-owned suffix)? APP-024 human test implies player may see hints in `[Mechanics failed — …]` — PM should pick one or both; dual injection is safest for recovery.
- **Trigger narrowness:** Match `fn_name == "set_phase"` and `args.get("phase", "").lower() == "delve"` and `not result.get("ok")` — avoid hinting on unrelated tool failures in same turn.
- **Dynamic vs static hint:** Static text is simple; optional `bridge.compass_exits()` in hint builder could list `below` addresses when on surface — duplicates context when compass already in prompt; useful when context build failed or cell has no below in context.
- **Out of scope per ticket:** `tools.py`, `system_prompt.py`, bridge/engine phase rules — Expected files is orchestrator only; schema/prompt already document correct tools.
- **APP-024 interaction:** `_SITE_ENTRY_REFUSAL_LINE` already names `enter_dungeon` when entry fiction stripped — orthogonal to tool-failure hint; avoid duplicate prose if both fire same turn.
- **Creation guard:** `_llm_loop` blocked during `creation.active` — set_phase hint irrelevant at desk; no creation drift interaction.
- **Session evidence:** Domain spec cites log failures; session JSONL gitignored — not replayed locally.

## Raw notes

### Key line references

| Symbol | Location | Role |
|--------|----------|------|
| `_llm_loop` failure inject | `orchestrator.py:2443–2448` | Generic `TOOL FAILED` — extension point for hint |
| `all_failed and content` | `orchestrator.py:2462–2478` | Player-visible failure banner + APP-024 sanitize |
| `_execute_tool` set_phase | `orchestrator.py:2548–2549` | Passthrough to bridge |
| `PHASE_TRANSITIONS` | `extraction.py:12–17` | `preparation` → `{ingress}` only |
| `advance_phase_for_dungeon_entry` | `extraction.py:65–84` | Correct phase walk on dungeon entry |
| `set_phase` tool description | `tools.py:294–299` | Already says use `enter_dungeon` instead |
| `_SITE_ENTRY_REFUSAL_LINE` | `orchestrator.py:109–111` | APP-024; mentions enter tools, not compass |

### Recommended implementation axes (for PM/plan — not spec)

1. **Helper** `_delve_entry_tool_hint(*, include_below: bool = False) -> str` — static or compass-backed string naming `compass_exits` then `enter_dungeon(site_address)`.
2. **Enrich tool result** in `_llm_loop` after failed `set_phase` when `phase.lower() == "delve"`: add `"hint": "..."` to dict before JSON serialize to tool message (LLM-visible, logged).
3. **Extend system `TOOL FAILED` message** with same hint (stronger model steering on recurse).
4. **Optional player-visible:** Append hint to `prefix` in `all_failed and content` when `"set_phase" in failed_names` and failed phase was `delve`.
5. **Tests:** Mock LLM single-tool `set_phase(delve)` failure; assert hint substrings in returned narration and/or `_last_tool_results["set_phase"]["hint"]`.

### Related backlog

| Ticket | Relationship |
|--------|--------------|
| APP-024 | Fiction gate — sibling; refusal line overlaps enter_dungeon mention |
| APP-021 | enter_dungeon arg naming — hint should use `site_address` |
| APP-077 | Footer compose — hints precede or append outside footer helper |
| APP-028 | Shared `all_failed and content` pattern — hints add guidance, not content strip |
| APP-063 | Map UX may surface ingress later — not blocking APP-022 |
