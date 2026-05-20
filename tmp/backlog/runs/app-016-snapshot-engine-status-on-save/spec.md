# Spec: APP-016-snapshot-engine-status-on-save

**Status:** draft (PM r2 — QA round 1 addressed)
**backlog_ticket:** APP-016
**ticket_path:** tmp/backlog/app-016-snapshot-engine-status-on-save.md
**domain_spec:** tmp/app-session-persistence-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-session-persistence-spec.md

## Problem

`session_state.json` stores rich `creation_state` but only partial engine truth (`session_id`, `campaign_slug` from `get_status()`). Mid-creation saves can show `creation_state.step` advanced while the engine has `awaiting: CHARACTER_CREATION` and an empty `roster`. Downstream reconcile tickets (APP-017, APP-018) need a **save-time** engine snapshot; today they would rely on live DB state at load, which may be stale or empty.

## Goals

- Persist full `GameBridge.status()` / `handle_status` payload on every app save under **`engine_status`**.
- Keep all existing save triggers and fields unchanged except the additive snapshot.
- Remain backward compatible when `engine_status` is absent (legacy saves).

## Non-goals

- **Read path:** `_load_session`, orchestrator resume, reconcile precedence — **APP-017**, **APP-018**.
- Trimming `engine_status` payload size.
- Changing startup `has_save()` / boot behavior (APP-064 closed).
- Centralizing save logic outside `app/ui/app.py` (unless Dev plan proposes minimal refactor ⊆ Expected files).

## Requirements

### R1 — Snapshot on save

**Acceptance criteria**

- [ ] Every `_save_session()` write includes `engine_status` when `get_status()` succeeds.
- [ ] `engine_status` is the **full** dict returned by `Orchestrator.get_status()` → `GameBridge.status()` → `handle_status` (same source as APP-005 `creation_finalize` JSONL `engine_status`).
- [ ] Reconcile-relevant keys are present when session exists: at minimum `awaiting`, `roster`, `party`, `combat`, `active` (plus any other keys `handle_status` returns today).
- [ ] On `get_status()` failure, save proceeds without blocking; **`engine_status` key omitted** (domain S5d preferred); load/reconcile treat absent key and `null` as “no snapshot”.
- [ ] Legacy saves without `engine_status` continue to load without error (write-only ticket; no new load behavior).

### R2 — Save triggers unchanged

**Acceptance criteria**

- [ ] Autosave (60s), Escape quit, and post-turn `finally` still call `_save_session()` only — no new triggers.

### R3 — Batch coordination

**Acceptance criteria**

- [ ] **APP-014** (`setup_new_game` lifecycle): no change required for APP-016; new-game wipe may replace `session_state.json` entirely — snapshot is recreated on next save after a successful session.
- [ ] **APP-015** (clear creation on new game): C2 surgical disk write **removes** `engine_status` on every `setup_new_game()` entry (owner: APP-015; test **T-015d**). APP-016 does not implement new-game clear.
- [ ] Domain spec § Consumers documents **APP-017** / **APP-018** read `engine_status` on load (out of APP-016 scope).

## Test plan

```bash
cd app && python -m pytest app/tests -q -k "engine_status or save_session"
python -m pytest play/tomb_gm/tests -q -k session   # regression
```

| ID | Case | Expected |
|----|------|----------|
| **T4a** | Headless/temp workspace: mid-creation (`CHARACTER_CREATION`, empty roster) → `_save_session` | `session_state.json` has `engine_status.awaiting == "CHARACTER_CREATION"`, `engine_status.roster == []` |
| **T4b** | Post-finalize or in-delve with slotted character → save | `engine_status.roster` non-empty; `awaiting` not `CHARACTER_CREATION` |
| **T4c** | Load legacy JSON without `engine_status` | No exception; existing `_load_session` behavior unchanged |
| **T4d** | `get_status()` raises or returns error-shaped payload | Save file written; `engine_status` absent/null; other fields intact |

## Human playtest hints (for Stage 7)

- Mid-creation (name or later step) → wait 60s or press Escape → open `app/session_state.json` → confirm `engine_status.awaiting` matches desk state (`CHARACTER_CREATION` + empty `roster` when no character slotted).
- After finalize / in-delve → save → confirm `engine_status.roster` has at least one entry.
- **Do not** expect load/continue to use the snapshot yet — that is APP-017/018.

## Affected paths

**Expected files** (ticket-aligned):

| Path | Role |
|------|------|
| `app/ui/app.py` | `_save_session()` — add `engine_status`; optional single `get_status()` |
| `app/tests/` | T4a–d save snapshot tests (isolated `SAVE_PATH`) |
| `tmp/app-session-persistence-spec.md` | Domain § APP-016 (this ticket) |

**Out of scope for APP-016** (APP-015 batch):

- `app/gm/orchestrator.py` — `engine_status` clear on new game (**APP-015** C2 / T-015d)
- `_load_session()` — no read of `engine_status` (**APP-017** / **APP-018**)

## Domain spec (source of truth)

Full behavior, schema, and tests: **[`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md)** § Engine status snapshot on save (APP-016).

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft |
| 2026-05-20 | PM r2: QA findings — domain § APP-016, APP-015 owns new-game `engine_status` clear, Expected files table, S5d omit canonical |
