# Spec: APP-019-surface-new-game-errors

**Status:** draft (PM r2 — SPEC-001 emit contract)
**backlog_ticket:** APP-019
**ticket_path:** tmp/backlog/app-019-surface-new-game-failure-errors.md
**domain_spec:** tmp/app-session-persistence-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-session-persistence-spec.md

## Problem

When `setup_new_game()` fails, players get a terse engine string (`Could not start game: {error}`) in the narration panel with **no** matching `gm_narration` JSONL event (same gap APP-071 fixed for `load game`). Two **silent-success** paths narrate “A **new game** has started…” even when setup failed: `_handle_player_death` and `session_resume` + `run_ended`. The UI clears narration **before** orchestrator runs on explicit **`new game`**, so failed attempts wipe prior context and leave only the engine error line. No toast widget exists under `app/`; APP-071 established `_emit_recovery_narration` as the drift-safe pattern for recovery copy.

## Goals

- Every `setup_new_game` failure surfaces **player-facing** narration with **mapped cause** + **retry hint** (`new game`).
- JSONL retains `error` (`context: setup_new_game`) **and** `gm_narration` with the same panel text (via `_emit_recovery_narration`).
- Death restart and `run_ended` resume paths **never** claim success when `setup_new_game` returns `ok: false`.
- Suggestion chips offer **`new game`** retry without spurious `creation_drift`.

## Non-goals

- Toast / overlay UI (no infrastructure today; narration + optional status bar is sufficient).
- Changing APP-014 L1–L7 lifecycle ordering or APP-015 C1–C2 disk clear.
- Friendly copy for **`load game`** resume failure (APP-071 closed).
- Skipping `clear_narration` on explicit **`new game`** unless manual QA proves it blocks readability (document only).
- `main.py` changes (thin bootstrap — no session logic).

## Requirements

### R0: Failure contexts (order of evaluation)

All paths call the same `setup_new_game(campaign_slug)` (APP-014). On `not result.get("ok")`, emit recovery copy per context below — **never** proceed to `_creation_turn` or death-success narration.

| Context | Entry | Caller |
|---------|-------|--------|
| **A — command** | Player types `new game` / `start` / `new` | `process_turn` |
| **B — death** | PC death in combat mechanical results | `_handle_player_death` |
| **C — run_ended** | `load game` → `session_resume` ok + `run_ended` true | `process_turn` resume branch |

**Acceptance criteria**

- [ ] Each context uses `_setup_new_game_failure_message(result, context=...)` (name may vary) before return.
- [ ] No context returns success desk copy (“What is your name?”, “new game has started”) when `ok` is false.

### R1: Emit pattern (drift-safe JSONL)

**On any setup failure (A/B/C):**

1. `log_error("setup_new_game", <engine error>)` — unchanged context string for QA grep.
2. Build player message via R2–R4.
3. Call **`_emit_recovery_narration(message)`** exactly **once** (existing helper — same as APP-071).
4. Return `message` to UI (and to combat history append where applicable).

**Do not** use `_emit_narration` on setup-failure paths (would run `_check_creation_drift` on recovery footers).

#### R1a: Emit ownership — contexts A and C (inline callers)

**Contexts A and C** emit inside `process_turn` — the same function that calls `setup_new_game`. No secondary caller re-emits.

| Context | Failure emit site | Caller pattern |
|---------|-------------------|----------------|
| **A — command** | `process_turn` new-game branch | `log_error` → build R2 → `_emit_recovery_narration` → `return message` |
| **C — run_ended** | `process_turn` resume branch | `log_error` → build R4 → `_emit_recovery_narration` → `return message` |

On success, context C keeps today’s `_emit_narration(death_msg)` inline (R7).

**Acceptance criteria**

- [ ] Context A/C failure: exactly one `log_gm_narration` per failed attempt (no duplicate from UI or helper).

#### R1b: Emit ownership — context B (death restart; SPEC-001)

**Problem:** `_handle_player_death` **returns** a string; two combat call sites always call `_emit_narration(death_narration)` when non-`None` (`orchestrator.py` ~1586–1591, ~1680–1684). Naive fix inside `_handle_player_death` only (recovery emit + return) **double-logs** `gm_narration`. Caller-only `_emit_narration` on failure copy violates R1 and risks `creation_drift` / `awaiting_mismatch`.

**Contract (required):**

1. **`_handle_player_death` on `setup_new_game` failure:**
   - `log_error("setup_new_game", …)`
   - Build R3 copy (corpse lines preserved)
   - `_emit_recovery_narration(message)` **inside** `_handle_player_death`
   - Return a result that signals **narration already emitted** (e.g. `(message, already_emitted=True)`, small dataclass, or equivalent — Dev choice).

2. **`_handle_player_death` on success:** unchanged success copy; return with **narration not yet emitted** (`already_emitted=False`).

3. **Both combat call sites** (monster auto-chain path ~1586; PC combat LLM path ~1680): when death result is non-`None`:
   - If `already_emitted`: **MUST NOT** call `_emit_narration`; still append combat history and `return message`.
   - If not emitted: call `_emit_narration(message)` as today.

**Forbidden patterns:**

- Recovery emit inside `_handle_player_death` **and** `_emit_narration` at caller on the same failure message.
- Failure copy emitted via `_emit_narration` at either call site.

**Acceptance criteria**

- [ ] Mock death + failed `setup_new_game`: exactly **one** `log_gm_narration` with R3 body; one `log_error("setup_new_game", …)`.
- [ ] No `creation_drift` with `awaiting_mismatch` from recovery footer alone (T-019e applies to context B as well as A).
- [ ] Success death restart unchanged: caller `_emit_narration` once; NAME desk path (R7).

**R1 acceptance criteria (all contexts)**

- [ ] JSONL contains both `error` (`context: setup_new_game`) and `gm_narration` with identical body text shown in panel.
- [ ] Failure path does **not** emit `creation_drift` with `awaiting_mismatch` solely from `[Awaiting: new game]` footer (`_creation_drift_scope()` false after APP-015 NAME-fresh disk).
- [ ] Raw engine error strings are **not** the primary player message; map per R5.

### R2: Context A — explicit `new game` command failure

**When:** R0 context A; `setup_new_game()` returns `not ok`.

**Copy (minimum):**

```
Could not start a fresh session.

{cause_line}

Type **new game** to try again. If this keeps happening, quit and relaunch the app.
```

- `{cause_line}` from R5 engine-error map.
- Footer: `[Awaiting: new game]` on its own line (chip retry).

**Acceptance criteria**

- [ ] `process_turn("new game")` with mocked L4/L5 failure shows friendly copy in panel (not `Could not start game: …`).
- [ ] Status footer / chips include **`new game`** via bracket parsing.

### R3: Context B — death restart failure

**When:** R0 context B; delver death processed ok but `setup_new_game()` returns `not ok`.

**Copy (minimum):**

```
**{name}** is dead. The body remains in **{where}** — gear still on the corpse for anyone who finds it.

This run is over, but the registry could not open a fresh desk session.

{cause_line}

Type **new game** to try again.
```

- Preserve `{name}` / `{where}` from existing death narration (corpse location unchanged).
- Footer: `[Awaiting: new game]`.
- **Forbidden:** “A **new game** has started”, “What is your name?” when setup failed.

**Acceptance criteria**

- [ ] Mock death → failed `setup_new_game`: panel shows death + failure + retry; **no** success creation prompt.
- [ ] JSONL: `error` + **single** `gm_narration` via R1b contract; no `_creation_turn` / `creation_step` for failed restart.

### R4: Context C — `run_ended` resume restart failure

**When:** R0 context C; `session_resume` succeeded with `run_ended`; subsequent `setup_new_game()` returns `not ok`.

**Copy (minimum):**

```
Your previous delver did not survive (0 HP after the last fight). The body remains in **{where}** with all carried gear.

This run is over, but the registry could not open a fresh desk session.

{cause_line}

Type **new game** to try again.
```

- `{where}` from existing corpse list logic (unchanged).
- Footer: `[Awaiting: new game]`.
- **Forbidden:** success “new game has started” copy when setup failed.

**Acceptance criteria**

- [ ] Fixture: `session_resume` → `run_ended` + mocked setup failure → R4 copy; no NAME desk turn.
- [ ] JSONL: `error` + **single** `gm_narration` (R1a inline emit); no `_creation_turn`.
- [ ] Successful `run_ended` + setup success path unchanged (regression).

### R5: Engine error → player cause mapping

**Input:** `result.get("error")` string from `setup_new_game` (L4 `campaign_new` or L5 `session_start`).

| Engine error pattern (substring match) | `{cause_line}` |
|--------------------------------------|----------------|
| `campaign not found` | The save campaign could not be found in the workspace database. |
| `slug must be` | The campaign name failed validation — this is an internal setup error. |
| `campaign already exists` | A leftover campaign record blocked startup (unexpected after wipe). |
| `active session already exists` | A stale open session blocked startup (regression — report if seen after APP-014). |
| `campaign already has an open session` | Same as above — stale session lock. |
| `permission denied`, `database is locked`, `disk I/O` | The workspace database could not be written (permissions or file lock). |
| default / unknown | Something went wrong while resetting the workspace for a new run. |

Log the **verbatim** engine error in JSONL `error`; only `{cause_line}` is player-facing.

**Acceptance criteria**

- [ ] Tests assert mapped copy for at least `campaign not found` and default unknown.
- [ ] Verbatim engine error never appears as the first line of player copy.

### R6: UI scope (optional visibility boost)

**Default (orchestrator-only):** Friendly narration + `[Awaiting: new game]` satisfies ticket AC (mirrors APP-071).

**Optional (if manual QA shows weak visibility after command failure):**

- In `app/ui/app.py` `_process_turn`, when orchestrator return matches setup-failure sentinel (e.g. starts with “Could not start a fresh session” **or** orchestrator exposes `last_turn_was_setup_failure`), call `_set_turn_idle("Error — try again")` after queuing narration.
- **Do not** duplicate full copy into `("error", …)` queue — that wraps text in `[Error: …]` and doubles messaging.

**Acceptance criteria**

- [ ] Ticket closes without **required** UI edits if narration + chips are clear in manual smoke.
- [ ] Any UI status change stays within `app/ui/app.py`; no `main.py`.

### R7: Success paths (non-regression)

Unchanged when `setup_new_game` returns `ok: true`:

- Context A → `_creation_turn("[SYSTEM: New game started…]")`.
- Context B → existing death + “new game has started” + NAME prompt.
- Context C → existing run_ended death_msg + `_emit_narration`.

**Acceptance criteria**

- [ ] Cold **`new game`** still reaches NAME desk (T-014a regression).
- [ ] Death restart success + `run_ended` success paths unchanged in copy tone.

## Test plan

### Automated (`app/tests/test_setup_new_game_failure.py`)

```bash
python -m pytest app/tests -q -k "setup_new_game_failure or setup_new_game"
```

| ID | Case | Setup | Action | Assert |
|----|------|-------|--------|--------|
| **T-019a** | Command failure | Mock `bridge.campaign_new` → `ok: false`, error `campaign not found: salt-road` | `process_turn("new game")` | R2 copy; `campaign not found` cause; `[Awaiting: new game]`; **one** `log_gm_narration` + `log_error("setup_new_game", …)` |
| **T-019b** | Command failure default map | Mock L5 `session_start` → generic error | `process_turn("new game")` | Default `{cause_line}`; no verbatim `Could not start game:` prefix |
| **T-019c** | Death failure | Monkeypatch `bridge.extract_death_from_mechanical` / fixture mechanical; mock `setup_new_game` → `ok: false` | Direct `_handle_player_death(mechanical)` then simulate caller branch (or minimal combat turn stub) | R3 copy; no “new game has started”; no `_creation_turn`; **one** `log_gm_narration` + `log_error("setup_new_game", …)`; caller does **not** `_emit_narration` when `already_emitted` |
| **T-019d** | run_ended failure | Mock `session_resume` → `ok, run_ended=True` + `setup_new_game` → `ok: false` | `process_turn("load game")` | R4 copy; no success NAME prompt; **one** `log_gm_narration` + `log_error("setup_new_game", …)` |
| **T-019e** | Drift silence | T-019a **and** T-019c | inspect logger | No `creation_drift` with `awaiting_mismatch` from recovery footer alone |
| **T-019f** | Success regression | Isolated workspace | `process_turn("new game")` | Reaches creation / NAME path unchanged |

**Note:** T-019c does **not** require a full combat integration test — direct `_handle_player_death` + mocked bridge is sufficient. No existing pytest covers combat death today.

Use `isolated_workspace`, `mock_openrouter_client`; lazy-import `Orchestrator`; monkeypatch `log_gm_narration` / `log_error` per APP-071 test style.

### Manual smoke

```bash
cd app && python main.py
```

1. Normal **`new game`** → NAME desk (regression).
2. (Dev inject) force L4/L5 failure → R2 panel copy + JSONL `error` + `gm_narration`.
3. (Dev inject) death + setup failure → R3 copy, no false success.

## Human playtest hints (Stage 7)

- **TC-A:** Injected setup failure on **`new game`** — panel shows cause + “Type **new game** to try again”; chips include `new game`; JSONL dual-logged.
- **TC-B:** Death with injected setup failure — death/corpse line preserved; **no** “new game has started”; retry hint present.
- **TC-C:** `load game` after run ended with injected setup failure — R4 copy; no NAME desk.
- **TC-D:** Regression — happy-path death restart and **`new game`** still open NAME desk.

## Affected paths

| Path | Role |
|------|------|
| `app/gm/orchestrator.py` | `_setup_new_game_failure_message`, failure branches in `process_turn`, `_handle_player_death`, `run_ended` |
| `app/ui/app.py` | Optional `_set_turn_idle("Error — try again")` (R6) |
| `app/tests/test_setup_new_game_failure.py` | T-019a–f |
| `tmp/app-session-persistence-spec.md` | § New game failure (APP-019) |

**Out of scope:** `app/main.py` (remove from ticket Expected files if listed).

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-019): R0–R7 contexts, copy, JSONL, tests; orchestrator Expected files |
| 2026-05-20 | PM r2 (QA SPEC-001): R1a/R1b emit ownership — context B death caller contract; T-019c/d single JSONL + direct `_handle_player_death` test; T-019e covers B; removed stale Expected-files note |
