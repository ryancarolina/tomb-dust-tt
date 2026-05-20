# Spec: APP-014-setupnewgame-session-lifecycle

**Status:** draft (PM round 1)  
**backlog_ticket:** APP-014  
**ticket_path:** [tmp/backlog/app-014-setupnewgame-session-lifecycle.md](../../app-014-setupnewgame-session-lifecycle.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md)  
**registry_gap:** false (per research-brief)  
**Domain specs touched:** `tmp/app-session-persistence-spec.md`

## Problem

`Orchestrator.setup_new_game` wipes and starts fresh without explicitly ending the prior engine session first. Today the order is **`wipe_all_data` → `init` → `campaign_new` → `session_start`**. That often works in isolated tests because wipe deletes session rows and `active.json`, but it diverges from the ticket AC and the domain spec “Problem (from logs)” symptoms: stale `active.json`, open session rows, and player-visible **Could not start game** when mid-creation users type **`new game`** after APP-064’s boot path (empty roster → new-game chip only).

Historical log strings **`active session already exists`** / **`campaign already has an open session`** are symptom descriptions — not required substring matches in current engine code.

## Goals

- **P0:** `setup_new_game()` runs **graceful session end before wipe**, then campaign + session start per ticket AC.
- **P0:** Document ordered lifecycle, invariants, and tests in session-persistence domain spec.
- **P1:** Death / run-ended callers (`_handle_player_death`, resume `run_ended`) use the same lifecycle without breaking **`world_corpses`** persistence.

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Explicit `session_state.json` creation-block clear on failure / autosave race | **APP-015** — `_delete_save_file()` on success path only today; UI `_save_session` in `finally` may rewrite stale creation on failed setup |
| Engine `status()` snapshot on autosave | **APP-016** — save path only |
| Rich UI toast for `new game` failure | **APP-019** — narration-only error string remains |
| Remove `campaign already exists` swallow in `setup_new_game` | Out of scope unless Dev proves post-wipe insert still hits it |
| Change `session_resume`, startup save-detection, or load-game recovery | APP-064 / APP-071 closed |

## Requirements (summary)

Full behavior and test contracts live in domain spec § **setup_new_game lifecycle (APP-014)**.

| ID | Summary | Domain spec |
|----|---------|-------------|
| **L1** | Call `bridge.end_session()` first; on `not ok`, call `bridge.force_close_all_sessions()` before wipe | § Required order |
| **L2** | Then `wipe_all_data` → `init` → `campaign_new` → `session_start` (unchanged relative order after end) | § Required order |
| **L3** | On success: reset orchestrator creation (`NAME`), clear history, `_delete_save_file()` | § Success path |
| **L4** | On failure before `session_start`: return error dict; do not claim success | § Failure path |
| **L5** | **`world_corpses`** rows MUST survive `setup_new_game` (wipe excludes that table) | § Invariants |
| **L6** | All callers (`new game`, death, run-ended resume) invoke the same `setup_new_game` ordering | § Callers |
| **T-014a–c** | Lifecycle-order pytest coverage | § Tests APP-014 |

## Batch coordination

| Ticket | Owns | Overlap with APP-014 |
|--------|------|----------------------|
| **APP-014** | Engine session end **before** wipe in `setup_new_game` | — |
| **APP-015** | Explicit creation-block clear in `session_state.json` (incl. failure / autosave) | Shares `_delete_save_file()` on success; APP-014 must not skip L1–L2 assuming APP-015 will fix stale engine state |
| **APP-016** | `engine_status` snapshot on save | No change to `setup_new_game`; post-success UI autosave writes fresh creation block |
| **APP-019** | Surface setup failure in UI | Error narration from `process_turn` unchanged |

**Impl note:** Batch wave is parallel; prefer **`app/gm/orchestrator.py`** edits in APP-014 first (L1 prepend). APP-015 may touch `_delete_save_file`, `export_creation_state`, or UI save guard — coordinate merge order if both land same file.

## Acceptance criteria mapping

| Ticket AC | Spec / deliverable |
|-----------|-------------------|
| `setup_new_game()`: session end → wipe_all_data → campaign new → session start | L1, L2 |
| Domain spec updated | § setup_new_game lifecycle (APP-014) |
| Stuck partial creation → `new game` → clean NAME (manual) | T-014a + human playtest hint |

## Implementation pointers (Dev plan)

| Area | Path | Notes |
|------|------|-------|
| Lifecycle hub | `app/gm/orchestrator.py` `setup_new_game` ~348–361 | Prepend L1; keep wipe → init → campaign → session_start |
| Bridge | `app/gm/bridge.py` | `end_session` already falls back to `force_close_all_sessions` on exception |
| Callers | `orchestrator.py` `process_turn` ~495–500, `_handle_player_death` ~383, resume `run_ended` ~518 | No duplicate lifecycle — all route through `setup_new_game` |
| UI | `app/ui/app.py` `_process_turn` | Clears narration on `new game`; `_save_session` in `finally` — APP-015 scope |
| Engine | `play/tomb_gm/domain/session.py` | `end_session`, `start_session` semantics |

## Test plan

```bash
python -m pytest play/tomb_gm/tests -q -k session
python -m pytest app/tests -q -k "creation_flow or setup_new_game or session_lifecycle"
```

Manual + pytest cases in domain spec § Tests APP-014.

## Human playtest hints (for Stage 7)

- **APP-064 follow-on:** Partial creation (empty roster) → quit → relaunch → **`new game`** chip only → type **`new game`** → NAME step, no **Could not start game**.
- **Mid-creation retry:** Advance to RACE or later → **`new game`** → NAME step; no stale step in footer.
- **Death restart:** Delver death → new game narration → corpse still discoverable in world (manual spot-check or DB).
- **Regression:** Fresh workspace **`new game`** still reaches creation normally.

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py` — `setup_new_game` and callers
- `app/ui/app.py` — turn pipeline / autosave interaction (read-only unless APP-015 merges)
- `tmp/app-session-persistence-spec.md` — § setup_new_game lifecycle (APP-014)

## Pointers (source of truth)

| Topic | Location |
|-------|----------|
| Lifecycle behavior, invariants, tests | [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § setup_new_game lifecycle (APP-014) |
| Bridge session APIs | [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) — `end_session`, `force_close_all_sessions`, `wipe_all_data`, `session_start` |
| Research traces | [`research-brief.md`](research-brief.md) |
| Batch board | [`batch-board-APP-014-APP-015-APP-016.md`](../batch-board-APP-014-APP-015-APP-016.md) |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-014) |
