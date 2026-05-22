# Spec: APP-079-finish-reason-length-recovery

**Status:** draft  
**backlog_ticket:** APP-079  
**ticket_path:** [tmp/backlog/app-079-finish-reason-length-recovery-policy.md](../../app-079-finish-reason-length-recovery-policy.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-llm-orchestrator-spec.md` (primary); `tmp/app-character-creation-spec.md` (cross-link on close); `tmp/app-logging-qa-spec.md` (new event on close)

## Problem

The orchestrator logs `finish_reason` on every LLM response but **never branches** on `"length"`. Truncated assistant text is composed and emitted as-is.

**Player-visible harm:**

| Mode | Symptom | Partial mitigations today |
|------|---------|---------------------------|
| Creation (gated steps) | Partial `\| Race \|`, `\| School \|`, stats rows above code table | APP-072/073 step-specific strippers — not SKILLS/SCHOOLS/SPELLS/EQUIPMENT (APP-078 open) |
| Creation (flavor-only) | Cut-off NAME question or half sentence | None |
| Exploration / combat | Truncated final narration or mid-chain assistant prose | `_last_content` used for depth/API errors only — not `length` |

Session `app/logs/session-2026-05-20.jsonl`: **28** `llm_response` events with `finish_reason: length` (~1.9% of responses), overwhelmingly during creation at `_CREATION_FLAVOR_MAX_TOKENS = 120`.

APP-072 explicitly deferred length retry; APP-079 owns the **central policy** across modes.

## Goals

- Single helper `handle_finish_reason_length(...)` applied immediately after every `chat_completion` that feeds player-visible prose.
- **Never** ship truncated markdown table fragments when a code `body` already provides the table.
- Bounded cost: at most **one** length-specific LLM retry per turn where retry is allowed; coordinate with APP-083 via a **shared per-turn LLM attempt budget**.
- Observable: `llm_truncation_recovery` JSONL event for every policy action.

## Non-goals

| Deferred | Owner |
|----------|-------|
| Generic table strip for all creation steps | APP-078 (defense in depth if discard misses) |
| Semantic wrong-catalog retry | APP-083 verify loop |
| Transport/API retry on 400/malformed transcript | APP-032 |
| Revive dead `_creation_llm_loop` | Out of scope unless re-wired |
| Changing `_CREATION_FLAVOR_MAX_TOKENS` or config `max_tokens` defaults | Separate tuning ticket |

## Architecture

### Policy helper

```python
handle_finish_reason_length(
    response,  # OpenRouter choice: content, finish_reason
    *,
    mode: Literal["creation", "exploration", "combat"],
    creation_step: str | None = None,
    body_pending: bool = False,
    flavor_only: bool = False,
    attempt: int = 0,  # length-recovery attempts already consumed this turn
) -> LengthRecoveryResult
```

```python
@dataclass
class LengthRecoveryResult:
    content: str | None          # None → caller uses discard / fallback path
    action: Literal[
        "pass",                  # finish_reason != length
        "discard_flavor",        # creation + body_pending
        "retry",                 # caller performs one bounded LLM retry
        "fallback_last_content", # exploration/combat terminal
        "fallback_static",       # flavor-only static string
    ]
    retry_hint: str | None       # appended system line for single retry
```

**Constants (orchestrator module or config):**

| Constant | Default | Meaning |
|----------|---------|---------|
| `LENGTH_RETRY_MIN_CHARS` | `32` | Below this, flavor-only / terminal prose is “unusably short” → retry or fallback |
| `LENGTH_MAX_RECOVERY_RETRIES` | `1` | Max length-specific retries **per turn** (not per call site) |
| `NARRATION_LLM_MAX_ATTEMPTS` | `6` | Shared cap: length retries + verify retries (APP-083) per published turn |

### Semantics: `body_pending` vs `flavor_only`

**Definitions**

| Flag | Meaning |
|------|---------|
| `body_pending=True` | Compose will include an **authoritative code mechanical block** the player must receive intact — markdown tables from `format_*_table()`, roll-stats readout, class eligibility block, equipment summary, or post-finalize character summary (HP/MP/Fortune/GP/skills/kit). Truncated flavor must not ship above this block → **`discard_flavor`**, no length retry. |
| `body_pending=False` | No authoritative mechanical block pending; player-visible output is flavor-driven or flavor + static prompt copy only. |
| `flavor_only=True` | Creation path where LLM flavor carries the narrative; any `body` is **static prompt copy** (e.g. NAME question line) — **not** a code table or mechanical summary. On `length`: one retry or static fallback (R3). |

**Invariant:** `body_pending=True` ⇒ `flavor_only=False`. Never set both true.

**Not `body_pending`:** error-prefix strings (`**Note:** …`), static prompt lines, or footer tags alone — only code-owned tables, roll readouts, equipment summaries, and finalize summary blocks count.

#### Per-step wiring (creation)

| Step | Present function | Code `body` kind | `body_pending` | `flavor_only` | On `length` |
|------|------------------|------------------|----------------|---------------|-------------|
| NAME | `_auto_present_name` | Static prompt (`"What name shall I put on the Registry ledger?"`) | `false` | `true` | Retry (1×) or static fallback |
| RACE | `_auto_present_race` | `format_races_table()` | `true` | `false` | `discard_flavor` |
| CLASS | `_auto_present_class` | Stat line + `format_classes_table()` | `true` | `false` | `discard_flavor` |
| SKILLS | `_auto_present_skills` | `format_skills_table()` | `true` | `false` | `discard_flavor` |
| SPELL_SCHOOLS | `_auto_present_schools` | `format_schools_table()` | `true` | `false` | `discard_flavor` |
| SPELLS | `_auto_present_spells` | `format_spells_table()` | `true` | `false` | `discard_flavor` |
| EQUIPMENT_GOLD | `_auto_present_equipment` | `format_equipment_summary()` | `true` | `false` | `discard_flavor` |
| ROLL_STATS | `_auto_roll_stats` | `format_roll_stats_table()` + `format_classes_table()` | `true` | `false` | `discard_flavor` |
| FINALIZE → WORLD_INTRO | `_auto_finalize` | Code summary (HP/MP/Fortune/GP/skills/kit) + `RECEPTION_CHOICE` footer | `true` | `false` | `discard_flavor` |
| `_creation_table_flavor` error path | SKILLS / SPELL_SCHOOLS / SPELLS | Error prefix only; LLM skipped when `error` set | n/a | n/a | LLM not called |

**WORLD_INTRO split:** Post-finalize handoff (`_auto_finalize` → `step=WORLD_INTRO`, `active=False`) is **`body_pending=true`** — truncated setting banter is discarded; player still receives code summary + footer. Subsequent turns with `WORLD_INTRO` and `active=False` route to `process_turn` (exploration terminal policy — not this table).

### Recovery matrix (normative)

| Context | `body_pending` | On `finish_reason == "length"` | Length retry? | Verify (APP-083) |
|---------|----------------|--------------------------------|---------------|------------------|
| Creation gated step (RACE, CLASS, SKILLS, … — see § Semantics table) | `true` | **`discard_flavor`** — set flavor `""` before compose | **No** | Runs on surviving flavor (often empty) — low risk |
| Creation flavor-only (NAME) | `false`, `flavor_only=true` | One retry with “≤2 sentences, no tables” **or** static fallback if retry exhausted / budget spent | **Yes (1×)** | Applies to published flavor |
| Creation FINALIZE / WORLD_INTRO handoff (`_auto_finalize`) | `true` | **`discard_flavor`** — ship code summary + footer only | **No** | Runs on surviving flavor (often empty) |
| Creation `_creation_table_flavor` error skip | n/a | LLM not called | — | — |
| Exploration / combat **terminal** (no tool_calls) | n/a | One retry “complete in ≤3 sentences”; if still `length` → `_last_content` if **eligible**, else safe static fallback | **Yes (1×)** | Phase 2–3: same helper inside `narrate_with_verification` |
| Tool loop **mid-chain** (tool_calls present) | n/a | Strip markdown table blocks from assistant `content` before append; **continue loop** | **No** | N/A until terminal prose |
| Combat final narrate (~1966) | n/a | Same as exploration terminal | **Yes (1×)** | Phase 3 |
| `_narrate_only` one-shots | varies | Terminal policy for mode | Per matrix | When 083 wraps path |

**`_last_content` eligibility:** use only when a **prior** stored snippet has `finish_reason == "stop"` (or missing, treated as stop) and non-empty content from the **same** turn loop — never return stale tool-round empty assistant shells.

### Call sites (wire order)

After `log_llm_response`, before compose / verify / tool append:

| Function | Mode | Notes |
|----------|------|-------|
| `_narrate_flavor` | creation | Caller passes `body_pending` / `flavor_only` per § Semantics table |
| `_narrate_creation_flavor` (ROLL_STATS) | creation | `body_pending=True`, `flavor_only=False`; sanitize path unchanged |
| `_llm_loop` | exploration | Terminal + mid-chain branches |
| `_combat_llm_loop_inner` | combat | Tool loop + final narrate call |
| `_narrate_only` / `_narrate_text` | combat | Terminal one-shots |

Creation compose: when action is `discard_flavor`, caller passes `flavor=""` into `_compose_creation_narration` — strippers (APP-072/073/078) remain defense in depth.

## Coordination with APP-083 (mechanical-truth gate)

**Batch:** [batch-board-APP-041-APP-079-APP-083.md](../batch-board-APP-041-APP-079-APP-083.md) — parallel impl wave; no hard dependency, but **shared budget and call order are normative**.

### Pipeline order (creation + code body)

```text
chat_completion → log_llm_response
  → handle_finish_reason_length (079)
       if body_pending + length → discard_flavor (STOP — no verify on discarded text)
  → [APP-083 Phase 1+] verify_narration(surviving_flavor, TurnTruth)
       if fail → retry with violation feedback (consumes shared budget)
  → _compose_creation_narration(flavor, body, footer)
  → emit once
```

**Rule:** When `body_pending` and `finish_reason == "length"`, **discard before verify**. Do not treat truncated table flavor as input to `verify_narration` — verify may pass on benign partial sentences while `\| Race \|` fragments remain unless table rules are exhaustive.

### Pipeline order (flavor-only / exploration / combat terminal)

```text
chat_completion → log_llm_response
  → handle_finish_reason_length (079)
       may request one length retry OR fallback
  → verify_narration (083) on candidate prose
       truncated table / catalog violations → verify fail → retry
  → compose + emit
```

When 079 already discarded or fell back to static/last-good text, 083 still verifies **what will publish** (static fallbacks must be pre-approved or trivially pass).

### Shared per-turn retry budget

| Budget | Owner | Default |
|--------|-------|---------|
| `NARRATION_LLM_MAX_ATTEMPTS` | Orchestrator turn | **6** |
| `LENGTH_MAX_RECOVERY_RETRIES` | APP-079 | **1** (subset of above) |
| `NARRATION_VERIFY_MAX_RETRIES` | APP-083 | **5** (subset of above) |

**Stacking rule:** One counter `narration_llm_attempts` increments on every `chat_completion` whose output is a candidate for player-visible prose on this turn (creation flavor, exploration terminal, combat terminal, `_narrate_only`). When `narration_llm_attempts >= NARRATION_LLM_MAX_ATTEMPTS`, stop — ship code body + footer only (creation) or safe static fallback (other modes). Log `narration_llm_budget_exhausted`.

- Length retry and verify retry **both** consume the shared counter.
- At most **one** attempt may be tagged `length_recovery_retry` per turn (`LENGTH_MAX_RECOVERY_RETRIES`).
- APP-079 may land **before** APP-083 Phase 1; helper signature must allow 083 to call it inside `narrate_with_verification` without duplicating logic.

### When length surfaces as verify fail (083-only path)

If 079 `pass` (provider did not flag length) but prose is truncated table garbage, APP-083 **duplicate_table** / **catalog** rules fail → verify retry. If provider **did** flag length and 079 did not discard (bug or `body_pending=false`), 083 failure is acceptable backstop — tests should prefer asserting 079 `discard_flavor` + `llm_truncation_recovery` log, not only absence of duplicate headers.

## Requirements

### R1: Central policy helper

**Acceptance criteria**

- [ ] `handle_finish_reason_length` implemented in `orchestrator.py` (or small `truncation.py` if Dev prefers — still APP-079 expected files).
- [ ] Returns `LengthRecoveryResult`; never raises into turn loop.
- [ ] `finish_reason != "length"` → `action=pass`, content unchanged.

### R2: Creation gated steps — discard, no retry

**Acceptance criteria**

- [ ] `_auto_present_*` paths that compose with **authoritative code mechanical blocks** (§ Semantics table: RACE, CLASS, SKILLS, SPELL_SCHOOLS, SPELLS, EQUIPMENT_GOLD, ROLL_STATS, FINALIZE→WORLD_INTRO handoff via `_auto_finalize`) pass `body_pending=True`, `flavor_only=False` into flavor fetch / `handle_finish_reason_length`.
- [ ] `_auto_present_name` passes `body_pending=False`, `flavor_only=True` — static prompt `body` does **not** trigger discard (R3 owns retry/fallback).
- [ ] On `length` with `body_pending=True`, flavor discarded before `_compose_creation_narration`.
- [ ] Composed narration contains **one** table header from code body (RACE, SKILLS integration tests) and finalize handoff shows code summary without truncated banter above it.
- [ ] `llm_truncation_recovery` logged with `action=discard_flavor`, `mode=creation`, `step=<step>`.

### R3: Creation flavor-only — bounded retry or static fallback

**Acceptance criteria**

- [ ] NAME (and other flavor-only steps): one retry with tightened prompt when content `< LENGTH_RETRY_MIN_CHARS` or `length`.
- [ ] After retry still `length` or budget exhausted → static fallback string (step-specific or generic clerk line).
- [ ] Max one `length_recovery_retry` per turn.

### R4: Exploration / combat terminal recovery

**Acceptance criteria**

- [ ] Terminal `length`: one short-prose retry; then eligible `_last_content` or static fallback.
- [ ] Final combat `chat_completion` (~1966) wired — not only `_narrate_flavor`.
- [ ] Mid-chain: table strip on assistant content, no content-only retry.

### R5: Observability

**Acceptance criteria**

- [ ] `log_llm_truncation_recovery(mode, step, action, content_length, attempt)` in `logger.py` (or orchestrator wrapper).
- [ ] Changelog row in `app-logging-qa-spec.md` on ticket close.

### R6: APP-083 handoff contract

**Acceptance criteria**

- [ ] Orchestrator spec documents pipeline order and shared budget (this ticket’s domain spec §).
- [ ] Helper callable from future `narrate_with_verification` without signature break.
- [ ] No double-counting: length discard does not increment verify attempt counter.

## Test plan

```bash
cd app && python -m pytest tests/test_llm_truncation_recovery.py -q
cd app && python -m pytest tests/test_creation_tables.py tests/test_creation_flavor_sanitize.py -q
cd app && python -m pytest tests/ -q
```

| Test | Setup | Pass |
|------|-------|------|
| `test_creation_length_discards_flavor_when_body_pending` | Mock `_narrate_flavor` → `length` + partial `\| Race \|` row; drive RACE present | Single `\| Race \| Adjustments \|` from body; `llm_truncation_recovery` `discard_flavor` |
| `test_finalize_length_discards_flavor_ships_summary` | Mock `_auto_finalize` flavor → `length`; drive FINALIZE | Code HP/MP/Fortune/GP/skills/kit summary visible; no truncated banter; `discard_flavor` logged |
| `test_narrate_flavor_length_short_retries_or_fallback` | Stub `length` + 10-char content; NAME step | One retry OR static fallback; ≤2 sentences in output |
| `test_skills_length_ships_code_table_only` | Integration: SKILLS present, LLM `length` + truncated skills table | Full `format_skills_table` visible; no truncated LLM table above |
| `test_exploration_length_fallback_last_content` | Mock terminal `_llm_loop` `length` after prior `stop` content | Returns prior good content |
| `test_mid_chain_length_strips_tables_continues` | Assistant `length` + tool_calls | Loop continues; table lines stripped from appended assistant message |
| `test_shared_budget_caps_retries` | Mock repeated `length` / verify fail | After 6 attempts, fallback; `narration_llm_budget_exhausted` logged (when 083 wired, joint test may live in `test_narration_verify.py`) |

Use `_patch_llm_content(..., finish_reason="length")` from `conftest.py`.

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py`
- `app/gm/logger.py` _(optional but recommended for `llm_truncation_recovery`)_
- `app/tests/test_llm_truncation_recovery.py`
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-character-creation-spec.md` _(cross-link § finish_reason recovery on close)_
- `tmp/app-logging-qa-spec.md` _(event row on close)_

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Creation long steps:** SKILLS / SPELL_SCHOOLS / SPELLS — if model hits token cap, player sees code table only (no torn markdown above).
- **NAME:** Long name banter truncated — still get intelligible name prompt, not half a table.
- **Exploration:** Long tool-chain turn — final narration complete or sensibly shortened, not mid-sentence cut-off.
- **Logs:** Filter `llm_truncation_recovery` in `app/logs/session-*.jsonl` during creation stress — actions match matrix.

## Pointers

- **Research:** [research-brief.md](./research-brief.md)
- **Domain truth:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — § `finish_reason: length` recovery
- **Peer ticket:** [APP-083](../../app-083-creation-flavor-verification-gate.md) — verify gate, shared budget
- **Related:** APP-072/073 (strippers), APP-078 (generic table strip), APP-077 (exploration footer)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | PM draft: recovery matrix, APP-083 coordination, shared budget, test mapping |
| 2026-05-21 | PM r2: § Semantics per-step table; R2 gated-step list (excludes NAME); FINALIZE/WORLD_INTRO handoff `body_pending=true` |
