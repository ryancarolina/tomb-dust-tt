# Spec — App LLM Orchestrator

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/orchestrator.py`, `tools.py`, `context.py`, `system_prompt.py`, `openrouter.py`, `choice_memory.py`

---

## Spec

Turn loop: **player input → context → LLM (+ tools) → narration → UI/TTS**.

### Mechanical truth (non-negotiable)

**Code state leads narration.** Player must not see outcomes (PRE_DELVE, combat hits, site entry, loot) unless the matching bridge/tool call returned `"ok": true`.

### Modes

| Mode | When | Behavior |
|------|------|----------|
| Creation | `creation.active` | Only creation handlers — no exploration tool loop |
| Combat | `combat.active` or engine combat | `combat_fsm` + combat tools |
| Exploration | default | `status`/`check`/`suggest` context + full tool set |

### Tools (`tools.py`)

Schemas must match `bridge.py` method signatures. When adding a tool:

1. Add bridge method (gamebridge spec).
2. Add tool schema here.
3. Add handler in `orchestrator._dispatch_tool`.
4. Update `system_prompt.py` usage rules.
5. Update this spec checklist.

---

## Task checklist

- [x] `process_turn` with creation / combat / exploration branches
- [x] Tool dispatch to GameBridge
- [x] LLM loop with depth limit for tool chains
- [x] `build_state_context` from status + recap + inventory
- [ ] Block exploration `_llm_loop` during creation (character-creation spec)
- [ ] On all-tools-failed: no success fiction (combat-play spec)
- [ ] Delve: prefer `enter_dungeon` over `set_phase(delve)` (exploration-delve spec)
- [ ] **Transcript sanitize** — no orphan `tool` messages without preceding `tool_calls`
- [ ] **400 retry** — on malformed transcript, repair/truncate history and retry once
- [ ] **SQLite threading** — single connection per process or thread-local `GameBridge`
- [ ] Log full tool-call chain on API errors (redact keys)

---

## Problem (from logs)

- Google 400: *Tool-call assistant message produced no valid function calls but is followed by tool result messages*
- SQLite cross-thread error (2026-05-18)

---

## Tests

- Mock LLM tests in `app/tests/test_orchestrator.py` (when added).
- Session JSONL: every tool call logged with result.

---

## File map

| File | Role |
|------|------|
| `orchestrator.py` | Turn loop, creation/combat branches |
| `tools.py` | OpenAI function schemas |
| `context.py` | State block for LLM |
| `system_prompt.py` | GM persona + rules |
| `openrouter.py` | API client, history sanitize |
| `choice_memory.py` | Creation choice recall |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged mechanical-truth + llm-transcript-resilience content |
