# Spec: APP-022-hint-enterdungeon-on-failed-setphasedelve

**Status:** draft  
**backlog_ticket:** APP-022  
**ticket_path:** [tmp/backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md](../../app-022-hint-enterdungeon-on-failed-setphasedelve.md)  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-exploration-delve-spec.md`

## Problem

The LLM often tries to enter a site by calling **`set_phase(phase="delve")`** while the party is still on the surface in **`preparation`**. The engine rejects this — legal transitions from `preparation` are **`ingress` only** — and **`enter_dungeon(site_address)`** is the correct entry path (it runs `advance_phase_for_dungeon_entry`: `preparation→ingress→delve` internally).

Today the orchestrator surfaces only a generic failure:

- Tool message: `{ok: false, error: "Cannot transition from preparation to delve"}`
- System inject: `TOOL FAILED (set_phase): … You MUST narrate this failure honestly.`
- Optional player banner: `[Mechanics failed — set_phase: …]` + sanitized assistant `content` (APP-024)

**No code-owned hint** names **`compass_exits`** or **`enter_dungeon`**. Prompt/schema guidance exists (`tools.py`, `system_prompt.py`, APP-021) but is not reinforced at failure time, so the model may retry the same wrong tool or narrate entry fiction without the right tools.

**Evidence:** Domain spec problem log; research trace `orchestrator.py` `_llm_loop` L2443–2478; engine test `test_set_phase_rejects_preparation_to_delve`.

## Goals

- On **failed `set_phase(delve)`**, inject a **code-owned hint** that steers the model (and optionally the player) toward **`compass_exits`** then **`enter_dungeon(site_address)`**.
- Keep scope **hints only** — no change to phase FSM, bridge entry logic, APP-024 fiction gate, or APP-077 footer.

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Block site-entry fiction without tools | [APP-024](../../app-024-block-site-fiction-without-enter-dungeon.md) — done; sibling layer |
| Code-owned exploration status footer | [APP-077](../../app-077-code-owned-exploration-status-footer.md) |
| Change `set_phase` / `enter_dungeon` tool schemas or `system_prompt.py` | Out of ticket **Expected files**; already document correct flow |
| Map UX surfacing ingress | [APP-063](../../app-063-map-ux-redesign-useful-navigation.md) |
| Strip assistant `content` on `all_failed` | [APP-028](../../app-028-combat-tool-failure-narration.md) combat scope; exploration may still append sanitized content — hint **adds** guidance, does not replace APP-024 |
| Creation-desk phase hints | `_llm_loop` blocked during `creation.active` |

## Requirements

Full behavior and test contracts: domain spec § **Failed set_phase(delve) hint (APP-022)**.

### Trigger

Fire **only** when **all** of:

| Condition | Value |
|-----------|--------|
| Tool name | `set_phase` |
| Requested phase | `args.get("phase", "").strip().lower() == "delve"` (after `normalize_tool_args`) |
| Tool outcome | `result.get("ok")` is falsy |

**Do not** fire on failed `set_phase` for other phases (`ingress`, `extract`, `aftermath`, `preparation`, unknown).

**Applies to all failed `set_phase(delve)`** — primary case `preparation→delve`, secondary `aftermath→delve` (`Cannot enter dungeon from phase aftermath` is a different path; if engine returns `ok: false` via `set_phase(delve)` from `aftermath`, hint still applies).

**Partial success:** If the same tool batch includes a successful `enter_dungeon` / `site_enter`, hint may still attach to the failed `set_phase` tool result (LLM transcript) but **must not** append a player-visible hint on the `all_failed and content` short-circuit (that path not taken).

### Hint text contract

**Helper:** `_delve_entry_tool_hint(*, below_addresses: list[str] | None = None) -> str`

**Core (always present):**

> Do not use set_phase to enter a site. Call **compass_exits** to list below addresses, then **enter_dungeon(site_address)**. enter_dungeon advances preparation→ingress→delve automatically.

**Optional suffix** when `below_addresses` non-empty (from `bridge.compass_exits()` → `exits.below` at hint-build time):

> Below from current cell: {comma-separated AV-GRID addresses}.

When `compass_exits` fails or `below` is empty, emit **core only** — do not fail the hint.

Use **`site_address`** (APP-021 primary param name), not `site_id`.

### Injection points (dual audience)

| ID | Channel | When | Content |
|----|---------|------|---------|
| **R1** | Tool result dict | After failed trigger, before `log_tool_call` / `_last_tool_results` store | Add `"hint": "<hint text>"` to the result dict returned to the tool message (JSON-serialized). Original `"error"` unchanged. |
| **R2** | System `TOOL FAILED` message | Same failure, in `_llm_loop` else branch | Append after existing sentence: ` Hint: <hint text>` (same string as R1 `hint` field). |
| **R3** | Player-visible banner | `all_failed and content` early return at depth 0, and failed batch includes triggered `set_phase(delve)` | After `prefix = f"[Mechanics failed — {failures}]"`, append `\n\n` + hint text **before** `\n\n` + APP-024 composed content. Do **not** inject R3 when `failed_names & _COMBAT_TOOL_NAMES` (existing early return). |

**Order with APP-024:** R3 hint sits between failure prefix and sanitized assistant prose — not inside `_compose_exploration_narration`. APP-024 sanitizer unchanged.

**APP-024 refusal overlap:** If gate strips entry fiction to `_SITE_ENTRY_REFUSAL_LINE`, player may see both refusal and R3 hint on the same turn — acceptable; refusal addresses fiction, hint addresses wrong tool.

### Requirement summary

| ID | Summary | Locus |
|----|---------|-------|
| **R1** | Enrich failed `set_phase(delve)` tool JSON with `hint` | `orchestrator.py` `_llm_loop` |
| **R2** | Extend system `TOOL FAILED (set_phase)` with same hint | `orchestrator.py` `_llm_loop` |
| **R3** | Player-visible hint on `all_failed and content` when set_phase(delve) failed | `orchestrator.py` `_llm_loop` |
| **R4** | Optional below-address suffix from live `compass_exits` | `_delve_entry_tool_hint` + bridge call |
| **R5** | No hint on non-delve `set_phase` failures or successful `set_phase` | Negative tests |

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| On failed set_phase(delve), orchestrator hints enter_dungeon + compass_exits | R1–R3; T1–T3 |
| Spec sync on close | Domain spec § APP-022 + changelog |

## Test plan

```bash
# Engine regression (phase FSM — unchanged)
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q

# App — new module (APP-022)
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q

# APP-024 regression
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
```

**Primary new tests** (`app/tests/test_exploration_set_phase_delve_hint.py`):

| ID | Test | Setup | Pass |
|----|------|-------|------|
| **T1** | `test_failed_set_phase_delve_tool_result_has_hint` | Mock LLM: single `set_phase({"phase": "delve"})`; party phase `preparation`; mock `bridge.set_phase` → `{ok: false, error: "Cannot transition from preparation to delve"}` | `_last_tool_results["set_phase"]["hint"]` contains `compass_exits` and `enter_dungeon` (case-insensitive) |
| **T2** | `test_all_failed_content_includes_player_hint` | Mock LLM: `content` entry prose + failing `set_phase(delve)` only; surface mode | Return contains `[Mechanics failed`; substrings `compass_exits`, `enter_dungeon`; APP-024 may strip entry markers from content portion |
| **T3** | `test_failed_set_phase_ingress_no_hint` | Mock failing `set_phase({"phase": "ingress"})` | No `hint` key; player/system output lacks delve-entry hint helper text |
| **T4** | `test_successful_set_phase_delve_no_hint` | Party phase `ingress`; real or mocked successful `set_phase(delve)` | No `hint` on result |
| **T5** | `test_partial_success_enter_dungeon_no_player_hint` | Batch: fail `set_phase(delve)` + success `enter_dungeon`; loop continues | Failed `set_phase` may have R1 hint; final player path not `all_failed` short-circuit with R3-only assertion |
| **T6** | `test_system_tool_failed_message_includes_hint` | Capture `messages` in `_llm_loop` after failed `set_phase(delve)` | System role content includes `TOOL FAILED (set_phase)` and `compass_exits` |

Reuse helpers from `test_exploration_site_entry_gate.py`: `_patch_llm_sequence`, `_surface_exploration_orchestrator`, `_tool_call`, `orchestrator` fixture from `app/tests/conftest.py`. Do not use `play/workspace`.

## Affected paths

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_delve_entry_tool_hint`, R1–R3 in `_llm_loop` |
| `app/tests/test_exploration_set_phase_delve_hint.py` | **new** — T1–T6 |
| `tmp/app-exploration-delve-spec.md` | § Failed set_phase(delve) hint (APP-022) |

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Surface at Registry hub / Breley:** After creation, say **"enter the undercrypt now"** or phrasing that provokes **`set_phase(delve)`** without `enter_dungeon`. Expect **`[Mechanics failed — set_phase: …]`** plus visible mention of **`compass_exits`** and **`enter_dungeon`**; engine still surface / `preparation`.
- **Recovery:** On next turn, model should call **`compass_exits`** then **`enter_dungeon(site_address)`** — mode becomes dungeon, phase advances.
- **Regression:** Successful entry via **`enter_dungeon`** still works; no duplicate hint spam on normal entry.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — paths A–E, injection axes
- **Domain truth:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) — § Failed set_phase(delve) hint (APP-022)
- **Coordination:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — `_llm_loop` tool failure pattern; APP-022 listed under open work until close
- **Related:** APP-024 (fiction gate), APP-021 (`site_address`), APP-077 (footer compose order)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft — trigger, dual injection R1–R3, hint text, T1–T6, domain spec § |
