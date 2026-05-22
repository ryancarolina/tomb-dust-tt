# Implementation Plan: APP-022-hint-enterdungeon-on-failed-setphasedelve

**Status:** draft  
**backlog_ticket:** APP-022  
**ticket_path:** tmp/backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

When the LLM calls **`set_phase(phase="delve")`** and the engine returns **`ok: false`**, enrich the failure path in **`_llm_loop`** with a **code-owned hint** naming **`compass_exits`** then **`enter_dungeon(site_address)`**. No FSM, bridge, prompt, or APP-024 sanitizer changes.

Three injection channels (spec R1–R3), one shared string from a module helper:

1. **R1** — Add `"hint"` to the failed tool result dict (JSON in tool message + `_last_tool_results`).
2. **R2** — Append ` Hint: …` to the existing system `TOOL FAILED (set_phase): …` inject.
3. **R3** — On `all_failed and content` at **depth 0**, insert hint between `[Mechanics failed — …]` and APP-024-sanitized assistant prose.

**Optional R4:** When building the hint, call `bridge.compass_exits()`; if `ok` and `exits.below` non-empty, append `Below from current cell: {addresses}.` Failures or empty `below` → core hint only.

**Turn-scoped flag:** Reset `self._delve_entry_hint_this_turn = None` at `_llm_loop` depth 0. Set to the hint string on first triggered failure in the batch (sticky for R3 even if `_last_tool_results["set_phase"]` is overwritten later in the same turn). Clear semantics match APP-024’s `_entry_committed_this_turn` pattern.

**TurnTruth:** Hint text is code-owned system/player inject — **not** LLM verify path (same class as APP-024 refusal line).

**Out of scope:** `tools.py`, `system_prompt.py`, `bridge.py`, phase FSM, APP-077 footer, APP-028 combat strip.

---

## Code-path traces (current → planned)

### Flow A — Primary case: failed `set_phase(delve)` from preparation

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` | Exploration branch → `_llm_loop(messages)` | unchanged |
| 2 | `_llm_loop` | depth 0: reset `_last_tool_results`, `_entry_committed_this_turn`, snapshot `_exploration_pre_turn_mode` (`2364–2372`) | **Also** reset `_delve_entry_hint_this_turn = None` |
| 3 | same | Model returns `set_phase({"phase": "delve"})` + optional entry `content` | unchanged |
| 4 | same | `normalize_tool_args` — no `set_phase` normalizer; args pass through | unchanged |
| 5 | `_execute_tool` | `set_phase` → `bridge.set_phase` (`2548–2549`) | unchanged |
| 6 | `bridge.set_phase` | `{ok: false, error: "Cannot transition from preparation to delve"}` | unchanged |
| 7 | `_llm_loop` tool loop | `log_tool_call`; `_last_tool_results["set_phase"] = result`; generic system inject (`2442–2448`) | **After result, before log/store:** if `_should_delve_entry_hint(fn_name, args, result)`: build hint via `_delve_entry_tool_hint`; **R1** `result["hint"] = hint`; set `_delve_entry_hint_this_turn = hint`; **R2** append ` Hint: {hint}` to system content |
| 8 | same | Tool message `json.dumps(result)` (`2450–2454`) | Includes `"hint"` field when R1 fired |
| 9 | same | `all_failed and content` (`2462–2478`) | **R3:** if `depth == 0` and `_delve_entry_hint_this_turn` and not `failed_names & _COMBAT_TOOL_NAMES`: `return f"{prefix}\n\n{hint}\n\n{safe}"` else unchanged |
| 10 | `process_turn` | `_compose_exploration_narration` on final string (APP-024) | Hint already in string from R3; compose runs on content portion only — **do not** put hint inside sanitizer |

**Player-visible order (R3 path):** `[Mechanics failed — set_phase: …]` → APP-022 hint → APP-024 sanitized content → (APP-077 footer when landed).

---

### Flow B — Correct path contrast (no hint)

| Step | Current | Planned |
|------|---------|---------|
| `enter_dungeon(site_address)` ok | Sets `_entry_committed_this_turn`; phase advances via engine | unchanged; no hint |
| `set_phase(delve)` from `ingress` ok | `{ok: true}` | No trigger; no hint (T4) |

---

### Flow C — Negative: failed `set_phase(ingress)` or other phase

| Step | Current | Planned |
|------|---------|---------|
| `set_phase({"phase": "ingress"})` fails | Generic `TOOL FAILED` only | `_should_delve_entry_hint` → false; no R1–R3 (T3) |

**Trigger predicate** (all required):

```python
def _should_delve_entry_hint(fn_name: str, args: dict, result: dict) -> bool:
    return (
        fn_name == "set_phase"
        and str(args.get("phase", "")).strip().lower() == "delve"
        and not result.get("ok")
    )
```

Uses **post-`normalize_tool_args`** `args` (spec trigger table).

---

### Flow D — Partial success: fail `set_phase(delve)` + ok `enter_dungeon`

| Step | Current | Planned |
|------|---------|---------|
| Same batch | `all_failed = False`; loop recurses | R1/R2 still attach to failed `set_phase` result; `_delve_entry_hint_this_turn` set |
| Final return | Normal narration path, not `all_failed and content` short-circuit | **R3 not taken** — no player-visible hint banner (T5) |

---

### Flow E — Combat-tool batch suppresses R3

| Step | Current (L2474–2475) | Planned |
|------|---------------------|---------|
| `set_phase(delve)` fail + `start_combat` fail | Early `return prefix` only | unchanged — R3 suppressed; R1/R2 may still run for LLM transcript |

---

### Flow F — Recurse at depth ≥ 1 (not R3)

| Step | Current | Planned |
|------|---------|---------|
| depth 0 all tools fail, no `content` | Recurse `_llm_loop(..., depth + 1)` | R1/R2 at depth 0 still in transcript; R3 requires `depth == 0` (qa-spec-pass NOTE-6) |

---

## Task breakdown

### 1. Module helper — `app/gm/orchestrator.py` (~after `_SITE_ENTRY_REFUSAL_LINE`, L109)

#### 1.1 `_delve_entry_tool_hint(*, below_addresses: list[str] | None = None) -> str`

**Core (always):**

```text
Do not use set_phase to enter a site. Call compass_exits to list below addresses, then enter_dungeon(site_address). enter_dungeon advances preparation→ingress→delve automatically.
```

Implementation note: spec shows bold tool names in domain doc; player/system string may use plain names (match APP-024 refusal style — no markdown `**` required in inject). Tests use case-insensitive substring `compass_exits` / `enter_dungeon`.

**Optional suffix** when `below_addresses` truthy:

```text
Below from current cell: {comma-separated addresses}.
```

#### 1.2 `_should_delve_entry_hint(fn_name, args, result) -> bool`

Module-level predicate per Flow C trigger table.

#### 1.3 `_build_delve_entry_hint(orchestrator) -> str` (instance helper)

```python
def _build_delve_entry_hint(self) -> str:
    below: list[str] = []
    try:
        compass = self.bridge.compass_exits()
        if compass.get("ok"):
            for item in (compass.get("exits") or {}).get("below") or []:
                addr = (item.get("address") or "").strip()
                if addr:
                    below.append(addr)
    except Exception:
        pass  # R4: never fail hint build
    return _delve_entry_tool_hint(below_addresses=below or None)
```

Call once per triggered failure; reuse string for R1/R2/R3.

---

### 2. Turn-scoped state — `Orchestrator`

#### 2.1 `__init__`

Add: `self._delve_entry_hint_this_turn: str | None = None`

#### 2.2 `_llm_loop` depth-0 block (~L2364)

After existing resets:

```python
self._delve_entry_hint_this_turn = None
```

---

### 3. R1 + R2 — tool loop (~L2431–2454)

After `result = self._execute_tool(...)` / validation error result, **before** `log_tool_call`:

```python
if _should_delve_entry_hint(fn_name, args, result):
    hint = self._build_delve_entry_hint()
    result = {**result, "hint": hint}
    if self._delve_entry_hint_this_turn is None:
        self._delve_entry_hint_this_turn = hint
```

In the `else` branch (failure), extend system message:

```python
sys_content = (
    f"TOOL FAILED ({fn_name}): {json.dumps(result, default=str)}. "
    "You MUST narrate this failure honestly. Do NOT describe success."
)
if result.get("hint"):
    sys_content += f" Hint: {result['hint']}"
messages.append({"role": "system", "content": sys_content})
```

Ensure `log_tool_call` and `_last_tool_results[fn_name] = result` see the enriched dict (hint included).

---

### 4. R3 — `all_failed and content` block (~L2462–2478)

Replace return assembly:

```python
if all_failed and content:
    ...
    prefix = f"[Mechanics failed — {failures}]"
    failed_names = {...}
    if failed_names & _COMBAT_TOOL_NAMES:
        return prefix
    gate_active = self._exploration_gate_active(self._exploration_pre_turn_mode)
    safe = self._compose_exploration_narration(content, gate_active=gate_active)
    hint = self._delve_entry_hint_this_turn
    if depth == 0 and hint:
        return f"{prefix}\n\n{hint}\n\n{safe}"
    return f"{prefix}\n\n{safe}"
```

**Do not** inject R3 when `depth != 0`. **Do not** duplicate hint in `_compose_exploration_narration`.

---

### 5. Tests — `app/tests/test_exploration_set_phase_delve_hint.py` (new)

Reuse from `test_exploration_site_entry_gate.py`:

- `_tool_call`, `_patch_llm_sequence`, `_surface_exploration_orchestrator`, `_patch_party_mode`
- `orchestrator` fixture from `app/tests/conftest.py`

**Shared setup for failure cases:**

```python
def _mock_set_phase_delve_fail(orchestrator, monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "_execute_tool",
        lambda name, args: (
            {"ok": False, "error": "Cannot transition from preparation to delve"}
            if name == "set_phase"
            else {"ok": False, "error": f"unexpected {name}"}
        ),
    )
```

#### 5.1 Test matrix (spec T1–T6)

| ID | Test name | Setup | Assert |
|----|-----------|-------|--------|
| **T1** | `test_failed_set_phase_delve_tool_result_has_hint` | Single-tool turn; call `_llm_loop` or `process_turn` with mocked LLM | After loop, `orchestrator._last_tool_results["set_phase"]["hint"]` contains `compass_exits` and `enter_dungeon` (case-insensitive) |
| **T2** | `test_all_failed_content_includes_player_hint` | Mock LLM: `content=ENTRY_PROSE` + failing `set_phase(delve)` only; surface mode | Return has `[Mechanics failed`, `compass_exits`, `enter_dungeon`; entry markers stripped (APP-024) |
| **T3** | `test_failed_set_phase_ingress_no_hint` | Mock failing `set_phase({"phase": "ingress"})` | No `"hint"` key; output lacks delve-entry helper phrases |
| **T4** | `test_successful_set_phase_delve_no_hint` | Mock/stub `{ok: true}` for `set_phase(delve)` from legal phase | No `"hint"` on result |
| **T5** | `test_partial_success_enter_dungeon_no_player_hint` | Batch: fail `set_phase(delve)` + ok `enter_dungeon`; second LLM response with benign prose | Failed `set_phase` may have R1 hint in `_last_tool_results`; final narration **lacks** R3 banner pattern with hint between prefix and content (or not `[Mechanics failed` at all) |
| **T6** | `test_system_tool_failed_message_includes_hint` | Inspect `messages` after one `_llm_loop` iteration | System role entry contains `TOOL FAILED (set_phase)` and `compass_exits` |

**T6 implementation pattern:** Build minimal `messages` list; patch `chat_completion` to return one tool-call response; optionally wrap `_llm_loop` or spy on appended messages via list mutation (append to shared `messages` in test).

**Optional R4 test (non-blocking):** If `compass_exits` returns `below` addresses on test hub cell, assert hint contains `Below from current cell`. Skip if setup lacks grid below — core hint still satisfies AC.

#### 5.2 Commands

```bash
cd app && python -m pytest tests/test_exploration_set_phase_delve_hint.py -q
cd app && python -m pytest tests/test_exploration_site_entry_gate.py -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q
```

---

### 6. Domain spec sync on close — `tmp/app-exploration-delve-spec.md`

On `release APP-022 --done`:

1. Mark checklist open-work item `[x]`.
2. Changelog: APP-022 done — `_delve_entry_tool_hint`, R1–R3, `test_exploration_set_phase_delve_hint.py`.
3. Update orchestrator spec open-work list in `tmp/app-llm-orchestrator-spec.md` (coordination — not Expected files but noted in qa-spec-pass).

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **R1** | `"hint"` on failed tool JSON | `_llm_loop` tool loop | T1 |
| **R2** | System `TOOL FAILED` append | `_llm_loop` else branch | T6 |
| **R3** | Player banner hint at depth 0 | `all_failed and content` | T2 |
| **R4** | Optional below suffix | `_build_delve_entry_hint` | optional / manual |
| **R5** | No hint on wrong phase / success | trigger predicate | T3, T4 |
| — | Partial success: no R3 | `all_failed` false | T5 |
| — | APP-024 regression | compose unchanged | T2 + site_entry_gate suite |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/orchestrator.py` | `_delve_entry_tool_hint`, `_should_delve_entry_hint`, `_build_delve_entry_hint`; `_delve_entry_hint_this_turn`; R1–R3 in `_llm_loop` |
| `app/tests/test_exploration_set_phase_delve_hint.py` | **New** — T1–T6 |

**Not in Expected files (close-time only):** `tmp/app-exploration-delve-spec.md`, `tmp/app-llm-orchestrator-spec.md` checklist/changelog.

---

## Rollback

Revert `orchestrator.py` + delete test module restores generic `TOOL FAILED` with no delve-entry hints. No feature flags.

---

## Open questions

- **None blocking.** Hint prose not pinned as exported constant — substring tests per spec.
- **Exact bold/markdown in hint:** Use plain tool names in inject strings for consistency with system messages; domain spec may keep markdown for docs only.
- **Session claim:** confirm `tmp/.active-ticket.json` includes APP-022 before `app/` edits (`impl-check APP-022`).
