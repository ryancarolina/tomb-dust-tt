# Spec: APP-017-reconcile-empty-roster

**Status:** draft (PM round 2)
**backlog_ticket:** APP-017
**ticket_path:** tmp/backlog/app-017-reconcile-empty-roster-on-load.md
**domain_spec:** tmp/app-session-persistence-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-session-persistence-spec.md

## Problem

APP-016 persists `engine_status` on save, but load paths never read it. `_load_session()` restores `creation_state` and calls `_sync_creation_from_status()` against **live** `bridge.status()` only. When disk has `creation_state: null` (or `active: false`) but the saved engine snapshot shows **empty `roster`** mid-creation, the orchestrator stays in non-creation mode — suggestion chips go empty and the player can enter exploration/combat LLM paths instead of the desk FSM.

## Goals

- On **load game** / **continue** / **resume** UI restore (`_load_session` and post-resume sync), reconcile **inactive creation + empty roster** → force **`creation.active = true`**.
- Read saved **`engine_status`** from `session_state.json` when live engine state is missing, stale, or `awaiting: SETUP`.
- Keep reconcile **idempotent** across `_load_session` and post-resume `_sync_creation_from_status` calls.

## Non-goals

- **Boot / startup** auto-restore — APP-064; player must type load/new.
- **Restore creation step, name, race, roll, tables** — **APP-018** (same batch; runs after or alongside 017 in load hook).
- Fix **`export_creation_state() → None`** write-path desync (mitigated on read only).
- **`new game`** failure surfacing — **APP-019**.
- Edits outside ticket **Expected files** unless ticket expanded (prefer orchestrator reading disk internally).

## Requirements

### R1 — Force creation active on load reconcile

**Ticket AC:** If engine roster empty, creation inactive, and mid-creation (`awaiting == CHARACTER_CREATION` live or saved) → force creation mode.

**Acceptance criteria** (aligned with domain § R1 table)

| Condition | Action |
|-----------|--------|
| `creation.active == false` **and** empty **`roster`** **and** mid-creation (`live awaiting == CHARACTER_CREATION` **or** `saved engine_status.awaiting == CHARACTER_CREATION`) | Set **`creation.active = true`** |
| Non-empty live **`roster`** | Do **not** activate creation (post-finalize / in-delve unchanged) |
| Legacy save: no **`engine_status`**, live only | Reconcile from live engine; no new errors (T-017d) |

- [ ] Reconcile runs without requiring a successful `session_resume()` (covers resume-failure + mid-creation disk snapshot cases).
- [ ] Reconcile MUST be safe to call multiple times per load (no flip-flop).
- [ ] Do **not** force creation when live or saved **`awaiting`** is anything other than **`CHARACTER_CREATION`** (e.g. **`SETUP`**, **`ROSTER_SETUP`**, post-finalize states) even if **`roster`** is empty.

### R2 — Live vs saved precedence

**Acceptance criteria**

- [ ] **Precedence:** live `bridge.status()` wins when session is active — live **`roster`** wins over stale saved snapshot.
- [ ] When live session absent or `awaiting == SETUP`, fall back to saved **`engine_status.roster`** / **`engine_status.awaiting`** from `session_state.json` (APP-016 snapshot).
- [ ] **Absent or `null` `engine_status`:** no error; reconcile from live engine only (legacy saves — T-017d / T4c baseline).
- [ ] When saved snapshot shows non-empty **`roster`** but live **`roster`** is empty, live empty roster wins for mid-creation detection (stale snapshot does not block force-active).

### R3 — Empty roster definition (`roster` vs `characters`)

**Acceptance criteria**

- [ ] Force-active empty check uses **`roster` only** (slotted living characters), **not** **`characters`** (all campaign rows). Replace today's `_sync_creation_from_status` guard that uses `not status.get("characters")`.
- [ ] When live **`awaiting == ROSTER_SETUP`** (**`roster` empty**, **`characters` non-empty** — unslotted orphan rows): APP-017 **no-op**; do **not** force **`creation.active`**. Out of ticket AC; future ticket if orphan-row recovery is needed.
- [ ] Mid-creation force-active applies only when **`awaiting == CHARACTER_CREATION`** (R1), not when engine is in **`ROSTER_SETUP`**.

### R4 — APP-018 boundary (active vs restore)

**Acceptance criteria**

- [ ] **APP-017 owns:** flipping **`creation.active`** to **`true`** under R1 only.
- [ ] **APP-018 owns:** restoring **`creation.step`**, **`name`**, **`race`**, **`roll_result`**, table flags, and other desk FSM fields from saved **`creation_state`** when `awaiting == CHARACTER_CREATION`.
- [ ] APP-017 MUST NOT reset an in-progress step to **`NAME`** when saved **`creation_state`** carries a later step — defer step to APP-018. Minimal exception: if **`creation.step`** is **`WORLD_INTRO`** or otherwise invalid for an active desk session, reconcile MAY set **`step = "NAME"`** only **after** APP-018 import (domain § Merge order).
- [ ] **Merge order (canonical — matches domain § Merge order and [APP-018 spec](../app-018-continue-creation-state/spec.md)):** **APP-018** field restore (`import_creation_state` when gate passes) runs **first**; **APP-017** force-active runs only if **`roster`** empty and **`creation.active`** still false after (1). Shared load helper in `orchestrator.py` should call 018 restore before 017 reconcile before `_sync_creation_from_status`.

### R5 — Implementation locus

**Acceptance criteria**

- [ ] Primary change in **`app/gm/orchestrator.py`** — extend **`_sync_creation_from_status()`** and/or a dedicated reconcile helper invoked from existing load hooks.
- [ ] Orchestrator reads **`session_state.json`** internally (e.g. via existing `_session_state_path()`) so **`ui/app.py`** need not change for APP-017.
- [ ] Does **not** change APP-016 write path or APP-015 new-game clear.

## Test plan

```bash
python -m pytest app/tests -q -k "engine_status or load_session or reconcile or empty_roster or app_017"
python -m pytest app/tests -q -k "inactive_creation or session_resume"
```

| ID | Case | Expected |
|----|------|----------|
| **T-017a** | Mid-creation save; in-memory `creation.active=False`; `_load_session` / reconcile with disk `engine_status` (`CHARACTER_CREATION`, `roster==[]`) | `creation.active is True` after reconcile |
| **T-017b** | Disk: `creation_state: null`, `engine_status.roster==[]`, `awaiting: CHARACTER_CREATION`; live `awaiting: SETUP` | Force `creation.active is True`; step restore deferred to APP-018 |
| **T-017c** | Post-finalize: live **`roster`** non-empty | Reconcile does **not** reactivate creation |
| **T-017c2** | Stale snapshot: live **`roster`** empty, saved **`engine_status.roster`** non-empty, `awaiting: CHARACTER_CREATION` | Live empty wins — force **`creation.active`** per R1 (stale saved roster ignored) |
| **T-017d** | Legacy save: no `engine_status`, `creation_state.active=true` | Behavior unchanged vs pre-017 (T4c baseline) |
| **T-017e** | After reconcile of inactive + `CHARACTER_CREATION`: `get_player_suggestions` | Non-empty creation chips (not `[]`) — regression for `test_inactive_creation_ignores_step` |
| **T-017f** | Live `awaiting: ROSTER_SETUP`, `roster==[]`, `characters` non-empty; `creation.active=false` | APP-017 no-op — `creation.active` stays false |

**Test hygiene:** reuse `save_path` monkeypatch from `test_engine_status_on_save.py`; never write dev `app/session_state.json`.

## Human playtest hints (for Stage 7)

- Mid-creation (e.g. RACE step) → autosave → quit → relaunch → **load game** (no engine roster save): desk should re-enter creation mode with chips (step/name detail is APP-018).
- Post-finalize save with slotted character → **load game**: normal delve/exploration, not forced back to NAME desk.
- Legacy save without `engine_status` but active `creation_state`: load behaves as before.

## Affected paths

**Expected files** (ticket-aligned):

| Path | Role |
|------|------|
| `app/gm/orchestrator.py` | `_sync_creation_from_status`, disk read of `engine_status`, load-hook reconcile |
| `app/tests/test_reconcile_empty_roster_on_load.py` | T-017a–f, T-017c2 |
| `tmp/app-session-persistence-spec.md` | Domain § Reconcile empty roster on load (APP-017) |

**Out of scope**

| Path | Owner |
|------|-------|
| `app/ui/app.py` | Avoid unless reconcile cannot read disk from orchestrator |
| `app/gm/creation.py` | APP-018 if FSM import changes needed |

## Domain spec (source of truth)

Full behavior, batch boundaries, and tests: **[`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md)** § Reconcile empty roster on load (APP-017).

## Pointers

| Artifact | Path |
|----------|------|
| Research brief | [research-brief.md](./research-brief.md) |
| Batch board | [batch-board-APP-017-APP-018-APP-019.md](../batch-board-APP-017-APP-018-APP-019.md) |
| APP-018 ticket | [app-018-continue-restores-creation-state.md](../../app-018-continue-restores-creation-state.md) |
| APP-016 snapshot (write) | Domain spec § Engine status snapshot on save |
| Symptom test | `app/tests/test_ui_suggestions.py` — `test_inactive_creation_ignores_step` |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft — R1–R4, T-017a–e, APP-018 boundary |
| 2026-05-20 | PM r2 (QA round 1): R1/R2 unified mid-creation guard; R3 roster vs characters; R4 merge order 018→017; T-017f; ticket Expected files for tests |
