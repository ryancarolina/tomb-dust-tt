# Research Brief: app-014-setupnewgame-session-lifecycle

**Date:** 2026-05-20
**Question:** What is the current `setup_new_game` lifecycle, where does it diverge from “end prior session → wipe → new campaign → start session”, and what must change to satisfy APP-014 without breaking corpse persistence or batch siblings?

**backlog_ticket:** APP-014
**ticket_path:** tmp/backlog/app-014-setupnewgame-session-lifecycle.md
**domain_spec:** tmp/app-session-persistence-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) already owns `setup_new_game`, `session_state.json`, autosave, resume, and the “Problem (from logs)” block listing `setup_new_game` / open-session failures. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Session persistence** → `app-session-persistence-spec.md` → `session_state.json`, autosave, resume (`play/workspace/`). Bridge session APIs are cross-documented in [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) but do not need a new domain spec for this ticket.

## Summary

`Orchestrator.setup_new_game` is the single app entry for **`new game`**, death restart, and `session_resume` run-ended recovery. Today it runs **`wipe_all_data` → `init` → `campaign_new` → `session_start`** with no explicit **`end_session` / `force_close_all_sessions`** beforehand. Engine `start_session` already calls `_clear_save_slot` and `clear_active`, and `wipe_all_data` deletes session/campaign rows plus `active.json`, so many paths work in isolated tests — but the ticket AC and domain spec “Problem (from logs)” require an ordered **graceful session end before wipe** to avoid stale `active.json`, partial DB state, and player-visible “Could not start game” after APP-064 steers mid-creation users to type `new game`.

Historical log strings **`active session already exists`** / **`campaign already has an open session`** are **not present in current `play/tomb_gm` Python** (grep 2026-05-20); they remain valid symptom descriptions in the domain spec. The fix is lifecycle ordering and failure handling, not matching obsolete error text. **`world_corpses`** is intentionally outside `wipe_all_data`’s table list — corpse persistence matches spec (“World corpses persist”). Sibling **APP-015** (explicit `session_state.json` creation-block clear) overlaps `_delete_save_file()` at the end of `setup_new_game`; coordinate so PM does not duplicate requirements.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| New game command | `app/gm/orchestrator.py` `process_turn` | Lines 495–500: `setup_new_game()` → `_creation_turn` |
| Lifecycle hub | `app/gm/orchestrator.py` `setup_new_game` | Lines 348–361: wipe-first; no `end_session` |
| Death / run-ended restart | `app/gm/orchestrator.py` | `_handle_player_death` (383), `process_turn` resume branch (518) — no `ok` check |
| Bridge session API | `app/gm/bridge.py` | `end_session`, `force_close_all_sessions`, `wipe_all_data`, `session_start`, `campaign_new` |
| Engine session FSM | `play/tomb_gm/domain/session.py` | `start_session`, `end_session`, `resume_session`, `has_save_session` |
| Engine campaign | `play/tomb_gm/domain/campaign.py` | `create_campaign` — `campaign already exists` if slug in DB |
| UI new-game UX | `app/ui/app.py` `_process_turn` | Queues `clear_narration` before orchestrator (283–284); `_save_session` in `finally` (324–325) |
| App save file | `app/session_state.json` | Deleted in `_delete_save_file` after successful path only |
| Tests | `app/tests/conftest.py`, `test_creation_flow.py` | Isolated workspace; no dedicated lifecycle-order test |
| Batch | `tmp/backlog/runs/batch-board-APP-014-APP-015-APP-016.md` | APP-014/015/016 parallel wave |

## Code-path traces

### Player types `new game` (happy path today)

1. **Entry:** `App._submit` → `_process_turn` (`app/ui/app.py:270–289`) queues `clear_narration` for `new game` / `new` / `start`.
2. **Orchestrator:** `process_turn` → `setup_new_game()` (`orchestrator.py:495–500`).
3. **`setup_new_game`:** `bridge.wipe_all_data()` — DELETE from `events`, `combat_state`, `party_state`, … `campaigns`, `memories`; unlink `active.json` (`bridge.py:423–440`). **Does not** touch `world_corpses`.
4. `bridge.init()` — migrations only (`cmd_core.handle_init`).
5. `bridge.campaign_new("salt-road", …)` — insert campaign row + campaign dir (`campaign.py:60–92`). On `"already exists"` error, **swallow and continue** (`orchestrator.py:353–354`).
6. `bridge.session_start(campaign_slug)` → `start_session` (`session.py:161–207`): `_clear_save_slot`, `clear_active`, INSERT session `current` + `party_state`, `write_active`.
7. `history.clear()`, `CreationState(active=True, step="NAME")`, `_delete_save_file()` (`orchestrator.py:358–360`).
8. Return `session` dict → `_creation_turn("[SYSTEM: New game started…]")`.
9. **UI `finally`:** `_save_session()` writes fresh `creation_state` to `session_state.json` (`app.py:324–325, 393–425`).

### Required path per ticket AC (not implemented)

1. **`bridge.end_session()`** (or **`force_close_all_sessions`** on failure — `bridge.py:399–405`).
2. **`bridge.wipe_all_data()`**
3. **`bridge.campaign_new(...)`**
4. **`bridge.session_start(...)`**

Gap: steps 1 is missing; steps 3–4 order matches today after wipe.

### `end_session` vs `wipe` (engine semantics)

- **`end_session`** (`session.py:311–345`): requires `active.json` with `session_id`; sets `sessions.ended_at`, updates `party_state.phase`, `clear_active`. Returns `no active session` if `active.json` missing — common after crash or manual file delete.
- **`force_close_all_sessions`** (`bridge.py:407–421`): `UPDATE sessions SET ended_at = … WHERE ended_at IS NULL`, unlink `active.json` — works without valid active pointer.
- **`wipe_all_data`**: hard DELETE session-scoped + campaign rows; does not log `session.ended` events (CLI `handle_session_end` logs + memory compact — `cmd_session.py:55–82`).

### Failure path (partial setup — risk)

1. `wipe_all_data` + `init` succeed; `campaign_new` returns `ok: false` for reason **other than** `"already exists"` → **early `return result`** (`orchestrator.py:355–356`).
2. **Skipped:** `session_start`, `creation` reset, `_delete_save_file`.
3. `process_turn` surfaces `Could not start game: {error}` + `log_error("setup_new_game", …)` (`497–499`) — **APP-019** scope for richer UI toast remains open.
4. Prior `creation` / `session_state.json` may remain stale until user retries — overlaps APP-015.

### Other callers of `setup_new_game`

1. **`_handle_player_death`:** after `process_delver_death`, sets `combat.active = False`, calls `setup_new_game(campaign_slug)` without checking return (`orchestrator.py:382–383`).
2. **`process_turn` resume + `run_ended`:** `setup_new_game(campaign_slug)` then death narration (`518–525`) — also no `ok` check.

### Post–APP-064 boot → `new game` (repro context)

1. Startup: `has_save()` false with active empty-roster creation session → chips `["new game"]` only (APP-064 done).
2. Player types **`new game`** → lifecycle above; failures here are the Supa-class stuck-creation recovery path cited in spec § Problem and APP-064 plan “Known UX”.

## Existing specs & docs

- **Ticket domain spec:** `tmp/app-session-persistence-spec.md` — § Problem lists `setup_new_game` / open-session errors; § Spec bullet: “**`new game`:** wipe app save + engine workspace via `setup_new_game()`”; open checklist item APP-014–APP-020; tests mention “`new game` from stuck partial creation → clean NAME step”.
- **GameBridge:** `tmp/app-gamebridge-spec.md` — documents `end_session`, `wipe_all_data`, `force_close_all_sessions`, `session_start`.
- **APP-064 / APP-071 run artifacts:** document that partial-creation boot → `new game` is follow-on UX for APP-014 (not APP-064 regression).
- **APP-015:** explicit creation-block clear in `session_state.json` — adjacent; `_delete_save_file` removes whole file today.
- **APP-019:** surface `new game` failure errors — narration-only today on failure branch.
- **Canon:** `build/docs/engine-integration.md` — inventory/stash; no session lifecycle detail (engine in `play/tomb_gm/domain/session.py`).

## Tests & commands

```bash
# Engine session domain
python -m pytest play/tomb_gm/tests -q -k session

# App creation (uses new game; isolated workspace)
python -m pytest app/tests -q -k "creation_flow or session_resume"

# Manual (domain spec + APP-064 T1a follow-on)
cd app && python main.py
# Partial creation → quit → relaunch → new game only chip → type new game → NAME step, no setup error
```

**Suggested new tests (for PM/Dev plan, not implemented here):**

| ID | Case | Expected |
|----|------|----------|
| **T-014a** | Isolated workspace: `session_start` → mid-creation state → `setup_new_game()` | `ok: true`; `bridge.status()` active session; `creation.step == NAME`; no open duplicate sessions |
| **T-014b** | `active.json` present + open session row → `setup_new_game()` | Prior session `ended_at` set **or** rows wiped; new session `current` |
| **T-014c** | `setup_new_game` after `process_delver_death` fixture | Corpse row still in `world_corpses`; new session started |

## Risks & unknowns

- **`end_session` alone may fail** when `active.json` is missing but DB still has `ended_at IS NULL` rows — implementation should use `end_session` then **`force_close_all_sessions`** on `not ok` before wipe (bridge already has this pattern on exception).
- **Redundant work:** `wipe_all_data` + `start_session._clear_save_slot` both delete session tables — acceptable if ordering satisfies AC and logging; avoid double-start without wipe if `campaign_new` fails.
- **`campaign already exists` swallow** (`orchestrator.py:353–354`) can hide incomplete wipe; after proper end+wipe, insert should succeed — PM should decide whether to keep swallow or tighten.
- **Autosave race:** `_save_session` in `finally` after failed `setup_new_game` may rewrite old `creation_state` if orchestrator creation not reset — failure-path should clear or skip save (APP-015 related).
- **No `app/tests` assertion** for lifecycle order today — regression risk without T-014a/b.
- **Exact historical error strings** not found in repo — QA should validate behavior (clean NAME, no “Could not start game”) not log substring match.
- **`play/workspace` guard:** `start_session` refuses `DEFAULT_WORKSPACE` under pytest (`session.py:52–65`); app tests use isolated tmp workspace — manual play uses real workspace.
- **Batch coupling:** APP-015/016 touch same save/orchestrator surfaces — spec/plan should sequence file ownership to avoid merge conflicts.

## Raw notes

- `setup_new_game` line refs (2026-05-20): `orchestrator.py:348–361`, `process_turn` 495–500.
- `wipe_all_data` tables: `bridge.py:425–429` — excludes `world_corpses`, `account_state` on campaign row (campaign row deleted entirely).
- `start_session` returns `replaced_previous: True` always on success (`session.py:206`).
- `main.py` has no `new game` handling — “main flow” in ticket = orchestrator + `ui/app.py` turn pipeline.
- Related open tickets: APP-015 (creation block), APP-017 (empty roster reconcile), APP-018 (continue restores creation), APP-019 (new game error surface), APP-052 (smoke).
