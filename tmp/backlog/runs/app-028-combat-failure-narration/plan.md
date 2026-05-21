# Implementation Plan: APP-028-combat-failure-narration

**Status:** draft  
**backlog_ticket:** APP-028  
**ticket_path:** [tmp/backlog/app-028-combat-tool-failure-narration.md](../../app-028-combat-tool-failure-narration.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Combat tool failures are enforced in three orchestrator choke points (spec R1–R4):

1. **R1 — Beat-trigger propagation:** `_handle_combat_trigger` returns a canonical failure string; `_execute_tool("process_beat")` stores it; `_llm_loop` short-circuits **before** `all_failed` + content handling — fixes grave-ghoul / `combat: null`.
2. **R2 — Exploration `all_failed` strip:** `_llm_loop` returns `[Mechanics failed — …]` **only** (no `\n\n{content}`); per-tool `TOOL FAILED` system injection **unchanged** when loop continues.
3. **R3/R4 — Combat inner loop:** `_combat_llm_loop_inner` mirrors R2 strip + adds exploration-equivalent `TOOL FAILED` injection on partial failure before tool-result messages.

**Out of scope:** engine `process_beat` contract, `pending_start` unification (R7 optional), APP-027 validation, APP-026 gating, domain spec changelog until impl close.

**Files (ticket Expected files only):**

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | R1–R4, R8 logging |
| `app/tests/test_combat_failure_narration.py` | **new** T1–T11 |
| `tmp/app-combat-play-spec.md` | checklist + changelog on **close** (no drift during impl) |

---

## Code-path traces (current → planned)

### Flow A — Grave-ghoul beat trigger (R1) — **primary bug**

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` | Exploration path → `_llm_loop(messages)` (~813) | unchanged |
| 2 | `orchestrator.py:_llm_loop` | `chat_completion` → assistant `content` + `process_beat` tool call | unchanged |
| 3 | `orchestrator.py:_execute_tool` | `process_beat` → `bridge.process_beat` → `_handle_combat_trigger(result)` → return engine result (**ok: true** + `combat_trigger`) | After trigger: if failure str, set `self._beat_combat_start_failure` |
| 4 | `orchestrator.py:_handle_combat_trigger` | `-> None`; on `not start.get("ok")`: **no branch** (1912–1917) | `-> str \| None`; on failure: `combat.active = False`; return `[Mechanics failed — combat start: {error}]\n\nCombat could not begin.`; on success: existing `active=True`, `run_combat_monster_turns()`; else `None` |
| 5 | `orchestrator.py:_llm_loop` | After tool batch: `all_failed` may append `content` (1999–2006) | **Before** `all_failed` block: if `_beat_combat_start_failure`: `log_error`, clear flag, **return failure str** (no content, no `depth+1`) |
| 6 | `bridge.py:start_combat_from_trigger` | `{ok: false, error: …}` on missing JSON / no roster | unchanged (mock in tests) |
| 7 | `context.py:build_state_context` | No combat block when `status.combat` null | unchanged — player text is short-circuit, not second LLM pass |

**Dual-channel (SPEC-004):** Tool-role JSON for `process_beat` stays `ok: true` with `combat_trigger` in `mechanical_summary`. **Player channel** = R1 short-circuit return. T2 asserts player return, not tool JSON.

**Non-goal:** Do not call `run_combat_monster_turns()` on failed start (current code already skips — keep).

```
process_turn
  └─ _llm_loop(depth=0)
       ├─ chat_completion #1 → content + tool_calls[process_beat]
       ├─ _execute_tool(process_beat)
       │    ├─ bridge.process_beat → ok:true, combat_trigger in summary
       │    └─ _handle_combat_trigger → str (failure) | None
       ├─ [NEW] if _beat_combat_start_failure → return (END)
       ├─ all_failed handling (R2)
       └─ _llm_loop(depth+1)  # NOT reached on R1 short-circuit
```

### Flow B — Exploration combat tools + `all_failed` (R2, R5)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_execute_tool` | Routes `start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend` to bridge (2054–2071) | unchanged |
| 2 | `orchestrator.py:_llm_loop` tool loop | On `not result.get("ok")`: inject `TOOL FAILED ({fn_name}): …` system msg (1986–1992) | **unchanged** |
| 3 | same | `if all_failed and content:` return `prefix\n\n{content}` (1999–2006) | Return **`prefix` only**; `log_error("llm_loop", …)` notes strip (R8) |
| 4 | same | `if all_failed and depth >= 2:` user “narration only” directive + recurse (2008–2015) | unchanged — applies when no early return (e.g. no pre-tool content) |
| 5 | `bridge.py` | Engine `{ok: false, error: …}` | mocked in T3–T7 |

**Banned substrings (tests):** initiative / enemies charge (T3); damage / hit (T4); combat ended / victory (T5); spell damage / effect (T6); Fortune spent / reroll (T7).

### Flow C — Combat inner loop (R3, R4)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_combat_turn` | PC turn → `_combat_llm_loop` → `_combat_llm_loop_inner` (1759–1761, 1798) | unchanged |
| 2 | `orchestrator.py:_combat_llm_loop_inner` | Tool loop: wrong name → synthetic `{ok: false}` (1837–1838); else `_execute_combat_action` (1840) | On `not result.get("ok")`: **inject** `TOOL FAILED` system message (mirror 1986–1992) **before** tool result append (R4) |
| 3 | same | `if all_failed:` return `prefix\n\n{content or fallback}` (1848–1854) | Return **`prefix` only**; if `failures` empty, optional `\n\nYour action did not resolve.` — **never** model `content` (R3) |
| 4 | same | Partial success → mechanical brief + second `chat_completion` (1867–1880) | unchanged |
| 5 | `orchestrator.py:_combat_mechanical_brief` | `FAILED:` rows for `ok: false` (1700–1701) | unchanged |

### Flow D — Reference good path (do not regress)

| Step | File:symbol | Current (L) | Note |
|------|-------------|-------------|------|
| 1 | `orchestrator.py:_combat_turn` | `pending_start` failure copy (1710–1717) | Canonical shape for R1 — **no edit required** |
| 2 | `orchestrator.py:_handle_combat_trigger` | Success branch (1913–1917) | Preserve |

### Flow E — Instance state (R1)

| Field | Where | Lifecycle |
|-------|-------|-----------|
| `_beat_combat_start_failure: str \| None` | `Orchestrator.__init__` (default `None`) | Set in `_execute_tool` after `process_beat` + trigger; cleared on R1 short-circuit return in `_llm_loop`; optionally clear at `_llm_loop` `depth == 0` start alongside `_last_tool_results` reset |

**Same-batch ordering (QA adversarial note):** Short-circuit runs after **full** tool batch. Rare `process_beat` + `combat_attack` in one turn may still run attack before return — acceptable for APP-028; grave-ghoul path is beat-only.

---

## Task breakdown

### 1. R1 — `_handle_combat_trigger` + propagation — `app/gm/orchestrator.py`

#### 1.1 Signature and failure branch — **L1906–1917**

**Current:**

```python
def _handle_combat_trigger(self, beat_result: dict) -> None:
    ...
    start = self.bridge.start_combat_from_trigger(specs)
    if start.get("ok"):
        self.combat.active = True
        ...
        self.bridge.run_combat_monster_turns()
```

**Planned:**

```python
def _handle_combat_trigger(self, beat_result: dict) -> str | None:
    for item in beat_result.get("mechanical_summary") or []:
        if item.get("action") != "combat_trigger":
            continue
        specs = item.get("monster_specs") or ["grave-ghoul:1"]
        if self._combat_active_in_db():
            continue
        start = self.bridge.start_combat_from_trigger(specs)
        if not start.get("ok"):
            self.combat.active = False
            err = start.get("error", start)
            return (
                f"[Mechanics failed — combat start: {err}]\n\n"
                "Combat could not begin."
            )
        self.combat.active = True
        self.combat.step = "COMBAT_PC_ACTION"
        self.combat.order_narrated = False
        self.bridge.run_combat_monster_turns()
    return None
```

- Use same `\n\n` between prefix and second line as `pending_start` branch (1717).
- Context label **`combat start`** (not `start_combat`) per domain spec.

#### 1.2 `_execute_tool("process_beat")` — **L2040–2043**

**Planned:**

```python
elif name == "process_beat":
    result = self.bridge.process_beat(**args)
    failure = self._handle_combat_trigger(result)
    if failure:
        self._beat_combat_start_failure = failure
    return result
```

#### 1.3 `_llm_loop` short-circuit — **after L1997, before L1999**

**Planned (insert):**

```python
beat_failure = getattr(self, "_beat_combat_start_failure", None)
if beat_failure:
    self._beat_combat_start_failure = None
    log_error("llm_loop", f"beat combat start failed: {beat_failure[:120]}")
    return beat_failure
```

- Does **not** append assistant `content`.
- Does **not** increment depth / second `chat_completion`.
- T2: `chat_completion` call count == 1.

#### 1.4 `__init__` — **~L107–111**

Add: `self._beat_combat_start_failure: str | None = None`

Optionally reset at `_llm_loop` `depth == 0` with `_last_tool_results` for hygiene.

---

### 2. R2 — Exploration `all_failed` content strip — **L1999–2006**

**Current:**

```python
if all_failed and content:
    ...
    return f"[Mechanics failed — {failures}]\n\n{content}"
```

**Planned:**

```python
if all_failed and content:
    log_error("llm_loop", f"all tools failed at depth {depth}, stripping assistant content")
    failures = "; ".join(...)
    return f"[Mechanics failed — {failures}]"
```

- When `all_failed` and **no** `content`, existing `depth >= 2` retry path remains.
- Per-tool `TOOL FAILED` injection (1986–1992) unchanged for partial-failure / retry turns.

**Optional DRY:** `_format_mechanics_failed_prefix(tool_results: dict) -> str` shared with combat inner loop — only if it reduces duplication without new module.

---

### 3. R3 + R4 — `_combat_llm_loop_inner` — **L1831–1854**

#### 3.1 R4 — TOOL FAILED injection in tool loop

After computing `result`, before `messages.append({"role": "tool", ...})`:

```python
if not result.get("ok"):
    messages.append({
        "role": "system",
        "content": (
            f"TOOL FAILED ({fn_name}): {json.dumps(result, default=str)}. "
            "You MUST narrate this failure honestly. Do NOT describe success."
        ),
    })
```

- For wrong-tool branch, `fn_name` is the **requested** tool (e.g. `start_combat`) — matches exploration pattern.

#### 3.2 R3 — `all_failed` return

**Planned:**

```python
if all_failed:
    failures = "; ".join(...)
    prefix = f"[Mechanics failed — {failures}]" if failures else "[Mechanics failed — combat_action: unknown failure]"
    log_error("combat_llm_loop", f"all tools failed at depth {depth}, stripping assistant content")
    if not failures:
        return f"{prefix}\n\nYour action did not resolve."
    return prefix
```

- **Never** append `content` from the same turn.
- T8: assert banned hit-fiction substring absent.
- T10: partial failure → `all_failed` false → loop continues to narrate pass; assert system `TOOL FAILED (combat_action)` appears **before** matching `role: tool` entry in `messages`.

---

### 4. R8 — Logging

| Event | `log_error` context | Payload hint |
|-------|---------------------|--------------|
| R1 short-circuit | `llm_loop` | truncated failure string |
| R2 content strip | `llm_loop` | depth + "stripping assistant content" |
| R3 content strip | `combat_llm_loop` | depth + strip note |

T11 (optional): `monkeypatch` `gm.orchestrator.log_error` or `caplog` — assert call on R1 or R2 path.

---

### 5. Domain spec on close — `tmp/app-combat-play-spec.md`

After pytest green:

- Mark task checklist **APP-028** done.
- Append changelog: implementation date + summary.
- Remove/open-work pointer if applicable.

No spec edits during impl unless behavior discovery forces PM sync (unlikely — qa-spec PASS).

---

## Test plan — `app/tests/test_combat_failure_narration.py`

**Run:**

```bash
python -m pytest app/tests/test_combat_failure_narration.py -q
python -m pytest play/tomb_gm/tests/test_combat*.py play/tomb_gm/tests/test_combat_beat_trigger.py -q
```

**Fixtures:** `orchestrator` from `conftest.py` (isolated workspace). Patch **`gm.orchestrator.chat_completion`** (not only `create_client`) for LLM loop tests.

**Shared helpers (module-local):**

```python
def _tool_call(name: str, args: dict, *, call_id: str = "call_1") -> list:
    """OpenAI-style tool_calls fragment for chat_completion mock."""

def _mock_chat_completion_once(monkeypatch, *, content: str, tool_name: str, tool_args: dict):
    """Single chat_completion return with one tool call; count calls via list wrapper."""

def _mock_bridge_tool(monkeypatch, orchestrator, name: str, result: dict):
    """Patch orchestrator.bridge.<method> or _execute_tool for isolated tool result."""
```

**Preconditions for loop tests:** `orchestrator.creation.active == False`; `orchestrator.combat.active == False`; `orchestrator.bridge.status()["combat"]` is null.

| ID | Test name (suggested) | Setup | Assertions |
|----|----------------------|-------|------------|
| **T1** | `test_handle_combat_trigger_returns_failure_string` | `beat_result = {"mechanical_summary": [{"action": "combat_trigger", "monster_specs": ["grave-ghoul:1"]}]}`; `monkeypatch` `bridge.start_combat_from_trigger` → `{ok: False, error: "monster JSON not found: grave-ghoul"}`; `monkeypatch` `_combat_active_in_db` → False | Return == `[Mechanics failed — combat start: monster JSON not found: grave-ghoul]\n\nCombat could not begin.`; `orchestrator.combat.active is False` |
| **T2** | `test_beat_trigger_e2e_llm_loop_short_circuits` | `_mock_chat_completion_once` with `content="Ghouls leap from the crypt."` + `process_beat` `{}`; `bridge.process_beat` → `{ok: True, mechanical_summary: [{action: combat_trigger, …}]}`; `start_combat_from_trigger` → ok false; minimal `messages` seed | `_llm_loop` return == T1 shape; `"Ghouls"` not in return; `chat_completion` call count **1**; `status()["combat"]` is None |
| **T3** | `test_llm_loop_all_failed_strips_content[start_combat]` | One tool `start_combat`; bridge → `{ok: False, error: "monster JSON not found: hollow-knight"}`; content mentions initiative / charge | Return starts with `[Mechanics failed — start_combat:`; banned substrings absent; no `\n\n` + fiction after prefix |
| **T4** | `test_llm_loop_all_failed_strips_content[combat_attack]` | `error: "attacker not in combat"`; content describes damage/hit | Prefix only; banned hit/damage words |
| **T5** | `test_llm_loop_all_failed_strips_content[combat_end]` | `error: "no active combat"`; content claims victory / combat ended | Prefix only |
| **T6** | `test_llm_loop_all_failed_strips_content[cast_spell]` | `error: "not in combat"`; content describes spell effect | Prefix only |
| **T7** | `test_llm_loop_all_failed_strips_content[fortune_spend]` | `error: "no Fortune remaining"`; content claims Fortune spent | Prefix only |
| **T8** | `test_combat_inner_all_failed_strips_content` | Call `_combat_llm_loop_inner` directly; mock `chat_completion` with hit fiction + failing `combat_action` | `[Mechanics failed` in return; fiction substring absent; no second `\n\n` model paragraph |
| **T9** | `test_combat_inner_wrong_tool_failure` | Inner loop tool name `start_combat` (not `combat_action`) | Return has `[Mechanics failed`; no hit narration |
| **T10** | `test_combat_inner_partial_failure_injects_tool_failed` | Two tool calls in one response: first `combat_action` ok false, second ok true **or** depth-0 fail + depth-1 retry mock | In captured `messages`, index of system `TOOL FAILED (combat_action)` < index of corresponding `role: tool`; not full `all_failed` short-circuit |
| **T11** | `test_all_failed_or_beat_failure_logs` _(optional)_ | T2 or T3 path with `log_error` spy | At least one `log_error` with context `llm_loop` |

**Parametrize T3–T7:** `@pytest.mark.parametrize("tool_name,error,banned", [...])` — five rows per spec.

**T2 implementation notes:**

- Patch `chat_completion` with a list append to count invocations.
- Do not require full `process_turn` / roster — beat path is orchestrator-only.
- Assert **return value** of `_llm_loop`, not tool message JSON.

**T10 implementation notes:**

- Easiest: single response with **two** `tool_calls` — one failing `combat_action`, one succeeding (mock `_execute_combat_action` side effect).
- Alternative: mock `chat_completion` to return fail on depth 0 and succeed on depth 1 — assert `TOOL FAILED` in accumulated `messages` before recurse.

---

## Implementation order

1. `__init__` + `_handle_combat_trigger` + `_execute_tool` + `_llm_loop` R1 short-circuit → **T1, T2**
2. `_llm_loop` R2 strip → **T3–T7**
3. `_combat_llm_loop_inner` R3/R4 → **T8–T10**
4. R8 logging → **T11** (optional)
5. Full pytest + domain spec changelog on ticket close

---

## Verification checklist (impl agent)

- [ ] R1: failed `start_combat_from_trigger` never calls `run_combat_monster_turns()`
- [ ] R1: player sees canonical two-line failure on same turn as `process_beat`
- [ ] R2/R3: no `\n\n{assistant content}` on `all_failed`
- [ ] R4: `TOOL FAILED` system line before tool result on partial combat failure
- [ ] T1–T10 green; engine regression commands run
- [ ] `tmp/app-combat-play-spec.md` checklist + changelog on `release --done`

---

## Pointers

- Research paths A–F: [research-brief.md](./research-brief.md)
- Requirement IDs R1–R8: [spec.md](./spec.md)
- QA gates: [qa-spec-pass.md](./qa-spec-pass.md) (round 2 PASS)
