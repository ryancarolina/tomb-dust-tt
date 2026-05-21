# Implementation Plan: APP-024-block-site-fiction

**Status:** draft  
**backlog_ticket:** APP-024  
**ticket_path:** tmp/backlog/app-024-block-site-fiction-without-enter-tool.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Exploration narration today exits `_llm_loop` raw — no compose step between mechanics and `_emit_narration`. Prompt rules forbid site entry without tools, but two leak paths remain:

1. **No-tool return** (`L1959–1960`) — model narrates threshold crossing with zero tool calls.
2. **`all_failed and content`** (`L1999–2006`) — failure banner prepended but success entry prose kept underneath.

Fix in three layers (spec E1–E9):

1. **E1** — Sticky per-turn `entry_committed_this_turn` in `_llm_loop` (depth 0 reset; set on first `ok: true` `enter_dungeon` / `site_enter`; never cleared). **Do not** infer from `_last_tool_results[tool_name]` — dict overwrites on each call (`L1978`).
2. **E4–E6** — Module-level `sanitize_premature_site_entry_flavor(text, *, gate_active: bool) -> str` with marker regexes + pinned refusal line when strip empties prose.
3. **E2, E5, E9** — Shared `_compose_exploration_narration(prose, *, gate_active: bool) -> str` wired from `process_turn` post-`_llm_loop` **and** inside `_llm_loop` at the `all_failed and content` early return. APP-024 strip runs first; APP-077 will append status footer in the same helper later.

**Default path:** orchestrator-only helper (ticket Expected files); reuse `strip_llm_status_tags` import only when APP-077 lands — APP-024 compose helper is strip + optional refusal only.

**Out of scope:** `system_prompt.py`, bridge/engine entry logic, APP-022 hints, APP-028 combat leak, travel fiction gate.

---

## Code-path traces (current → planned)

### Flow A — Exploration turn (happy path with successful entry)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` | Creation/combat branches exit early; exploration branch L779+ | unchanged |
| 2 | same | L779–792: `bridge.status()` → `build_state_context` — exposes `party.mode` (typically `surface`) | **Snapshot** `pre_turn_mode = (status.get("party") or {}).get("mode", "surface")` before `_llm_loop` for gate fallback |
| 3 | same | L813: `narration = self._llm_loop(messages)` | unchanged call site |
| 4 | `orchestrator.py:_llm_loop` | L1925–1926: depth 0 resets `_last_tool_results = {}` | **E1:** also `self._entry_committed_this_turn = False` |
| 5 | same | L1937–1944: `chat_completion` with `TOOLS` | unchanged |
| 6 | same | L1968–1997: tool loop; L1976 `_execute_tool`; L1978 `_last_tool_results[fn_name] = result` | **E1:** after L1978, if `fn_name in ("enter_dungeon", "site_enter")` and `result.get("ok")`: `self._entry_committed_this_turn = True` (sticky) |
| 7 | `_execute_tool` | L2050–2051 `site_enter`; L2086–2090 `enter_dungeon` (+ `site_id` alias) | unchanged — both return bridge dict with `ok` |
| 8 | `bridge.py:enter_dungeon` / `site_enter` | Engine sets `mode=dungeon` or `mode=site` | unchanged |
| 9 | `_llm_loop` | L2015: recurse until text-only return L1959–1960 | unchanged control flow |
| 10 | `process_turn` | L813–814: `_emit_narration(narration)` — **no exploration compose** | **E2/E9:** `gate_active = self._exploration_gate_active(pre_turn_mode)`; `narration = self._compose_exploration_narration(narration, gate_active=gate_active)` before `_emit_narration` |
| 11 | `_emit_narration` | L317–319: log + `_check_creation_drift` only | unchanged — exploration drift optional E7 |

**Gate inactive on happy path:** after successful entry, `entry_committed_this_turn == True` → bypass even if compose runs before re-read of status; post-turn `party.mode in ("dungeon", "site")` also bypasses (E3).

---

### Flow B — Site entry without tool commit (no-tool leak)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `process_turn` | Player on surface asks to enter crypt | `pre_turn_mode == "surface"` |
| 2 | `_llm_loop` | Model returns `content` + empty `tool_calls` | unchanged |
| 3 | same | L1959–1960: `return content or _last_content or fallback` | **No change inside loop** — compose at caller handles |
| 4 | `process_turn` | L813–814: raw entry prose → `_emit_narration` | **E4:** `_compose_exploration_narration` with `gate_active=True` strips threshold/interior markers |
| 5 | Engine | `party.mode` still `surface` | unchanged — mechanical truth preserved |
| 6 | Player output | Full interior fiction visible | **After:** markers removed; if empty → code-owned refusal (E6) |

---

### Flow C — `all_failed and content` (primary documented leak)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `_llm_loop` | Model returns `tool_calls` (e.g. failing `enter_dungeon`) **and** parallel `content` with success entry prose | unchanged model behavior |
| 2 | same | L1968: `all_failed = True`; L1979–1980: any `ok` clears flag | unchanged |
| 3 | same | L1986–1991: system inject "MUST narrate failure" per failed tool | unchanged |
| 4 | same | L1999–2006: `if all_failed and content:` → `return f"[Mechanics failed — {failures}]\n\n{content}"` | **E5:** before banner prepend: `gate_active = self._exploration_gate_active(pre_turn_mode)` where `pre_turn_mode` read from `self._exploration_pre_turn_mode` set at depth 0; `safe_content = self._compose_exploration_narration(content, gate_active=gate_active)`; return `f"[Mechanics failed — {failures}]\n\n{safe_content}"` |
| 5 | Player | Sees banner **and** "You step into the torchlit crypt…" | **After:** banner + sanitized surface-safe text only |

**Why sanitize inside `_llm_loop`:** early return bypasses a single post-loop compose if caller ever changes; spec E5 mandates this path explicitly. `process_turn` compose still runs on the final string (idempotent when gate inactive or prose already clean).

---

### Flow D — `entry_committed_this_turn` sticky flag vs `_last_tool_results` overwrite

| Step | File:symbol | Current (L) | Bug without E1 |
|------|-------------|-------------|----------------|
| 1 | `_llm_loop` turn N | First `enter_dungeon` → `{ok: true}` | `_last_tool_results["enter_dungeon"] = {ok: true}`; **flag True** |
| 2 | same | Model retries bad `enter_dungeon` → `{ok: false}` | L1978 **overwrites** dict slot to `{ok: false}` |
| 3 | Gate inference from dict only | Final slot says failure | Would incorrectly set `gate_active=True` and strip legitimate post-entry prose |
| 4 | **E1 sticky flag** | Second failure does not clear flag | `entry_committed_this_turn` stays **True**; gate bypass; entry fiction **retained** |

**Implementation shape:**

```python
# Orchestrator.__init__ — add default for clarity
self._entry_committed_this_turn = False
self._exploration_pre_turn_mode = "surface"

# _llm_loop depth 0 block (after L1925–1926)
self._entry_committed_this_turn = False
try:
    st = self.bridge.status()
    self._exploration_pre_turn_mode = (st.get("party") or {}).get("mode", "surface")
except Exception:
    self._exploration_pre_turn_mode = "surface"

# After each tool result (L1978 area)
if fn_name in ("enter_dungeon", "site_enter") and result.get("ok"):
    self._entry_committed_this_turn = True
```

**Gate predicate helper:**

```python
def _exploration_gate_active(self, pre_turn_mode: str) -> bool:
    if self._entry_committed_this_turn:
        return False  # E1 bypass
    if pre_turn_mode in ("dungeon", "site"):
        return False  # E3 — already inside
    # E2: surface-only per domain spec; hub/preparation uses mode=surface in engine
    return pre_turn_mode == "surface"
```

**Mode snapshot (qa-spec-pass NOTE-003):** use **`party.mode` at depth-0 `_llm_loop` start** (same snapshot as `process_turn` pre-loop `status()`). Do **not** use `party.phase` (`preparation`, `delve`) for gate — phase can read `delve` while mode is still `surface`. Engine reports hub as `mode=surface` during preparation at Registry desk.

---

### Flow E — `_compose_exploration_narration` and APP-077 compose order

| Order | Step | Owner | Action |
|-------|------|-------|--------|
| 1 | `sanitize_premature_site_entry_flavor(prose, gate_active=…)` | **APP-024** | Strip interior/threshold fiction when gate active |
| 2 | If stripped empty + gate was active | **APP-024** | Append `_SITE_ENTRY_REFUSAL_LINE` (E6) |
| 3 | `strip_llm_status_tags(prose)` | **APP-077** | Remove LLM bracket status lies |
| 4 | Append `format_exploration_status(status)` footer | **APP-077** | Code-owned `[Location:…]` line |

**APP-024 ships steps 1–2 only.** Structure helper so APP-077 adds 3–4 without reordering:

```python
def _compose_exploration_narration(self, prose: str, *, gate_active: bool) -> str:
    text = sanitize_premature_site_entry_flavor(prose or "", gate_active=gate_active)
    if gate_active and not text.strip():
        text = _SITE_ENTRY_REFUSAL_LINE
    # APP-077: text = strip_llm_status_tags(text); text = f"{text}\n\n{format_exploration_status(status)}"
    return text
```

Document in domain spec § APP-077 coordination (already at L63–70) — no code dependency on APP-077 ticket.

---

### Flow F — What must not change

| Path | File:symbol | Reason |
|------|-------------|--------|
| Creation `_compose_creation_narration` | `orchestrator.py` L824+ | Separate FSM; no site-entry gate |
| Combat `_combat_llm_loop_inner` | L1800+ | APP-028 scope; combat has own failure banner leak class |
| `_execute_tool` entry routing | L2050–2090 | Engine commit unchanged |
| `_check_creation_drift` | L232+ | Telemetry only today; E7 optional extension |

---

## Task breakdown

### 1. Sticky `entry_committed_this_turn` — `app/gm/orchestrator.py`

#### 1.1 Instance state — `Orchestrator.__init__` (~L108)

Add:

- `self._entry_committed_this_turn: bool = False`
- `self._exploration_pre_turn_mode: str = "surface"`

#### 1.2 Depth-0 reset + mode snapshot — `_llm_loop` (~L1925–1926)

After existing `_last_tool_results = {}`:

1. Set `_entry_committed_this_turn = False`.
2. Snapshot `_exploration_pre_turn_mode` from `bridge.status()["party"]["mode"]` (default `"surface"`).

#### 1.3 Set flag on successful entry tools — `_llm_loop` tool loop (~L1976–1980)

Immediately after `self._last_tool_results[fn_name] = result`:

```python
if fn_name in ("enter_dungeon", "site_enter") and result.get("ok"):
    self._entry_committed_this_turn = True
```

**Never** clear flag on later failures in the same turn.

#### 1.4 `_exploration_gate_active(pre_turn_mode: str) -> bool`

New method implementing E2/E3/E1 bypass as in Flow D.

---

### 2. `sanitize_premature_site_entry_flavor` — `app/gm/orchestrator.py`

**Placement:** module-level function below existing constants (~L80), mirroring `creation.py:sanitize_premature_completion_flavor` pattern.

**Signature:** `def sanitize_premature_site_entry_flavor(text: str, *, gate_active: bool) -> str`

**Behavior:**

- If not `gate_active` or empty text → return text unchanged.
- If `gate_active`:
  1. Run `_SITE_ENTRY_MARKER_RES` — list of compiled regexes (case-insensitive) targeting:
     - Threshold crossing: `step (?:into|inside|through)`, `cross(?:es|ed)? the threshold`, `beyond the (?:arch|door|gate)`
     - Interior reveal: `torchlit`, `corridor`, `vault interior`, `catacomb`, `undercrypt`, `dungeon (?:floor|hall)`
     - False in-dungeon claims: `you (?:are|enter|stand) (?:now )?(?:in|inside) (?:the )?(?:crypt|dungeon|site|undercrypt|vault)`
     - LLM status lies while on surface: `\[Phase:\s*delve`, `\[Location:[^\]]*(?:UG-|undercrypt|crypt|dungeon)`, inline `Phase: delve` / `mode: dungeon` (reuse bracket patterns from `creation.py:_LLM_STATUS_TAG_RE` style — **subset** for entry, not full status strip)
  2. **Line-oriented pass:** drop lines matching any marker; collapse `\n{3,}`.
  3. **Paragraph pass:** if whole text still matches a marker after line pass, return `""`.
  4. Preserve benign surface prose (travel banter, NPC at entrance) — markers are entry-specific, not generic "crypt" mention in quest dialog if line lacks crossing verbs (unit tests lock behavior).

**Pinned refusal line (E6 / qa-spec-pass NOTE-002):**

```python
_SITE_ENTRY_REFUSAL_LINE = (
    "The entrance holds you at the threshold — the Registry ledger still shows you on the surface. "
    "Crossing requires a successful **enter_dungeon** or **site_enter** call; the delving clock does not start until then."
)
```

Use when `gate_active` and sanitizer returns empty/whitespace-only. Must **not** imply entry succeeded when tools failed this turn.

Update domain spec § Sanitizer contract refusal sentence on close to match this exact string.

---

### 3. `_compose_exploration_narration` — `app/gm/orchestrator.py`

New method on `Orchestrator` (~after `_emit_narration`):

- Input: raw LLM prose + `gate_active: bool`
- Apply sanitizer → optional refusal → return (APP-077 extension point documented in docstring)

---

### 4. Wire compose — `process_turn` + `_llm_loop`

#### 4.1 `process_turn` (~L779–814)

Before L813 `_llm_loop`:

```python
status = self.bridge.status()  # already loaded L779 — reuse
pre_turn_mode = (status.get("party") or {}).get("mode", "surface")
```

After L813:

```python
gate_active = self._exploration_gate_active(pre_turn_mode)
narration = self._compose_exploration_narration(narration, gate_active=gate_active)
self._emit_narration(narration)
```

Use same `pre_turn_mode` as depth-0 snapshot when loop runs synchronously (equivalent to `_exploration_pre_turn_mode` after loop).

#### 4.2 `_llm_loop` `all_failed and content` (~L1999–2006)

Replace bare `content` in return with composed safe content:

```python
if all_failed and content:
    gate_active = self._exploration_gate_active(self._exploration_pre_turn_mode)
    safe = self._compose_exploration_narration(content, gate_active=gate_active)
    failures = "; ".join(...)
    return f"[Mechanics failed — {failures}]\n\n{safe}"
```

---

### 5. Optional telemetry (E7) — defer unless trivial

If timeboxed: extend `_check_creation_drift` or add `_check_exploration_drift` called from `_compose_exploration_narration` when strip mutates text — log `premature_site_entry` via `log_error` or new logger helper. **Non-blocking** for AC; skip if scope pressure.

---

### 6. Tests — `app/tests/test_exploration_site_entry_gate.py` (new)

**Module layout:** follow `test_creation_flavor_sanitize.py` — direct unit tests for helper + orchestrator integration with patched `chat_completion`.

#### 6.1 Test helpers

```python
def _patch_llm_sequence(monkeypatch, responses: list[dict]):
    """Each dict: {content, tool_calls, finish_reason}. Pop per chat_completion call."""

def _surface_exploration_orchestrator(orchestrator):
    """Drive minimal creation finalize OR monkeypatch status to exploration-ready surface party."""

ENTRY_PROSE = "You step into the torchlit crypt. Corridors stretch ahead."
BENIGN_SURFACE = "The clerk stamps your permit. Wind off the salt road."
```

**Mock LLM must not mask leaks** — never default `"Test narration."` for entry-gate cases.

#### 6.2 Test matrix (spec § Test plan)

| Test | Setup | Assert |
|------|-------|--------|
| `test_sanitize_premature_site_entry_flavor_unit` | Direct helper; `gate_active=True/False` fixtures | Entry lines removed; `BENIGN_SURFACE` retained when `gate_active=True`; unchanged when `gate_active=False` |
| `test_surface_no_tool_entry_fiction_stripped` | Surface party; mock content-only `ENTRY_PROSE` | No threshold/interior markers; `mode=surface`; refusal or safe prose |
| `test_surface_failed_enter_dungeon_no_entry_fiction` | Mock tool call failing `enter_dungeon` + parallel `ENTRY_PROSE`; triggers `all_failed and content` | `"[Mechanics failed"` in output; `ENTRY_PROSE` markers absent |
| `test_surface_successful_enter_dungeon_allows_fiction` | Mock `enter_dungeon` ok + entry prose; stub `_execute_tool` or bridge | Entry prose retained; `mode=dungeon` |
| `test_success_then_failed_enter_dungeon_retains_fiction` | Two `enter_dungeon` calls: ok then fail; entry prose in final content | Prose **retained**; proves dict-only gate would fail |
| `test_successful_site_enter_allows_fiction` | Mock `site_enter` ok + entry prose | Prose retained; `mode=site` |
| `test_site_entry_gate_bypass_when_in_dungeon` | Start `mode=dungeon`; room description without entry tools | Prose **unchanged** (byte-equal or marker-presence equal) |

#### 6.3 Integration pattern for tool-call mocks

Patch `gm.orchestrator.chat_completion` to return structured responses:

```python
# Response 1: tool call enter_dungeon
{"content": "", "tool_calls": [{"id": "1", "function": {"name": "enter_dungeon", "arguments": "{}"}}], "finish_reason": "tool_calls"}
# Response 2: narration
{"content": ENTRY_PROSE, "tool_calls": [], "finish_reason": "stop"}
```

Patch `_execute_tool` or `bridge.enter_dungeon` to return controlled `{ok: bool, ...}` without requiring real site JSON in isolated workspace.

#### 6.4 Commands

```bash
cd app && python -m pytest tests/test_exploration_site_entry_gate.py -q
cd app && python -m pytest tests/ -q -k "not exploration_site_entry"
cd app && python -m pytest ../play/tomb_gm/tests/test_extraction_slice.py -q
```

---

### 7. Domain spec sync on close — `tmp/app-exploration-delve-spec.md`

On `claim_ticket.py release APP-024 --done`:

1. Pin refusal line in § Sanitizer contract (L54) to `_SITE_ENTRY_REFUSAL_LINE` text.
2. Mark checklist L120 `[x]`.
3. Append changelog: `APP-024 done: entry_committed_this_turn, sanitize_premature_site_entry_flavor, all_failed path, test_exploration_site_entry_gate.py`.
4. Update § File map L142+ with helper + test module.

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **E1** | Sticky `entry_committed_this_turn`; no dict-only inference | `_llm_loop` L1925, L1978 | `test_success_then_failed_enter_dungeon_retains_fiction` |
| **E2** | Gate when surface + not committed | `_exploration_gate_active`, `process_turn` | `test_surface_no_tool_entry_fiction_stripped` |
| **E3** | Bypass in dungeon/site or committed | `_exploration_gate_active` | `test_site_entry_gate_bypass_when_in_dungeon` |
| **E4** | `sanitize_premature_site_entry_flavor` | module-level in `orchestrator.py` | `test_sanitize_premature_site_entry_flavor_unit` |
| **E5** | `all_failed and content` sanitized | `_llm_loop` L1999–2006 | `test_surface_failed_enter_dungeon_no_entry_fiction` |
| **E6** | Code-owned refusal when empty | `_compose_exploration_narration` | no-tool + failed-entry tests |
| **E8** | Dual entry tools | E1 flag on both names | `test_successful_site_enter_allows_fiction` |
| **E9** | APP-077 order documented | `_compose_exploration_narration` docstring + domain § | code review / domain spec |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/orchestrator.py` | E1 flag + snapshot; `_exploration_gate_active`; `sanitize_premature_site_entry_flavor` + markers + refusal constant; `_compose_exploration_narration`; wire `process_turn` + `all_failed` path |
| `app/tests/test_exploration_site_entry_gate.py` | **New** — seven tests per spec |
| `tmp/app-exploration-delve-spec.md` | Refusal copy + checklist + changelog on close |

**Out of scope:** `app/gm/creation.py`, `system_prompt.py`, `bridge.py`, `logger.py` (unless E7 added).

---

## Rollback

Revert `orchestrator.py` + delete test module restores pre-APP-024 behavior (prompt-only site entry rule). No feature flags.

---

## Open questions

- **None blocking.** Marker regex set finalized in impl + unit fixtures; adjust if over-strips wilderness "crypt" mentions without crossing verbs.
- **Double compose:** `process_turn` runs compose after `_llm_loop`; `all_failed` path composes inside loop — sanitizer must be idempotent on already-clean prose.
- **Session claim:** confirm `tmp/.active-ticket.json` includes APP-024 before `app/` edits.
