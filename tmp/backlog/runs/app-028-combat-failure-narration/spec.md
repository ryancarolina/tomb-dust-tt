# Spec: APP-028-combat-failure-narration

**Status:** draft (PM r2 — QA spec blockers addressed)  
**backlog_ticket:** APP-028  
**ticket_path:** [tmp/backlog/app-028-combat-tool-failure-narration.md](../../app-028-combat-tool-failure-narration.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-combat-play-spec.md`

## Problem

Combat tool failures are **inconsistently enforced** in the orchestrator. The grave-ghoul / `combat: null` scenario is the highest-impact gap: `process_beat` returns `ok: true` with a `combat_trigger` mechanical item, `_handle_combat_trigger` calls `start_combat_from_trigger`, and on failure **does nothing** — no player-visible error, no `[Mechanics failed — …]`, while the exploration LLM may narrate combat starting from the successful beat payload plus pre-tool assistant prose.

Secondary gaps:

- **`_llm_loop`:** When all tools in a turn fail and the assistant already emitted `content`, the early return is `[Mechanics failed — …]\n\n{content}` — **success fiction leaks** after the failure prefix.
- **`_combat_llm_loop_inner`:** Same `all_failed` + `content` append; **no** exploration-style `TOOL FAILED` system injection.
- **`pending_start`:** `_combat_turn` already returns a correct code-owned failure string when start fails, but `pending_start` is never set `True` in live code; beat-driven starts use `_handle_combat_trigger` instead.

**Evidence:** Research traces + [`app-combat-play-spec.md`](../../../app-combat-play-spec.md) problem lines (`attacker not in combat`, `hollow-knight`, partial `[Mechanics failed]`). Session log `app/logs/session-2026-05-20.jsonl` cited in ticket — gitignored, not replayed locally.

## Goals

- **No success fiction** when combat mechanics did not commit (`status.combat` null / tool `ok: false`).
- **Deterministic code-owned failure text** on every combat-tool failure path (not prompt-only).
- **Beat-driven encounter start failure** (`combat_trigger` → failed `start_combat_from_trigger`) surfaces to the player before exploration LLM continues.
- **`all_failed` turns** never append assistant pre-tool `content` that describes hits, combat start, initiative, or spell effects.

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Engine-side monster id validation at `start_combat` | [APP-027](../../app-027-validate-monster-id-at-combat-start.md) — engine errors exist; APP-028 owns **narration** when `ok: false` |
| Pre-check gating before `combat_attack` dispatch | [APP-026](../../app-026-combat-attack-gating.md) — overlaps failure cases; APP-028 still requires visible failure narration |
| Full combat integration / golden-path fixture | [APP-030](../../app-030-combat-integration-test.md) |
| Changing `beat.process_beat` to emit `ok: false` on trigger | Optional Dev approach; **outcome** is player-visible failure + `combat: null`, not engine contract change |
| Partial-tool-success second narrate pass quality | Relies on `_combat_mechanical_brief` + LLM; acceptable when at least one tool `ok: true` |
| `process_beat` as a “combat tool” | Not in tool inventory; covered under **beat-trigger start failure** (R1) |

## Requirements (summary)

Full behavior and test contracts: domain spec § **Combat tool failure narration (APP-028)**.

### Combat tool inventory

Tools that **must** obey failure narration when `ok: false` (exploration `_llm_loop` via `_execute_tool`, or combat `_combat_llm_loop_inner`):

| Tool | Loop | Typical failure |
|------|------|-----------------|
| `start_combat` | Exploration | Unknown monster JSON, no roster, combat already active |
| `combat_attack` | Exploration | `attacker not in combat`, not your turn |
| `combat_end` | Exploration | No active combat |
| `cast_spell` | Exploration | Not in combat / unknown spell / invalid target |
| `fortune_spend` | Exploration | No Fortune / invalid context |
| `combat_action` | Combat (`COMBAT_ACTION_TOOL` only) | `no active combat`, `not your turn`, engine action errors |
| Wrong tool name in combat loop | Combat | `During combat only combat_action is available` |

**Beat-trigger path (not a tool):** `process_beat` → `_handle_combat_trigger` → `start_combat_from_trigger` — must behave like a failed `start_combat` for narration purposes (R1).

### Requirement IDs

| ID | Summary | Locus |
|----|---------|-------|
| **R1** | **Beat-trigger silent failure:** If `mechanical_summary` contains `combat_trigger` and `start_combat_from_trigger` returns `ok: false`, orchestrator **must** surface code-owned failure to the player **on the same exploration turn** — before any further `chat_completion` narrate pass. `combat.active` stays false; `status.combat` null; **no** `run_combat_monster_turns()`. Failure text **includes** `[Mechanics failed — combat start: {error}]` and a short second line (e.g. `Combat could not begin.`) — **same shape** as `_combat_turn` `pending_start` branch. See **R1 propagation contract** below. | `orchestrator.py` `_handle_combat_trigger`, `_execute_tool`, `_llm_loop` |
| **R2** | **Exploration `all_failed` content strip:** In `_llm_loop`, when every tool call in the turn returns `ok: false`, the returned player string is **`[Mechanics failed — {failures}]` only** — **no** `\n\n` append of assistant pre-tool `content`. Existing per-tool `TOOL FAILED ({name}): …` system injection **remains** for the retry path when not short-circuited. | `orchestrator.py` `_llm_loop` |
| **R3** | **Combat inner `all_failed` content strip:** In `_combat_llm_loop_inner`, when every tool call fails, return **`[Mechanics failed — {failures}]` only** (optional fixed fallback sentence if empty, e.g. `Your action did not resolve.` — **not** model success prose). | `orchestrator.py` `_combat_llm_loop_inner` |
| **R4** | **Combat inner failure injection:** On `ok: false` in `_combat_llm_loop_inner`, append a **system** message equivalent to exploration: `TOOL FAILED (combat_action): … You MUST narrate this failure honestly` (or shared helper) **before** tool result message, when the loop continues (partial failure / depth retry). | `orchestrator.py` `_combat_llm_loop_inner` |
| **R5** | **Exploration combat tools:** For `start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend` with `ok: false`, player-visible outcome on total failure satisfies R2; narration must **not** describe hits, damage, combat start, initiative order, or spell resolution. | `_llm_loop` + bridge results |
| **R6** | **State truth:** After any R1/R5 failure, `bridge.status()` shows `combat: null` (or unchanged non-combat); UI/orchestrator must not enter `_combat_turn` until a successful start. | Integration |
| **R7** | **`pending_start` alignment (optional implementation):** If Dev sets `pending_start` on deferred trigger, `_combat_turn` failure copy in R1 **must** remain the canonical message shape. If trigger path handles failure inline (R1), `pending_start` behavior unchanged for restore/tests. | `combat_fsm.py`, `_combat_turn` |
| **R8** | **Logging:** `log_error` (or equivalent) when R1 short-circuits or R2/R3 strips `content`, including tool names and `error` fields — aids APP-034-style debugging without changing player text. | `orchestrator.py` |

### R1 propagation contract (observable — SPEC-001 / SPEC-004)

**Chosen mechanism:** `_llm_loop` **same-turn short-circuit** after `process_beat` + `_handle_combat_trigger`.

1. **`_handle_combat_trigger(beat_result) -> str | None`**
   - On `start_combat_from_trigger` → `ok: false`: set `combat.active = False`, return canonical string:
     - `[Mechanics failed — combat start: {error}]\n\nCombat could not begin.`
   - On success or no `combat_trigger`: return `None`.
   - **Must not** silently return with no feedback (replaces current `-> None` no-op).

2. **`_execute_tool("process_beat", …)`**
   - After `bridge.process_beat` and `_handle_combat_trigger`, if trigger returns a failure string, store it on the orchestrator instance (e.g. `self._beat_combat_start_failure`) for the current tool batch. Tool JSON returned to the loop may still be engine `ok: true` with `combat_trigger` in `mechanical_summary` — **engine contract unchanged**.

3. **`_llm_loop`**
   - After executing tool calls in the batch, if `self._beat_combat_start_failure` is set: clear the flag and **return that string immediately** as player narration — **do not** append assistant pre-tool `content`, **do not** recurse to `depth + 1`.
   - This is the **authoritative player channel** for grave-ghoul / `combat: null` (dual-channel: tool-role message may still look success-leaning; player text must not).

**Non-goal for R1:** Amending `process_beat` engine result to `ok: false` is optional Dev polish, not required for AC.

### Failure message contract

- **Prefix:** `[Mechanics failed — <tool_or_context>: <error>]` — multiple failures joined with `; ` (existing pattern).
- **Beat-trigger context label:** `combat start` (matches existing `pending_start` branch).
- **Banned in player text on total failure:** prose implying successful attack, damage dealt, enemy defeated, combat joined, initiative rolled, or spell effect applied when **no** combat tool returned `ok: true` and DB combat inactive.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Enforce failure narration for **all** combat tools | R5 + tool table; T3–T7 (exploration); T8–T10 (combat inner) |
| Success fiction when `ok: false` | R1 (T1–T2 short-circuit), R2/R3 (T3–T8 strip), R4 (T10), R5/R6 |
| Spec sync on close | Domain spec § APP-028 + changelog |

## Test plan

```bash
# Engine (regression — no app narration)
python -m pytest play/tomb_gm/tests/test_combat*.py -q
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py -q

# App — new module (APP-028)
python -m pytest app/tests/test_combat_failure_narration.py -q
```

**Primary new tests** (`app/tests/test_combat_failure_narration.py`):

| ID | Test | Setup | Pass |
|----|------|-------|------|
| **T1** | `test_handle_combat_trigger_returns_failure_string` | Mock `start_combat_from_trigger` → `{ok: false, error: "monster JSON not found: grave-ghoul"}`; call `_handle_combat_trigger` with `combat_trigger` item | Return equals `[Mechanics failed — combat start: …]\n\nCombat could not begin.`; `combat.active` false |
| **T2** | `test_beat_trigger_e2e_llm_loop_short_circuits` | Patch `chat_completion` once: `content` `"Ghouls leap from the crypt."` + `process_beat` tool call; mock `process_beat` → `ok: true` + `combat_trigger`; mock `start_combat_from_trigger` → `ok: false` | `_llm_loop` return is failure string only (R1 shape); **no** ghoul fiction; **no second** `chat_completion` call; `status.combat` null |
| **T3** | `test_llm_loop_all_failed_strips_content[start_combat]` | Single failing `start_combat`; pre-tool content with combat-start fiction | Prefix only; banned: initiative / enemies charge |
| **T4** | `test_llm_loop_all_failed_strips_content[combat_attack]` | `combat_attack` → `attacker not in combat`; hit fiction in `content` | Prefix only; banned: damage / hit |
| **T5** | `test_llm_loop_all_failed_strips_content[combat_end]` | `combat_end` → `{ok: false, error: "no active combat"}`; content claims combat ended | Prefix only; banned: combat ended / victory prose |
| **T6** | `test_llm_loop_all_failed_strips_content[cast_spell]` | `cast_spell` → `{ok: false, error: "not in combat"}`; content describes spell effect | Prefix only; banned: spell damage / effect prose |
| **T7** | `test_llm_loop_all_failed_strips_content[fortune_spend]` | `fortune_spend` → `{ok: false, error: "no Fortune remaining"}`; content claims Fortune spent | Prefix only; banned: Fortune spent / reroll success |
| **T8** | `test_combat_inner_all_failed_strips_content` | `_combat_llm_loop_inner`: content + failing `combat_action` | `[Mechanics failed` only; no appended model content |
| **T9** | `test_combat_inner_wrong_tool_failure` | Tool name `start_combat` during combat loop | Failure prefix; no hit narration |
| **T10** | `test_combat_inner_partial_failure_injects_tool_failed` | Mock turn: one `combat_action` `ok: false` + one `ok: true` (or depth-1 retry after single failure) | `messages` contains system line `TOOL FAILED (combat_action)` **before** corresponding tool result; loop continues (not `all_failed` short-circuit) |

Implement T3–T7 via `@pytest.mark.parametrize("tool_name,…")` or five explicit tests — same assertions, distinct mocked `error` + banned fiction substrings per tool.

**T2 dual-channel note:** Assert **player return** from `_llm_loop`, not `process_beat` tool JSON `ok: false`. Tool-role payload may still include `combat_trigger` with `ok: true`.

**Optional (SPEC-005):** `test_all_failed_or_beat_failure_logs` — `caplog` or mock `log_error` when R1 short-circuits or R2/R3 strips `content`.

Use existing `orchestrator` / `bridge` fixtures from `app/tests/conftest.py`; monkeypatch `chat_completion` and bridge methods — do not use `play/workspace`.

## Affected paths

_Must match ticket **Expected files**._

- `app/gm/orchestrator.py` — `_handle_combat_trigger` (return failure str), `_execute_tool` / `_beat_combat_start_failure`, `_llm_loop` short-circuit, `_combat_llm_loop_inner` R3/R4
- `app/tests/test_combat_failure_narration.py` — **new** (T1–T10)
- `tmp/app-combat-play-spec.md` — § Combat tool failure narration (APP-028)

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Unknown monster direct start:** Ask GM to start combat with invalid id (or scenario with missing JSON) — player sees mechanical failure, no “the knight charges” fiction.
- **Beat-trigger encounter:** Delve until `process_beat` would spawn grave-ghoul (or force encounter); if start fails, narration must **not** describe ghouls attacking while combat panel empty / `combat: null`.
- **Attack outside combat:** Declare attack before combat — failure line visible, no damage narration.
- **In-combat bad action:** Wrong turn or invalid `combat_action` — failure only, no hit line.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — paths A–F, `all_failed` lines, `pending_start` grep
- **Domain truth:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md) — § Combat tool failure narration (APP-028)
- **Coordination:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — mechanical truth; APP-028 listed under open work
- **Related:** APP-026 (gating), APP-027 (engine validation), APP-030 (integration test)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | Initial PM draft — R1 beat-trigger, R2/R3 content strip, combat tool inventory, test plan |
| 2026-05-21 | PM r2 (QA spec): R1 propagation contract (`_llm_loop` short-circuit); T1–T10 incl. five exploration tools + R4 partial-failure injection; ticket Expected files |
