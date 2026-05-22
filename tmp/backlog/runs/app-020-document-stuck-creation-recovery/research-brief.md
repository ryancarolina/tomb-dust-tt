# Research Brief: APP-020-document-stuck-creation-recovery

**Date:** 2026-05-22  
**Question:** What should players be told when character creation is stuck, and how does typing **`new game`** recover — without changing code?

**backlog_ticket:** APP-020  
**ticket_path:** tmp/backlog/app-020-document-stuck-creation-recovery.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec [`tmp/app-session-persistence-spec.md`](../../app-session-persistence-spec.md) is registered in [`tmp/app-master-spec.md`](../../app-master-spec.md) § Spec registry as **Session persistence** — owns `session_state.json`, autosave, resume, and `play/workspace/`. APP-020 is listed in that spec's open checklist (APP-014–APP-020 batch) and the spec already defines recovery behavior: `setup_new_game()` lifecycle (APP-014), upfront creation-block clear (APP-015), startup `has_save()` rules (APP-064), resume-failure copy (APP-071), and the test scenario "`new game` from stuck partial creation → clean NAME step." This ticket only surfaces that behavior in [`app/README.md`](../../../app/README.md). No new domain spec row is required.

## Summary

Players can land in **partial creation** — mid-desk FSM with an empty engine roster and optional `app/session_state.json` — after autosave, quit/relaunch, LLM errors, or failed setup. Engineering recovery is implemented: **`new game`** runs `setup_new_game()`, which resets creation to **NAME**, clears the on-disk creation block before engine wipe (APP-015), ends prior sessions, wipes workspace data, and on success deletes the app save file. APP-014/015/019 closed the historical failures (`Could not start game`, stale disk misleading variant-B `load game` copy).

[`app/README.md`](../../../app/README.md) does **not** document stuck-creation recovery today. Its Quick Start line ("The app auto-resumes if `session_state.json` or a workspace save exists") is **misleading** after APP-064: boot does **not** auto-restore from `session_state.json` alone; startup `has_save` requires a **living slotted character** in the engine DB. Mid-creation partial saves show the **new-game-only** path at relaunch — exactly when players need the README to say **type `new game`** to reset.

APP-020 is a **documentation chore** (Expected files: `app/README.md` only). PM should add a short player-facing section (symptoms → `new game` → progress wiped → optional `load game` only for finished saves) and correct the Quick Start resume sentence. Domain spec changelog on close is required per ticket; no pytest for README prose.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Player entry / startup | `app/ui/app.py` — `_init_orchestrator` | `bridge.has_save()` only; chips `["new game"]` or `["load game", "new game"]` |
| Recovery command | `app/gm/orchestrator.py` — `process_turn` (`new game` / `start` / `new`), `setup_new_game` | Aliases accepted; failure copy via `_setup_new_game_failure_message` (APP-019) |
| Creation reset | `app/gm/orchestrator.py` — `_reset_creation_for_new_game`, `_clear_creation_block_on_disk`, `_delete_save_file` | C1–C2 before wipe; full file delete on success |
| Engine lifecycle | `app/gm/bridge.py` — `end_session`, `force_close_all_sessions`, `wipe_all_data`, `campaign_new`, `session_start` | L1–L5 ordering per domain spec |
| Save eligibility | `play/tomb_gm/domain/session.py` — `find_save_campaign`, `has_save_session` | Save = slotted living character, not empty-roster creation |
| App autosave | `app/ui/app.py` — `_save_session`, `_load_session` | `_load_session` on **load game** only, not boot |
| Resume failure UX | `app/gm/orchestrator.py` — `_resume_failure_message`, `_is_mid_creation_resume_failure` | Variant B already tells player **`new game`** (wipe warning) in narration — not in README |
| Player doc (target) | `app/README.md` | Quick Start + Features mention persistence; no stuck-recovery section |

## Code-path traces

### Stuck partial creation at relaunch (APP-064 path)

1. Entry: Player mid-creation → Escape quit → `session_state.json` written with `creation_state` + `engine_status`; engine session active, **empty roster**.
2. Relaunch: `_init_orchestrator` → `bridge.has_save()` → **false** (no slotted living character).
3. UI: narration "Type 'new game' to create a character…"; suggestions **`["new game"]` only** — no "You have a saved game."
4. Player may try **`load game`** → `session_resume` fails → variant B narration names current step + suggests continue desk or **`new game`** (APP-071).
5. Recovery: player types **`new game`** → `setup_new_game()` (trace below).
6. Exit: NAME desk, fresh campaign; prior partial progress lost.

### Recovery: `new game` from stuck creation

1. Entry: `App._process_turn` → `orchestrator.process_turn("new game")` (also `start`, `new`).
2. `setup_new_game()`:
   - `_reset_creation_for_new_game()` — memory `CreationState(active=True, step="NAME")`.
   - `_clear_creation_block_on_disk()` — surgical `creation_state` + drop `engine_status` if file exists.
   - `bridge.end_session()` / `force_close_all_sessions()` on failure.
   - `bridge.wipe_all_data()` → `init()` → `campaign_new` → `session_start`.
   - On success: `history.clear()`, NAME creation, `_delete_save_file()`.
3. On failure: `_setup_new_game_failure_message` + `_emit_recovery_narration`; footer `[Awaiting: new game]`; retry **`new game`** (APP-019).
4. `_creation_turn` — clerk NAME prompt.
5. Exit: `finally` `_save_session()` writes fresh autosave aligned with new session.

### In-session reset (same run, no relaunch)

1. Entry: Player mid-desk (e.g. RACE/SKILLS) types **`new game`** again.
2. Same `setup_new_game()` trace; narration clears via UI `clear_narration` queue on submit.
3. Exit: Footer `[Awaiting: NAME_INPUT]`; must not reference prior name as finalized (APP-014 TC-2 / APP-015).

### What is *not* recovery for stuck creation

1. **`load game`** / **`continue`** — requires engine save (`find_save_campaign`); empty roster → variant A or B failure, not desk restore without APP-018 restore paths on successful resume.
2. **Deleting files by hand** — not documented; canonical play is in-app command per AGENTS.md / active rule.
3. **`tomb_gm` CLI / Cursor chat GM** — obsolete for players.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-session-persistence-spec.md`](../../app-session-persistence-spec.md) — § Problem (partial creation + empty roster); § Startup save-detection (APP-064); § setup_new_game lifecycle (APP-014); § New game — creation block clear (APP-015); § Resume failure (APP-071); § New game failure (APP-019); Tests "`new game` from stuck partial creation → clean NAME step".
- Master registry: [`tmp/app-master-spec.md`](../../app-master-spec.md) — Session persistence row; dependency note `app-session-persistence-spec → reliable new game`.
- Closed implementation tickets: APP-014, APP-015, APP-017, APP-018, APP-019, APP-064, APP-071 (behavior exists; APP-020 documents it).
- Human playtest reference: [`tmp/backlog/runs/app-014-setupnewgame-session-lifecycle/human-test-plan.md`](../app-014-setupnewgame-session-lifecycle/human-test-plan.md) — partial-creation setup + TC-1/TC-2 for **`new game`** → NAME.
- Prior research: [`tmp/backlog/runs/app-015-clear-creation-block-on-new-game/research-brief.md`](../app-015-clear-creation-block-on-new-game/research-brief.md) — noted "APP-020 will document stuck → `new game` recovery".
- Player README (gap): [`app/README.md`](../../../app/README.md) — line 15 auto-resume claim; no stuck-recovery section.
- Canon play rule: [`AGENTS.md`](../../../AGENTS.md) — PyGame `app/main.py` canonical; no hand-editing saves for players.

## Tests & commands

```bash
# Automated coverage for recovery behavior (not README)
python -m pytest app/tests -q -k "setup_new_game or creation_block or session_resume or creation_restore or reconcile"

# Engine save detection
python -m pytest play/tomb_gm/tests -q -k session

# Manual — maps to domain spec + APP-014 human-test-plan (for Stage 7 / QA doc cross-check)
cd app && python main.py
# 1. new game → advance past NAME → Escape quit
# 2. Relaunch → no "saved game"; chip new game only
# 3. Type new game → NAME prompt; no "Could not start game"
# 4. Optional: mid-desk new game without quit → NAME again
```

No test asserts README content. Acceptance is checklist review of `app/README.md` prose against ticket AC.

## Risks & unknowns

- **README inaccuracy (blocker for good docs):** Quick Start claims auto-resume when `session_state.json` exists; APP-064 explicitly forbids that at boot. PM/Dev should fix in the same edit as APP-020 or players will mis-trust **`load game`** for partial creation.
- **Wipe warning tone:** `new game` destroys in-progress creation and workspace campaign data (corpses persist per spec). README must state data loss plainly without duplicating full APP-019 error catalog.
- **Symptom list scope:** "Stuck" is player-reported (repeated prompts, blank GM, wrong step, setup error footer). Avoid implying every LLM glitch needs wipe — suggest retry one clerk input first, then **`new game`**.
- **`load game` confusion:** Mid-creation players may expect autosave to resume via load; doc should contrast **finished save** (slotted character) vs **partial creation** (`new game` reset).
- **Spec checklist drift:** Domain spec still lists APP-014 as open in Task checklist while ticket APP-014 is `done` — PM may sync checklist when closing APP-020; out of Research Expected files unless PM expands scope.
- **No code change:** If README documents behavior code lacks, that's pre-020 regression; research confirms APP-014/015 paths are present in `orchestrator.py` as of 2026-05-22.

## Raw notes

- Ticket AC: "`app/README.md` documents: stuck creation → type new game."
- Expected files: **`app/README.md` only** — no orchestrator/UI edits in this ticket.
- `setup_new_game` entry order verified in `app/gm/orchestrator.py` (~665–683): reset + disk clear **before** `wipe_all_data`.
- Startup chips (`app/ui/app.py` ~128–146): `has_save` drives branch; partial creation → `new game` only.
- APP-071 variant B prose already warns **`new game`** wipes — README should align, not contradict.
- Batch board: APP-020 parallel with APP-031, APP-037 — no file overlap.
- Suggested README placement (PM): new subsection under Quick Start or Features — "Stuck during character creation?" with bullet symptoms + **`new game`** + note on finished saves vs partial.
