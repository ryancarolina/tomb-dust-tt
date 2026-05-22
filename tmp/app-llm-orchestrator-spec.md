# Spec — App LLM Orchestrator

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/orchestrator.py`, `narration_verify.py`, `tool_args.py`, `tools.py`, `context.py`, `system_prompt.py`, `openrouter.py`, `choice_memory.py`

---

## Spec

Turn loop: **player input → context → LLM (+ tools) → narration → UI/TTS**.

### Mechanical truth (non-negotiable)

**Code state leads narration.** Player must not see outcomes (PRE_DELVE, combat hits, site entry, loot) unless the matching bridge/tool call returned `"ok": true`.

### Mechanical-truth narration gate (APP-083)

**Policy:** **TurnTruth in → verify out → retry until pass → publish.** Code owns mechanical truth; the LLM adds 1–3 sentences of clerk/scene banter **inside** those bounds. Failed prose is **never** shown to the player; retries are bounded; exhaustion ships code-owned fallback only (body/footers still append as today).

**Sibling layer:** Tool/FSM gates (APP-080, bridge, combat FSM) answer *"did the action happen?"* The narration gate answers *"does the story match what happened?"* Both stay; neither replaces the other.

#### Pipeline

```text
Mechanics in code  →  TurnTruth built  →  truth injected into LLM prompt
       →  LLM drafts fitting prose  →  verify(prose, truth)
       →  fail? retry (same truth + violation feedback)  →  pass? publish
```

```text
         ┌─────────────────────────────────────┐
         │         CODE (rules / engine)        │
         │  FSM · tools · catalogs · status     │
         └──────────────┬──────────────────────┘
                        │ TurnTruth
            ┌───────────┴───────────┐
            ▼                       ▼
   format_turn_truth_for_prompt   verify_narration
            │                       ▲
            ▼                       │
         ┌─────────────────────────────────────┐
         │   LLM (banter; truth in context)     │
         └──────────────┬──────────────────────┘
                        │ fail → retry (same truth)
                        ▼ pass
         ┌─────────────────────────────────────┐
         │   PUBLISH: verified prose + code     │
         │   blocks + footers → UI / TTS        │
         └─────────────────────────────────────┘
```

Injecting truth **reduces** hallucination rate; verification **guarantees** nothing false ships. Do not rely on prompt alone — creation Sumpty repro (`app/logs/session-2026-05-21.jsonl` L4743/L4749/L4755) shows models invent catalogs without allowed lists in context.

#### `TurnTruth`

One snapshot type; mode-specific builders read the same sources as mechanics (never parse markdown back).

```python
TurnTruth(
    mode: Literal["creation", "exploration", "combat"],
    step: str | None,                    # creation FSM step
    engine: dict,                        # bridge.status() slice
    tool_results: list[ToolResult],      # this turn, in order
    allowed: AllowedClaims,              # what prose MAY reference
    forbidden: ForbiddenClaims,          # hard deny patterns
    code_blocks: list[str],              # hints: what code will append (not full tables)
)
```

| Mode | Builder | Status (APP-083) |
|------|---------|------------------|
| **creation** | `build_creation_turn_truth(creation)` | **Phase 1 — done** |
| **exploration** | `build_exploration_turn_truth(status, tool_results, gate_flags)` | **Phase 2 — future** (`app-exploration-delve-spec.md`) |
| **encounter** | `build_encounter_turn_truth(status, encounter_phase, tool_results, gate_flags)` | **APP-089** — pre-combat; verify before `start_combat` |
| **combat** | `build_combat_turn_truth(status, combat_state, mechanical_slice, phase_label)` | **APP-090** — per-phase verify in `_combat_llm_loop_inner` |

#### Truth-as-context

**Helper:** `format_turn_truth_for_prompt(truth) -> str` — compact system block:

```text
## Authoritative facts (do not contradict)
Step: SPELL_SCHOOLS
Rule: Choose Divine + 1 other school (2 total).
Allowed schools: Pyromancy, Ward, Biomancy, Necromancy, Ether, Divine
Committed: name Sumpty, race Undead, class Novice, skills …
Code will append: full school pick table — do not duplicate
```

**Prompt contract (all modes when gated):**

- Include the authoritative facts block derived from `TurnTruth`.
- Instruct: *"The UI will append code-owned tables/footers below your prose. Write 1–3 sentences of clerk/scene banter only. Do not list picks, stats, kit, gold, schools, spells, or outcomes — reference the facts block if needed."*
- On **retry**, re-send the **same truth block** plus *"Your last draft violated: {violations}. Rewrite banter only."*
- Do **not** dump full markdown tables when code body will append them — send allowed ids/names + rules only.

**Phase 1 wire:** `_creation_flavor_messages` includes `format_turn_truth_for_prompt(build_creation_turn_truth(...))` — replaces thin committed-only block for gated steps. Exploration `build_state_context` extends/replaces with truth block in Phase 2 (one builder, two formatters: prompt vs verify).

#### `verify_narration(prose, truth) -> VerificationResult`

Single entry point; mode delegates to rule sets. Outcomes: **pass** | **fail(violations: list[str])** — no scrub-and-ship as primary policy.

| Rule class | Applies | Examples |
|------------|---------|----------|
| Universal | all | no duplicate code tables; no `Awaiting:` / fake status tags in flavor |
| Catalog | creation (+ spell lists in play) | no school/spell outside allowed; generic TTRPG denylist |
| Economy | creation equipment, vendors (Phase 4 in play) | no GP/kit claims ≠ truth |
| Spatial | exploration (Phase 2) | no interior fiction when `mode=surface` and entry tool not ok (APP-024 → verify fail) |
| Combat outcome | exploration + combat (Phases 2–3) | no hit/damage/kill unless matching tool ok (APP-028 → verify fail) |
| Stat/mechanical | creation rolls, combat HP (Phase 3) | no numbers contradicting engine snapshot |

**Verify boundary:** flavor/assistant prose only — never code `body` or explicit code `footer`.

#### `narrate_with_verification(...) -> str`

Shared orchestrator helper:

1. Build `TurnTruth` for current turn (or accept pre-built).
2. Build LLM messages with `format_turn_truth_for_prompt(truth)` in system context.
3. Generate LLM prose (`_narrate_flavor` or mode equivalent) → `log_llm_response` → **`handle_finish_reason_length` (APP-079)** on candidate prose.
4. `verify_narration(prose, truth)` → pass → return prose for compose.
5. Fail → log `narration_verify_fail` → append violation feedback → goto 3 (if `narration_llm_attempts < NARRATION_LLM_MAX_ATTEMPTS`).
6. After budget exhausted → log `narration_verify_exhausted` and/or `narration_llm_budget_exhausted` → return `""` or code-owned fallback; compose still appends body/footers.

**Emit once** per turn after pass (or exhaustion) — UI/TTS never see intermediate failures.

#### Where it wires in

| Path | Phase | Target |
|------|-------|--------|
| `_creation_turn` / `_compose_creation_narration` | **1** | All creation flavor via `narrate_with_verification`; compose after verified flavor |
| `_llm_loop` exploration return | **2** | Verify full prose + retry before `_compose_exploration_narration` |
| `_combat_llm_loop_inner` return | **3** | Verify + retry; supplement APP-028 failure prefix |
| Code-only paths (errors, resume) | — | Unchanged — no LLM |

#### Phase 1 batch close (APP-083)

**Ticket `done` for this batch when Phase 1 AC is met.** Phases 2–3 are documented here and in the ticket but **not** required for close — follow-on work reuses the same module.

Phase 1 deliverables:

- `app/gm/narration_verify.py` — `TurnTruth`, `verify_narration`, `format_turn_truth_for_prompt`
- `app/gm/creation.py` — `build_creation_turn_truth`
- `app/gm/orchestrator.py` — `narrate_with_verification`; all creation flavor call sites
- Creation rule matrix: [`app-character-creation-spec.md`](app-character-creation-spec.md) § Mechanical-truth narration gate (APP-083 Phase 1)
- Tests: `app/tests/test_narration_verify.py` — Sumpty violations, benign banter, mock retry integration

**Subsumed (Phase 1 docs):** APP-082; creation flavor slices of APP-078/059/073 — verify rules replace strip-first as pass gate; compose strippers optional defense-in-depth until consolidated.

**Future phases:** APP-024 site-entry strip → exploration verify rules (Phase 2); APP-028 combat failure prefix → combat verify rules (Phase 3); economy/inventory prose (Phase 4).

**APP-089 / APP-090 coordination (2026-05-22):** Encounter FSM uses `build_encounter_turn_truth` + verify before `start_combat`. After `start_combat` ok, only `build_combat_turn_truth` per combat phase (APP-090) — encounter verify **must not** run in `_combat_llm_loop_inner`. Schedule: APP-083 Phase 2 encounter builder with APP-089; Phase 3 per-phase combat builder with APP-090.

#### Observability

JSONL events (implement with `app-logging-qa-spec.md` sync):

| Event | When |
|-------|------|
| `narration_verify_fail` | Each failed attempt (`mode`, `step`, `violations`, `attempt`) |
| `narration_verify_pass` | Success (`attempts`) |
| `narration_verify_exhausted` | Circuit breaker |

#### Config

| Key | Default | Purpose |
|-----|---------|---------|
| `NARRATION_LLM_MAX_ATTEMPTS` | `6` | Shared cap per published turn — length recovery (APP-079) + verify retries (APP-083) |
| `NARRATION_VERIFY_MAX_RETRIES` | `5` | Max verify-regeneration attempts (subset of shared cap) |
| `LENGTH_MAX_RECOVERY_RETRIES` | `1` | Max length-specific retries per turn (subset of shared cap) |

#### Non-goals

- Replacing tool/FSM enforcement (bridge still authoritative for state changes).
- Verifying player-authored input.
- UI wait indicator for retries (optional later).
- Canon `build/systems/` content changes.

**Ticket:** [APP-083](backlog/app-083-creation-flavor-verification-gate.md) · **Run spec:** [spec.md](backlog/runs/app-083-mechanical-truth-narration-gate/spec.md)

**APP-079 coordination:** Length truncation runs **before** verify — see § **`finish_reason: length` recovery** below. Shared `NARRATION_LLM_MAX_ATTEMPTS` budget applies to length retries and verify retries together.

### `finish_reason: length` recovery (APP-079)

**Problem:** Every LLM call logs `finish_reason` but, until APP-079 lands, truncated `"length"` responses are composed and emitted as-is. Creation flavor at `_CREATION_FLAVOR_MAX_TOKENS = 120` frequently cuts mid-table; exploration/combat terminal narration can truncate at config `max_tokens`.

**Policy:** Central helper `handle_finish_reason_length(response, *, mode, creation_step, body_pending, flavor_only, attempt) -> LengthRecoveryResult` runs immediately after `log_llm_response` on every path that feeds player-visible prose. Post-hoc strippers (APP-072/073/078) and APP-083 verify rules remain **defense in depth** — they do not replace discard-on-length when code `body` is pending.

#### Semantics: `body_pending` vs `flavor_only`

| Flag | Meaning |
|------|---------|
| `body_pending=True` | Compose includes an **authoritative code mechanical block** ( `format_*_table()`, roll-stats readout, equipment summary, finalize character summary). On `length` → **`discard_flavor`**, no length retry. |
| `flavor_only=True` | Creation path where LLM flavor is primary; `body` is static prompt copy only (NAME). On `length` → one retry or static fallback. |
| **Invariant** | `body_pending=True` ⇒ `flavor_only=False` |

**Not `body_pending`:** error prefixes, static prompt lines, footer tags alone.

##### Per-step wiring (creation)

| Step | `body_pending` | `flavor_only` | On `length` |
|------|----------------|---------------|-------------|
| NAME | `false` | `true` | Retry or static fallback |
| RACE, CLASS, SKILLS, SPELL_SCHOOLS, SPELLS, EQUIPMENT_GOLD | `true` | `false` | `discard_flavor` |
| ROLL_STATS | `true` | `false` | `discard_flavor` |
| FINALIZE → WORLD_INTRO (`_auto_finalize`) | `true` | `false` | `discard_flavor` (code summary + footer) |
| `_creation_table_flavor` error path | n/a | n/a | LLM not called |

Post-finalize WORLD_INTRO handoff is **`body_pending=true`** — not flavor-only. Later `WORLD_INTRO` + `active=False` turns use exploration terminal policy via `process_turn`.

#### Recovery matrix

| Context | On `length` | Length retry |
|---------|-------------|--------------|
| Creation gated step (see per-step table) | **Discard flavor** (`""` before compose) | No |
| Creation flavor-only (NAME) | One retry (“≤2 sentences, no tables”) or static fallback | Yes (1× per turn max) |
| Creation FINALIZE / WORLD_INTRO handoff | **Discard flavor** — ship code summary + footer | No |
| Exploration / combat terminal | One retry (“≤3 sentences”); then eligible `_last_content` or static fallback | Yes (1× per turn max) |
| Tool loop mid-chain (has `tool_calls`) | Strip markdown table blocks from assistant content; continue loop | No |

**`_last_content` fallback:** only when prior snippet in the same loop had `finish_reason == "stop"` (or absent) and non-empty content — never stale empty tool-round shells.

**Constants:** `LENGTH_RETRY_MIN_CHARS = 32`; `LENGTH_MAX_RECOVERY_RETRIES = 1` per turn.

#### Wire points

| Call site | Mode |
|-----------|------|
| `_narrate_flavor`, `_narrate_creation_flavor` | creation |
| `_llm_loop` (terminal + mid-chain) | exploration |
| `_combat_llm_loop_inner`, `_narrate_only` | combat |

Creation: when `body_pending` and action is `discard_flavor`, `_compose_creation_narration("", body, …)` — code table + footer only.

#### Integration with APP-083 (`narrate_with_verification`)

```text
chat_completion → log_llm_response
  → handle_finish_reason_length (079)
       if body_pending + length → discard_flavor (do not verify discarded text)
  → verify_narration (083) on surviving candidate prose
       truncated tables / catalogs → verify fail → retry (shared budget)
  → compose + emit once
```

| Case | APP-079 | APP-083 |
|------|---------|---------|
| Creation + `body_pending` + `length` | **Discard before verify** | Verify surviving flavor (often empty) |
| Flavor-only / exploration / combat terminal | Length retry or fallback first | Verify published candidate |
| Mid-chain with tools | Table strip only | N/A until terminal prose |

When 079 already discarded or fell back, 083 still verifies what will publish (static fallbacks must pass or be pre-approved).

**Implement order:** APP-079 helper may land standalone on `_narrate_flavor` / `_llm_loop` before APP-083 Phase 1; APP-083 refactor must call the same helper inside `narrate_with_verification` step 3 — no duplicated logic.

#### Observability (APP-079)

| Event | When |
|-------|------|
| `llm_truncation_recovery` | Every policy action (`discard_flavor`, `retry`, `fallback_last_content`, `fallback_static`) — `mode`, `step`, `action`, `content_length`, `attempt` |
| `narration_llm_budget_exhausted` | Shared cap hit (joint with APP-083) |

#### Tests (APP-079)

```bash
cd app && python -m pytest tests/test_llm_truncation_recovery.py -q
```

| Case | Expected |
|------|----------|
| Creation RACE/SKILLS + `length` flavor + body pending | Single code table; `discard_flavor` logged |
| NAME + short `length` content | One retry or static fallback (`body_pending=false`, `flavor_only=true`) |
| FINALIZE handoff + `length` flavor | Code summary + footer; `discard_flavor` logged |
| Exploration terminal + `length` | Retry then eligible `_last_content` |
| Mid-chain + `length` + tools | Loop continues; tables stripped from assistant append |

**Ticket:** [APP-079](backlog/app-079-finish-reason-length-recovery-policy.md) · **Run spec:** [spec.md](backlog/runs/app-079-finish-reason-length-recovery/spec.md)

### Modes

| Mode | When | Behavior |
|------|------|----------|
| Creation | `creation.active` | Only creation handlers — no exploration tool loop; `_llm_loop` blocked when active |
| Combat | `combat.active` or engine combat | `combat_fsm` + combat tools |
| Exploration | default | `status`/`check`/`suggest` context + full tool set |

### Tools (`tools.py`)

Schemas must match `bridge.py` method signatures. When adding a tool:

1. Add bridge method (gamebridge spec).
2. Add tool schema here.
3. Add handler in `orchestrator._dispatch_tool`.
4. Update `system_prompt.py` usage rules.
5. Update this spec checklist.

**APP-080:** LLM JSON args are normalized in orchestrator (`normalize_tool_args`) before bridge dispatch — bridge assumes clean Python types. See [APP-080](backlog/app-080-normalize-tool-args-before-dispatch.md) and [GameBridge spec](app-gamebridge-spec.md) (typed-args contract).

### Tool argument normalization (APP-080)

**Problem:** Raw `json.loads` output may contain string-typed integers, XML/tool markup bleed from merged tool calls, or legacy param names. Passing these to `GameBridge` causes `TypeError` (e.g. `remember_fact.importance` → `semantic.remember` clamp) and silent memory loss when the LLM retries a different tool.

**Boundary:** Same pattern as creation flavor sanitizers (APP-073) — sanitize **structured tool args** before mechanical dispatch, not assistant prose.

| Step | Location | Action |
|------|----------|--------|
| 1 | `_llm_loop`, `_combat_llm_loop_inner`, `_creation_llm_loop` | `args = json.loads(...)`; on `JSONDecodeError` → `{}` |
| 2 | Same | `args = normalize_tool_args(fn_name, args)` |
| 3 | Same | `err = validate_tool_args(fn_name, args)`; if `err` → `{ok: false, error: err}` and skip dispatch |
| 4 | `_execute_tool` / `_execute_combat_action` / `_execute_creation_choice` | Dispatch with coerced dict; bridge assumes clean types |

**Module:** `app/gm/tool_args.py` (preferred).

#### Helpers

| Function | Contract |
|----------|----------|
| `normalize_tool_args(tool_name, args) -> dict` | Tool-specific coercions + generic fallbacks; drops unknown keys for tools with fixed bridge signatures; never raises |
| `validate_tool_args(tool_name, args) -> str \| None` | After normalize: returns `"<field> required"` or `None`; orchestrator loops short-circuit before bridge |
| `_coerce_int(value, default, *, min_v, max_v) -> int` | If `str`, strip markup then extract leading digits via regex; invalid → `default`; clamp to `[min_v, max_v]` |
| `_strip_tool_markup(s: str) -> str` | Remove fragments: `</invoke>`, `<invoke`, `</parameter>`, `<parameter`, etc. — apply on short scalars before numeric coercion |

#### Coercion table (v1)

| Tool | Field | Coercion |
|------|-------|----------|
| `remember_fact` | `fact` | `str()`; required — empty/missing → normalization failure |
| `remember_fact` | `entities` | `list[str]`; drop non-strings; default `[]` |
| `remember_fact` | `importance` | int 1–5; default 3; markup strip + `_coerce_int` — **regression:** `"4</importance>…"` → `4` |
| `memory_recall` | `query` | `str()`; required |
| `memory_recall` | `top_k` | int ≥ 1; default 5; string `"5"` → `5` |
| `memory_recall` | `top` (legacy) | Rename to `top_k` then coerce (APP-048 name + APP-080 type) |
| `fortune_spend` | `character_id` | `str()` + markup strip; required |
| `fortune_spend` | `amount` | **Drop** — not in app tool schema or bridge; engine CLI supports `amount`; bridge always spends 1 |
| `clock_tick` | `clock` | `str()`; required |
| `clock_tick` | `segments` | int ≥ 1; default 1 |
| `enter_dungeon` | `site_address` / `site_id` | `str()`; if only `site_id` present, set `site_address` from it (migrated from ad-hoc `_execute_tool` rewrite) |
| `set_creation_choice` | `step`, `value` | `str()`; both required (creation loop) |
| `combat_action` | `action`, `actor_id`, … | `str()` on present keys; `action` + `actor_id` required (combat loop) |
| Generic | string fields | `str()` on known tools when value present |
| Generic | array fields | Ensure `list`; filter element type when schema declares `items.type` |

Expand table incrementally; do not block APP-080 on every tool if `remember_fact` regression + unit tests are green.

#### Failure modes

- Coercion must **not** raise into `_execute_tool`'s generic `except Exception` for v1 fields.
- Missing/unrecoverable required field after normalize → `{ok: false, error: "<field> required"}` before bridge call.
- Optional (APP-034): log `tool_arg_coerced` JSONL when raw ≠ coerced (tool name, field, raw, coerced).

#### Non-goals (v1)

- Full JSON Schema validator for every tool.
- Code-owned quest memory from player prose.
- Markup stripping on long prose fields (`fact`) unless session evidence requires it — scalars first.
- Engine/bridge `int()` belt-and-suspenders in `semantic.remember` — orchestrator is primary.
- Exposing `fortune_spend.amount` in tools/bridge (separate ticket if needed).

### Transcript sanitize (APP-031)

**Problem:** In-turn tool loops build ephemeral `messages` arrays across `_llm_loop`, `_creation_llm_loop`, and `_combat_llm_loop_inner`. Malformed assistant `tool_calls` (empty array, missing `id`/`function.name`, merged XML in arguments) plus appended `tool` results cause provider **400** on the next depth:

```text
Tool-call assistant message produced no valid function calls but is followed by tool result messages
```

Persisted `self.history` stores only `{role: user|assistant, content}` — tool rounds are dropped before persist. Failure surface is **in-turn arrays only**. APP-080 coerces args before dispatch but does not repair the transcript.

**Policy:** **Proactive sanitize before send** — every orchestrator `chat_completion` receives a repaired array. APP-032 (reactive 400 → truncate/retry once) is the safety net; reuse the same helper after truncate.

**Boundary:** Sanitize the API **`messages` array** — not player-facing prose (APP-073/083), not tool args (APP-080). Implementation lives in **`orchestrator.py`** (ticket scope); `openrouter.chat_completion` remains pass-through.

#### Helper contract

`sanitize_transcript_messages(messages) -> list[dict]`:

- Returns a **new** list; shallow-copies message dicts into the output.
- **Must not** mutate the caller’s input list or dicts already in that list (shared arrays for APP-032).
- Never raises. Walk input left-to-right per invariants below; drop/reorder invalid entries.
- **Safe-prefix fallback:** if the walk would yield **empty** output while input was non-empty: (1) all leading `system` messages from input, in order; (2) if any `user` exists, append the **last** `user` only; (3) otherwise `[]`. Empty input → `[]`.

#### Invariants

After `sanitize_transcript_messages(messages)`:

| Rule | Action |
|------|--------|
| Valid `tool_call` | Non-empty `id`; `function.name` non-empty string; `function.arguments` present (string) |
| Invalid entries in `tool_calls` | Stripped from assistant message |
| Assistant with no valid calls after strip | Content-only assistant (no orphan `tool_calls`) |
| Each `tool` message | `tool_call_id` matches an `id` from nearest preceding assistant with unresolved valid calls |
| Unmatched `tool` messages | Dropped |
| Valid multi-tool chain | Preserved unchanged (ids + order) |
| Walk yields empty but input non-empty | Safe-prefix fallback (see Helper contract) |

#### APP-028 ordering

Exploration/combat failure paths insert `system` “TOOL FAILED …” between assistant `tool_calls` and `tool` results. Sanitizer **reorders**: all `tool` messages for that round immediately follow the assistant; intervening `system`/`user` messages move **after** the tool block (content preserved).

#### Wire points

Preferred: orchestrator wrapper (e.g. `_chat_completion`) calling `sanitize_transcript_messages` then `openrouter.chat_completion`.

| Call site | Context |
|-----------|---------|
| `_call_narration_llm` | Creation flavor |
| `_narrate_only` | Combat narrate |
| `_creation_llm_loop` | Creation tools |
| `_combat_llm_loop_inner` | Combat tools |
| Combat narrate pass | Full chain + user brief, `tools=None` |
| `_llm_loop` | Exploration tools |

#### APP-031 vs APP-032

| Ticket | Role |
|--------|------|
| **APP-031** | Always sanitize before send; enforce invariants |
| **APP-032** | On malformed-transcript 400, truncate to safe prefix, sanitize, retry **once** |

Shared primitives: `sanitize_transcript_messages`, `_safe_prefix_fallback` — no duplicate repair logic.

#### Observability (optional v1)

When drops/reorders occur: JSONL `transcript_sanitized` (`dropped_tools`, `stripped_calls`, `reordered_system`) — may defer to APP-034.

#### Tests (APP-031)

```bash
cd app && python -m pytest tests/test_transcript_sanitize.py -q
```

| Case | Expected |
|------|----------|
| Orphan `tool` with no preceding assistant `tool_calls` | Removed |
| Assistant `tool_calls: []` + following `tool` | Orphan tools stripped; assistant de-tooled |
| Invalid `tool_calls` (missing `id` / `function.name`) + `tool` | Invalid calls stripped; orphan tools removed |
| Valid assistant + two tools, one id unmatched | Unmatched `tool` dropped |
| Assistant → system TOOL FAILED → `tool` | Tools immediately after assistant; system after tool block |
| Valid multi-tool chain round-trip | All ids preserved |
| Mock `_llm_loop` depth ≥1 | `chat_completion` `messages` satisfy invariants |
| Caller list + dict refs unchanged after sanitize | Non-mutating contract |
| Tool-only input, or invalid tail after valid prefix | Safe-prefix fallback per Helper contract |

Use pytest fixtures for Holt-session malformed arrays — not gitignored session JSONL in CI.

**Ticket:** [APP-031](backlog/app-031-transcript-sanitize-orphan-tool-messages.md) · **Run spec:** [spec.md](backlog/runs/app-031-transcript-sanitize-orphan-tool-messages/spec.md)

### Reactive 400 retry (APP-032)

**Problem:** APP-031 eliminates most orphan-tool / ordering failures proactively, but strict providers (Google via OpenRouter) may still reject an in-turn array with **400 Bad Request**. Uncaught exceptions reach caller `except Exception` paths — exploration returns `"The GM falters. (API error: …)"` and the turn dies.

**Policy:** **Reactive truncate → sanitize → retry once** inside `Orchestrator._chat_completion`. APP-031 runs first on every call; APP-032 is the safety net when sanitize alone is insufficient.

**Boundary:** Same as APP-031 — in-turn `messages` arrays only; `openrouter.chat_completion` remains pass-through.

#### Detection

`is_malformed_transcript_400(exc) -> bool` — **narrow** classification; unrelated 400s must not retry.

| Condition | Required |
|-----------|----------|
| Exception type | `openai.BadRequestError` or `openai.APIStatusError` with `status_code == 400` |
| Message heuristic | `str(exc)` (case-insensitive) matches ≥1 transcript substring: `tool-call assistant message produced no valid function calls`; `no valid function calls but is followed by tool`; or `tool result messages` when `tool_call` / `tool_calls` also present |
| Unrelated 400 | No retry — e.g. invalid model, API key, context length |

#### Retry pipeline (`_chat_completion`)

```text
clean = sanitize_transcript_messages(messages)
try: return chat_completion(…, messages=clean)
except exc:
  if not is_malformed_transcript_400(exc): raise
  truncated = _safe_prefix_fallback(messages)   # caller's original array
  retry_clean = sanitize_transcript_messages(truncated)
  return chat_completion(…, messages=retry_clean)   # exactly one retry; re-raise on failure
```

| Rule | Contract |
|------|----------|
| Retry budget | **Once per `_chat_completion` invocation** — each loop depth may retry independently |
| Non-mutating | Caller `messages` list/dicts unchanged; retry uses internal copies only (APP-031 contract) |
| Truncate floor | Leading `system` messages + last `user` only (`_safe_prefix_fallback`) — drops in-turn tool chain |
| Kwargs | Second attempt uses same `tools`, `tool_choice`, `max_tokens`, `temperature` |
| Success | Return value indistinguishable from first-attempt success |
| Exhaustion | Second failure re-raises; existing caller fallbacks unchanged |

#### Wire point

Single intercept in `_chat_completion` — all six APP-031 call sites inherit retry without duplicate logic.

#### Observability (optional v1)

On retry path: JSONL `transcript_400_retry` (`attempt`, `prefix_len`, `original_len`) — may defer to APP-034 alongside `transcript_sanitized`.

#### Tests (APP-032)

```bash
cd app && python -m pytest tests/test_transcript_400_retry.py -q
```

| Case | Expected |
|------|----------|
| Malformed-transcript 400 then success | 2 HTTP attempts; 2nd `messages` satisfies invariants + safe-prefix shape |
| Unrelated 400 (invalid model) | No retry; exception propagates |
| Malformed 400 twice | Propagates after 2 attempts |
| Non-400 (429, connection) | No retry |
| `is_malformed_transcript_400` parametrize | Google string → true; unrelated → false |
| Caller list immutability | Shared `messages` ref unchanged after retry |
| `_llm_loop` depth ≥1 integration | Turn completes without GM falters fallback |

**Ticket:** [APP-032](backlog/app-032-400-retry-on-malformed-transcript.md) · **Run spec:** [spec.md](backlog/runs/app-032-400-retry-malformed-transcript/spec.md)

---

## Task checklist

- [x] `process_turn` with creation / combat / exploration branches
- [x] Tool dispatch to GameBridge
- [x] LLM loop with depth limit for tool chains
- [x] `build_state_context` from status + recap + inventory
- [x] Block `_llm_loop` during active character creation (APP-008)
- [x] Normalize + validate LLM tool args before bridge dispatch (APP-080)
- [x] Mechanical-truth narration gate — Phase 1 creation verify+retry (APP-083)
- [x] `finish_reason: length` recovery policy — creation paths + exploration fallback (APP-079)
- [x] Transcript sanitize — orphan tool messages before every `chat_completion` (APP-031)
- [x] Reactive 400 retry on malformed transcript in `_chat_completion` (APP-032)
- [ ] Mechanical-truth narration gate — Phase 2 exploration (APP-083 follow-on)
- [ ] Mechanical-truth narration gate — Phase 3 combat (APP-083 follow-on)

**Open work:** [APP-083](backlog/app-083-creation-flavor-verification-gate.md) (Phase 1 creation in batch), [APP-022](backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md), [APP-028](backlog/app-028-combat-tool-failure-narration.md) (subsumed Phase 3), [APP-033](backlog/app-033-sqlite-threading-policy.md)–[APP-034](backlog/app-034-log-tool-chain-on-api-errors.md), [APP-077](backlog/app-077-code-owned-exploration-status-footer.md), [APP-079](backlog/app-079-finish-reason-length-recovery-policy.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Problem (from logs)

- Google 400: *Tool-call assistant message produced no valid function calls but is followed by tool result messages* — see § **Transcript sanitize (APP-031)**
- SQLite cross-thread error (2026-05-18)

---

## Tests

```bash
cd app && python -m pytest tests/test_tool_args.py -q
cd app && python -m pytest tests/test_narration_verify.py -q   # APP-083 Phase 1
cd app && python -m pytest tests/test_llm_truncation_recovery.py -q   # APP-079
cd app && python -m pytest tests/test_transcript_sanitize.py -q   # APP-031
cd app && python -m pytest tests/test_transcript_400_retry.py -q   # APP-032
cd app && python -m pytest tests/ -q
```

**APP-083 Phase 1 (`test_narration_verify.py`):**

| Case | Expected |
|------|----------|
| `format_turn_truth_for_prompt` @ SPELL_SCHOOLS | Allowed school ids/names present; no full duplicate markdown table |
| Sumpty flavor excerpts (L4743/L4749/L4755) | `verify_narration` → `fail` with catalog/economy violations |
| Benign clerk banter (no catalogs) | `pass` |
| Mock LLM bad twice then good | Player sees only passing flavor in composed narration |
| Mock LLM always bad | `narration_verify_exhausted` logged; no bad prose in final emit |

**APP-080 (`test_tool_args.py`):**

| Case | Expected |
|------|----------|
| `_coerce_int("4</importance>…", 3, min_v=1, max_v=5)` | `4` |
| `_coerce_int("abc", 3, …)` | `3` (default) |
| `normalize_tool_args("remember_fact", {corrupted importance, valid fact/entities})` | `importance: int`; no `TypeError` through bridge/memory |
| `normalize_tool_args("memory_recall", {"query": "x", "top_k": "5"})` | `top_k == 5` |
| `normalize_tool_args("memory_recall", {"query": "x", "top": "3"})` | `top_k == 3`; no `top` key |
| `normalize_tool_args("fortune_spend", {"character_id": "pc-1", "amount": "2"})` | only `character_id`; no `amount` |
| Integration: corrupted `remember_fact` through `_execute_tool` | `{ok: true}`; fact persist path (mock bridge or memory assert) |

Use pytest fixtures for Holt-session `importance` payload — not gitignored session JSONL in CI.

- Mock LLM tests in `app/tests/test_orchestrator.py` (when added).
- Session JSONL: every tool call logged with result.

---

## File map

| File | Role |
|------|------|
| `orchestrator.py` | Turn loop, creation/combat branches, `narrate_with_verification` (APP-083) |
| `narration_verify.py` | `TurnTruth`, `verify_narration`, `format_turn_truth_for_prompt` (APP-083) |
| `tool_args.py` | `normalize_tool_args`, `validate_tool_args`, `_coerce_int`, markup strip (APP-080) |
| `tools.py` | OpenAI function schemas |
| `context.py` | State block for LLM |
| `system_prompt.py` | GM persona + rules |
| `openrouter.py` | API client (pass-through; transcript sanitize in orchestrator — APP-031) |
| `choice_memory.py` | Creation choice recall |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | APP-032 done: `is_malformed_transcript_400` narrow 400 classifier; `_chat_completion` truncate via `_safe_prefix_fallback` + sanitize + retry once; `test_transcript_400_retry.py` (R1–R7); pairs with APP-031 proactive sanitize |
| 2026-05-22 | APP-032 PM spec: § Reactive 400 retry — narrow 400 detection, truncate via `_safe_prefix_fallback` + sanitize, once per `_chat_completion`; test module `test_transcript_400_retry.py`; pairs with APP-031 |
| 2026-05-22 | APP-031 done: `sanitize_transcript_messages`, `_safe_prefix_fallback`, `Orchestrator._chat_completion` wired at all six call sites; APP-028 TOOL FAILED reorder at send boundary; `test_transcript_sanitize.py` (T1–T10) |
| 2026-05-22 | APP-031 PM spec: § Transcript sanitize — proactive `sanitize_transcript_messages` before every orchestrator `chat_completion`; invariants, APP-028 reorder, APP-032 pairing; file map clarifies openrouter pass-through |
| 2026-05-22 | APP-031 PM r2: helper non-mutating contract, safe-prefix fallback algorithm, test rows for mutability + tail fallback; ticket Expected files include `test_transcript_sanitize.py` |
| 2026-05-21 | APP-083 Phase 1 done: `narration_verify.py` (`TurnTruth`, `verify_narration`, `format_turn_truth_for_prompt`); `narrate_with_verification` wired on all creation flavor paths; JSONL `narration_verify_*` events |
| 2026-05-21 | APP-079 done: `handle_finish_reason_length` + `LengthRecoveryResult`; discard-on-length when code body pending; NAME flavor retry/fallback; exploration `_llm_loop` falls back to `_last_content`; `test_llm_truncation_recovery.py` |
| 2026-05-21 | APP-079 PM spec: § `finish_reason: length` recovery — recovery matrix, wire points, APP-083 integration (discard before verify when body pending), shared `NARRATION_LLM_MAX_ATTEMPTS` budget |
| 2026-05-21 | APP-079 PM r2: § Semantics per-step `body_pending`/`flavor_only` table; NAME vs gated steps; FINALIZE/WORLD_INTRO handoff discard |
| 2026-05-21 | APP-083 PM spec: § Mechanical-truth narration gate — TurnTruth in/verify out/retry/publish; Phase 1 creation batch close; Phases 2–3 exploration/combat documented as future |
| 2026-05-21 | APP-080 done: `tool_args.py` + three-loop wire (`normalize_tool_args` → `validate_tool_args` → dispatch); Holt `remember_fact` regression tests green; optional `tool_arg_coerced` logging deferred (APP-034) |
| 2026-05-21 | APP-080 PM spec: normative § Tool argument normalization — coercion table, helpers, wire points, tests; `fortune_spend.amount` corrected to `character_id` + drop unknown keys |
| 2026-05-20 | APP-080 spec draft: § Tool argument normalization — `normalize_tool_args` before bridge; `remember_fact.importance` coercion (Fatty/Holt session) |
| 2026-05-20 | APP-008: `_llm_loop` blocked when `creation.active` |
| 2026-05-20 | Spec created; merged mechanical-truth + llm-transcript-resilience content |
