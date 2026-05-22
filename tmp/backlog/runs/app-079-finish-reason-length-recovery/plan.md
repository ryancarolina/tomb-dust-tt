# Implementation Plan: APP-079-finish-reason-length-recovery

**Status:** draft  
**backlog_ticket:** APP-079  
**ticket_path:** [tmp/backlog/app-079-finish-reason-length-recovery-policy.md](../../app-079-finish-reason-length-recovery-policy.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Today every `chat_completion` path logs `finish_reason` via `log_llm_response` but never branches on `"length"`. Truncated flavor is composed and emitted — especially creation at `_CREATION_FLAVOR_MAX_TOKENS = 120` (~1.9% of session responses).

Fix in four layers (R1–R6):

1. **R1** — Module-level `LengthRecoveryResult` + pure `handle_finish_reason_length(...)` in `orchestrator.py` (top of file, near `PlayerDeathResult`).
2. **R2–R4** — Wire helper **immediately after every `log_llm_response`** on player-visible prose paths; creation callers pass `body_pending` / `flavor_only` per § Semantics table; exploration/combat get terminal retry + `_last_good_content` fallback; mid-chain strips markdown tables and continues (no content-only retry).
3. **R5** — `log_llm_truncation_recovery` + `log_narration_llm_budget_exhausted` in `logger.py`.
4. **R6** — Per-turn `narration_llm_attempts` counter (shared APP-083 budget); helper signature stable for future `narrate_with_verification` import.

**Defense in depth unchanged:** `_compose_creation_narration` strippers (APP-072/073/078) stay — 079 discard is the primary gate when code `body` is pending.

**Out of scope:** `_creation_llm_loop` (zero callers); token cap tuning; APP-078 generic compose strip; APP-083 verify loop (083 calls same helper later).

---

## Code-path traces (current → planned)

### Flow A — Creation flavor (primary choke: `_narrate_flavor`)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_auto_present_*` / `_auto_roll_stats` / `_auto_finalize` | L1115–1501: each calls `_narrate_flavor` or `_narrate_creation_flavor` / `_creation_table_flavor` | Pass **`body_pending` / `flavor_only`** per wire table below |
| 2 | `orchestrator.py:_narrate_creation_flavor` | L980–988: `_narrate_flavor` → optional `_sanitize_creation_flavor` | Add kwargs passthrough; ROLL_STATS keeps `presenting_step` sanitize |
| 3 | `orchestrator.py:_creation_table_flavor` | L1317–1324: skip LLM when `error=` | unchanged skip; when LLM runs → `body_pending=True` |
| 4 | `orchestrator.py:_narrate_flavor` | L990–1007: `chat_completion` → `log_llm_response` → return raw content | **R1+R2:** `_fetch_creation_flavor_with_recovery` inner loop OR inline: budget check → completion → log → `handle_finish_reason_length` → log recovery → retry/fallback/discard |
| 5 | `orchestrator.py:_compose_creation_narration` | L896–931: strippers → body → footer | When `discard_flavor`, callers pass `flavor=""` before compose (strippers no-op) |

#### Creation wire flags (normative)

| Presenter | Step | `body_pending` | `flavor_only` | On `length` |
|-----------|------|----------------|---------------|-------------|
| `_auto_present_name` | NAME | `false` | `true` | retry (1×) or static fallback |
| `_auto_present_race` | RACE | `true` | `false` | `discard_flavor` |
| `_auto_present_class` | CLASS | `true` | `false` | `discard_flavor` |
| `_auto_present_skills` | SKILLS | `true` | `false` | `discard_flavor` |
| `_auto_present_schools` | SPELL_SCHOOLS | `true` | `false` | `discard_flavor` |
| `_auto_present_spells` | SPELLS | `true` | `false` | `discard_flavor` |
| `_auto_present_equipment` | EQUIPMENT_GOLD | `true` | `false` | `discard_flavor` |
| `_auto_roll_stats` | ROLL_STATS→CLASS | `true` | `false` | `discard_flavor` |
| `_auto_finalize` | FINALIZE→WORLD_INTRO | `true` | `false` | `discard_flavor` |
| `_creation_table_flavor` | SKILLS/SCHOOLS/SPELLS | `true`* | `false` | `discard_flavor` (*when `error` set → LLM skipped) |

**Invariant:** never `body_pending=True` and `flavor_only=True`.

### Flow B — Exploration `_llm_loop`

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` → `_llm_loop` | L765 → L2021 | **Budget:** `_reset_narration_llm_budget()` at exploration turn entry (same turn as `_llm_loop` depth 0) |
| 2 | `orchestrator.py:_llm_loop` | L2045–2064: completion → `log_llm_response` | After log → `handle_finish_reason_length(mode="exploration", ...)` |
| 3 | same | L2066: `_last_content = content or _last_content` | Split: **`_last_good_content`** updated only when `finish_reason in ("stop", "")` and non-empty; `_last_content` may remain for depth-limit debug |
| 4 | same | L2068–2069: terminal `return content` | **Terminal + `length`:** one retry with system hint “complete in ≤3 sentences”; still `length` → `fallback_last_content` if eligible `_last_good_content`, else static fallback |
| 5 | same | L2071–2075: append assistant + tool_calls | **Mid-chain + `length`:** `content = strip_markdown_table_blocks(content)` before append; **no** length retry; continue loop |
| 6 | same | L2068–2069: terminal `finish_reason != length` | On terminal `stop` + content → update `_last_good_content` |

### Flow C — Combat `_combat_llm_loop_inner` + final narrate

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_combat_turn` | L1781+ | `_reset_narration_llm_budget()` at combat turn start |
| 2 | `orchestrator.py:_combat_llm_loop_inner` | L1895: `log_llm_response` | Mid-chain: same table strip as exploration when `tool_calls` |
| 3 | same | L1897–1900: terminal no tools → return content | Terminal policy: length retry → `_last_good_content` → static |
| 4 | same | L1966–1974: **final** `chat_completion` after mechanics | **Gap today:** no `log_llm_response`. Add log + `handle_finish_reason_length(mode="combat")` + terminal recovery before return |
| 5 | `orchestrator.py:_narrate_only` / `_narrate_text` | L1503–1520, L1736–1741 | Wire terminal combat/exploration one-shots: log already present → add recovery after log |

### Flow D — Dead path (no wire)

| Path | File:symbol | L | Reason |
|------|-------------|---|--------|
| `_creation_llm_loop` | `orchestrator.py` | L1522–1595 | Zero callers — spec non-goal |

### Flow E — APP-083 handoff (future, no impl in 079)

```text
chat_completion → log_llm_response
  → handle_finish_reason_length (079)     # discard before verify when body_pending + length
  → verify_narration (083)
  → compose + emit
```

079 lands standalone on `_narrate_flavor` / `_llm_loop` first. 083 Phase 1 replaces inline creation calls with `narrate_with_verification` that **imports** `handle_finish_reason_length` — no duplicated length logic.

---

## Task breakdown

### 1. Types + constants — `app/gm/orchestrator.py` (module level)

**Placement:** after `PlayerDeathResult` (~L140), before `class Orchestrator`.

```python
LENGTH_RETRY_MIN_CHARS = 32
LENGTH_MAX_RECOVERY_RETRIES = 1
NARRATION_LLM_MAX_ATTEMPTS = 6

@dataclass(frozen=True)
class LengthRecoveryResult:
    content: str | None
    action: Literal["pass", "discard_flavor", "retry", "fallback_last_content", "fallback_static"]
    retry_hint: str | None = None
```

**Static fallbacks (module constants):**

| Context | Fallback string |
|---------|-----------------|
| Creation flavor-only (NAME) | `"The Registry clerk looks up from the ledger."` (≤2 sentences; body still carries name prompt) |
| Exploration terminal | `"The dust settles. You stand at the crossroads, uncertain. What do you do?"` (reuse depth-limit copy L2041) |
| Combat terminal | `"The fight grinds on — declare your next action."` |

### 2. `handle_finish_reason_length(...)` — pure policy — `orchestrator.py`

**Signature** (matches run spec + domain spec):

```python
def handle_finish_reason_length(
    response: dict[str, Any],  # content, finish_reason keys from chat_completion
    *,
    mode: Literal["creation", "exploration", "combat"],
    creation_step: str | None = None,
    body_pending: bool = False,
    flavor_only: bool = False,
    attempt: int = 0,  # length-recovery retries already consumed this turn
    has_tool_calls: bool = False,
    content_length: int | None = None,
    last_good_content: str | None = None,
    budget_exhausted: bool = False,
) -> LengthRecoveryResult:
```

**Decision tree (never raises):**

| Condition | Action | `content` |
|-----------|--------|-----------|
| `finish_reason != "length"` | `pass` | unchanged |
| `has_tool_calls` | `pass`* | caller strips tables separately |
| `body_pending` | `discard_flavor` | `None` → caller uses `""` |
| `budget_exhausted` | `fallback_static` or `discard_flavor` | per mode |
| `flavor_only` or terminal exploration/combat | `retry` if `attempt < LENGTH_MAX_RECOVERY_RETRIES` and (length or len < MIN) | unchanged + `retry_hint` |
| retry exhausted + eligible `last_good_content` | `fallback_last_content` | `last_good_content` |
| else | `fallback_static` | mode fallback string |

\*Mid-chain: helper returns `pass`; caller runs `strip_markdown_table_blocks` when `finish_reason=="length"` and `tool_calls` — keeps table-strip logic in one place (task 3).

**Retry hints:**

| Mode | `retry_hint` |
|------|--------------|
| Creation flavor-only | `"Reply in at most 2 short sentences. No markdown tables, lists, or status lines."` |
| Exploration/combat terminal | `"Complete your narration in at most 3 short sentences. No tool calls."` |

Always call `log_llm_truncation_recovery` in the **caller** after helper returns (helper stays pure / testable).

### 3. Mid-chain table strip — `app/gm/creation.py`

**New:** `strip_markdown_table_blocks(text: str) -> str`

**Algorithm** (resolves qa-spec-pass SPEC-004; shared with future APP-078):

1. Reuse existing `_MD_TABLE_SEPARATOR_RE`, `_MD_TABLE_ROW_RE` (L563–564).
2. Scan lines; when a line matches `^\s*\|.*\|` (pipe row):
   - Treat as block start (header or truncated header).
   - If next line is separator → skip separator.
   - Consume subsequent `^\s*\|.*\|` rows until break.
   - Drop consumed block; continue scan.
3. Rejoin; collapse `\n{3,}` → `\n\n`; `.strip()`.
4. **No step-specific fingerprints** — generic pipe-table blocks only (mid-chain assistant messages may mention any catalog).

**Import** in `orchestrator.py` compose import block (~L16–44).

**Mid-chain wire** (`_llm_loop` L2071+, `_combat_llm_loop_inner` L1902+):

```python
if tool_calls and finish_reason == "length" and content:
    content = strip_markdown_table_blocks(content)
    log_llm_truncation_recovery(..., action="strip_mid_chain_tables", ...)
```

Use action `"strip_mid_chain_tables"` in log (extend spec action union in domain spec changelog on close) OR map to existing `"pass"` with distinct `step` — **prefer explicit action** for observability.

### 4. Per-turn budget — `Orchestrator`

**New instance fields** (`__init__` ~L159):

```python
self._narration_llm_attempts = 0
self._length_recovery_attempts = 0
self._last_good_content = ""
```

**Methods:**

```python
def _reset_narration_llm_budget(self) -> None:
    self._narration_llm_attempts = 0
    self._length_recovery_attempts = 0
    self._last_good_content = ""

def _consume_narration_llm_attempt(self) -> bool:
    """Returns False when budget exhausted (caller should fallback)."""
    self._narration_llm_attempts += 1
    if self._narration_llm_attempts >= NARRATION_LLM_MAX_ATTEMPTS:
        log_narration_llm_budget_exhausted(...)
        return False
    return True
```

**Reset call sites:**

| Entry | File:symbol | When |
|-------|-------------|------|
| Creation turn | `_creation_turn_body` | L1018 top |
| Exploration | `_llm_loop` | L2027 `depth == 0` |
| Combat | `_combat_turn` | L1782 top |

**Length retry tagging:** increment `_length_recovery_attempts` only when issuing `length_recovery_retry` (max 1 per turn); pass as `attempt=` to helper.

### 5. Creation flavor fetch loop — refactor `_narrate_flavor`

**New signature:**

```python
def _narrate_flavor(
    self,
    messages: list[dict[str, Any]],
    *,
    body_pending: bool = False,
    flavor_only: bool = False,
    creation_step: str | None = None,
) -> str:
```

**Loop (pseudocode):**

```python
step = creation_step or self.creation.step
length_attempt = 0
msgs = list(messages)
while True:
    if not self._consume_narration_llm_attempt():
        return "" if body_pending else NAME_STATIC_FALLBACK
    response = chat_completion(...)
    content = response.get("content", "") or ""
    log_llm_response(content, [], response.get("finish_reason", ""))
    result = handle_finish_reason_length(
        response, mode="creation", creation_step=step,
        body_pending=body_pending, flavor_only=flavor_only,
        attempt=length_attempt, budget_exhausted=not self._narration_llm_attempts_remaining(),
    )
    log_llm_truncation_recovery("creation", step, result.action, len(content or ""), length_attempt)
    if result.action == "discard_flavor":
        return ""
    if result.action == "retry":
        length_attempt += 1
        msgs = msgs + [{"role": "system", "content": result.retry_hint}]
        continue
    if result.action == "fallback_static":
        return result.content or NAME_STATIC_FALLBACK
    return content  # pass
```

**Exception path** (L1002–1004): unchanged clerk fallback; no recovery log required.

**Update all creation callers** to pass flags (task 6).

### 6. Update creation presenters — `orchestrator.py`

| Function | Change |
|----------|--------|
| `_auto_present_name` L1117 | `_narrate_flavor(..., body_pending=False, flavor_only=True)` |
| `_auto_present_race` L1129 | `body_pending=True, flavor_only=False` |
| `_auto_present_class` L1145 | same |
| `_auto_present_skills` / `_creation_table_flavor` | `_creation_table_flavor` delegates with `body_pending=True`; error skip unchanged |
| `_auto_present_schools` L1345 | via `_creation_table_flavor` |
| `_auto_present_spells` L1357 | via `_creation_table_flavor` |
| `_auto_present_equipment` L1369 | `_narrate_flavor(..., body_pending=True)` |
| `_auto_roll_stats` L1388 | `_narrate_creation_flavor(..., body_pending=True)` — extend wrapper kwargs |
| `_auto_finalize` L1486 | `_narrate_flavor(..., body_pending=True, creation_step="FINALIZE")` |

**Compose unchanged:** presenters still call `_compose_creation_narration(flavor, body[, footer])`; empty flavor after discard is valid.

### 7. Exploration terminal recovery — `_llm_loop`

After L2064 `log_llm_response`:

1. If `tool_calls`: apply mid-chain strip (task 3); skip length retry; continue existing loop.
2. If terminal (`not tool_calls`):
   - Run `handle_finish_reason_length(mode="exploration", has_tool_calls=False, last_good_content=self._last_good_content, ...)`.
   - On `retry`: append hint, recurse `_llm_loop` **or** inner while-loop at same depth (prefer inner loop to avoid depth inflation).
   - On `fallback_last_content` / `fallback_static`: return fallback content.
   - On `pass`: if `finish_reason in ("stop", "")` and content: `self._last_good_content = content`; return content.

**Eligibility:** `_last_good_content` only set from prior terminal responses with `finish_reason == "stop"` (or missing) in **this** turn's loop — reset by `_reset_narration_llm_budget` at depth 0.

### 8. Combat recovery — `_combat_llm_loop_inner` + `_narrate_only`

**Tool round (L1893–1902):** mirror exploration mid-chain strip.

**Terminal no tools (L1897–1900):** exploration terminal policy with `mode="combat"`.

**Final narrate block (L1965–1976):**

```python
final = chat_completion(...)
content = final.get("content") or ""
finish_reason = final.get("finish_reason", "")
log_llm_response(content, [], finish_reason)
# consume budget + handle_finish_reason_length terminal combat
# return recovered content or brief fallback
```

**`_narrate_only`:** extract shared `_terminal_narration_with_recovery(messages, *, mode)` used by `_narrate_only`, combat final narrate, and optionally exploration terminal — avoids triplicate retry loops.

### 9. Observability — `app/gm/logger.py`

```python
def log_llm_truncation_recovery(
    mode: str,
    step: str | None,
    action: str,
    content_length: int,
    attempt: int,
) -> None:
    log_entry("llm_truncation_recovery", {...})

def log_narration_llm_budget_exhausted(
    mode: str,
    step: str | None,
    attempts: int,
) -> None:
    log_entry("narration_llm_budget_exhausted", {...})
```

Import in orchestrator (~L71).

**On ticket close:** append event rows to `tmp/app-logging-qa-spec.md`; cross-link in `tmp/app-character-creation-spec.md` compose §.

### 10. Tests — `app/tests/test_llm_truncation_recovery.py` (new)

**Stub helper** — promote pattern from `test_creation_tables.py` L17–40; support **response queue** for retry tests:

```python
def _patch_llm_responses(monkeypatch, responses: list[dict]):
    # each dict: content, finish_reason; pop on each create()
```

Optionally add `finish_reason` param to `conftest.py` `_StubCompletions` for reuse — **local helper in new module is sufficient** for ticket scope.

| Test | Maps to | Setup | Assert |
|------|---------|-------|--------|
| `test_handle_finish_reason_length_pass` | R1 | unit call, `finish_reason="stop"` | `action=pass`, content unchanged |
| `test_handle_finish_reason_length_discard_when_body_pending` | R1/R2 | unit, `length` + `body_pending=True` | `discard_flavor`, `content is None` |
| `test_creation_length_discards_flavor_when_body_pending` | R2 | stub `length` + partial `\| Race \|`; `new game` → name → RACE | single `\| Race \| Adjustments \|`; `llm_truncation_recovery` `discard_flavor` |
| `test_finalize_length_discards_flavor_ships_summary` | R2 | drive FINALIZE with length flavor stub | HP/MP/Fortune/GP/skills/kit visible; no truncated banter; `discard_flavor` logged |
| `test_narrate_flavor_length_short_retries_or_fallback` | R3 | NAME step; queue `[length+10chars, stop+good]` or double length | ≤2 sentence flavor or static; max one length retry |
| `test_skills_length_ships_code_table_only` | R2 | SKILLS present, LLM `length` + truncated skills table in flavor | full `format_skills_table` markers; no LLM table fragment above |
| `test_exploration_length_fallback_last_content` | R4 | mock `_llm_loop`: first terminal `stop` content, second `length` | returns prior good content; `fallback_last_content` logged |
| `test_mid_chain_length_strips_tables_continues` | R4 | exploration stub: `length` + tool_calls + pipe table in content | loop continues; appended assistant message has no `\|.*\|` table block |
| `test_shared_budget_caps_retries` | R6 | queue 7× `length` on NAME | fallback by attempt 6; `narration_llm_budget_exhausted` logged |

**Regression commands:**

```bash
cd app && python -m pytest tests/test_llm_truncation_recovery.py -q
cd app && python -m pytest tests/test_creation_tables.py tests/test_creation_flavor_sanitize.py -q
cd app && python -m pytest tests/ -q
```

### 11. Spec sync on close (not in impl diff until release)

1. `tmp/app-llm-orchestrator-spec.md` — mark APP-079 checklist item done; changelog row.
2. `tmp/app-logging-qa-spec.md` — `llm_truncation_recovery`, `narration_llm_budget_exhausted` event rows.
3. `tmp/app-character-creation-spec.md` — cross-link centralized length policy (replace APP-072 “no retry” for flavor-only NAME).
4. Backlog ticket — sync Code AC to `LengthRecoveryResult` (qa-spec-pass TICKET-001); drop stale “reduced max_tokens” wording (SPEC-005).

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **R1** | Central helper + `LengthRecoveryResult` | `orchestrator.py` module level | `test_handle_finish_reason_length_*` |
| **R2** | Gated creation discard | `_narrate_flavor` + presenter flags | RACE + SKILLS + finalize integration |
| **R3** | NAME retry / static fallback | `_auto_present_name` flags + retry loop | `test_narrate_flavor_length_short_retries_or_fallback` |
| **R4** | Exploration/combat terminal + mid-chain | `_llm_loop`, `_combat_llm_loop_inner`, final narrate L1966 | exploration fallback + mid-chain strip |
| **R5** | JSONL events | `logger.py` | log assertions in integration tests |
| **R6** | APP-083 handoff + shared budget | budget fields + pure helper signature | `test_shared_budget_caps_retries` |

---

## `log_llm_response` wire checklist

| # | File:symbol | L | Mode | Wire action |
|---|-------------|---|------|-------------|
| 1 | `_narrate_flavor` | 1006 | creation | Full recovery loop (task 5) |
| 2 | `_narrate_only` | 1519 | combat/exploration one-shot | Terminal recovery via shared helper |
| 3 | `_creation_llm_loop` | 1549 | — | **Skip** (dead path) |
| 4 | `_combat_llm_loop_inner` | 1895 | combat | Mid-chain strip + terminal branch |
| 5 | `_combat_llm_loop_inner` final | 1966 | combat | **Add** `log_llm_response` + terminal recovery |
| 6 | `_llm_loop` | 2064 | exploration | Mid-chain strip + terminal branch |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/orchestrator.py` | Constants, dataclass, `handle_finish_reason_length`, budget fields/methods, `_narrate_flavor` loop, `_llm_loop` / `_combat_llm_loop_inner` / `_narrate_only` wire, presenter kwargs |
| `app/gm/creation.py` | `strip_markdown_table_blocks()` |
| `app/gm/logger.py` | `log_llm_truncation_recovery`, `log_narration_llm_budget_exhausted` |
| `app/tests/test_llm_truncation_recovery.py` | **New** — unit + integration per spec test table |
| `tmp/app-llm-orchestrator-spec.md` | Changelog on close |
| `tmp/app-character-creation-spec.md` | Cross-link on close |
| `tmp/app-logging-qa-spec.md` | Event rows on close |

**Note:** `creation.py` mid-chain helper is required for R4; add path to ticket Expected files before impl if hook gate strict.

---

## Rollback

Revert orchestrator + creation + logger + test module restores pre-079 behavior (truncated flavor ships as-is). No feature flags.

---

## Open questions

- **APP-083 merge order:** If 083 Phase 1 lands first with inline length stub, 079 impl replaces stub with `handle_finish_reason_length` import — one-line swap inside `narrate_with_verification`.
- **Mid-chain log action name:** Use `strip_mid_chain_tables` vs reuse `discard_flavor` — prefer new action string; document in logging spec on close.
- **Concurrent APP-078:** Generic compose strip is independent; mid-chain helper can later delegate to APP-078 if unified.
- **Session claim:** ensure `tmp/.active-ticket.json` includes APP-079 before `app/` edits.
