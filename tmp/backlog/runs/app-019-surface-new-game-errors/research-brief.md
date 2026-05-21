# Research Brief: APP-019-surface-new-game-errors

**Date:** 2026-05-20
**Question:** When `new game` / `setup_new_game` fails, what does the player see today, where are failures silent, and what code paths must change to meet “clear error + cause + retry hint”?

**backlog_ticket:** APP-019
**ticket_path:** tmp/backlog/app-019-surface-new-game-failure-errors.md
**domain_spec:** tmp/app-session-persistence-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) already owns `setup_new_game` lifecycle, failure-path behavior (§ setup_new_game lifecycle — Failure path), and explicitly assigns **APP-019** to “toast / UI error channel for **`new game`** failures.” [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Session persistence** → `app-session-persistence-spec.md` → `session_state.json`, autosave, resume. JSONL dual-logging patterns live in [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) but do not own new-game copy — no new domain spec required.

## Summary

After APP-014 (session end before wipe) and APP-015 (creation block clear on entry), the primary **`new game`** command path in `Orchestrator.process_turn` returns a one-line string `Could not start game: {engine error}` and logs `log_error("setup_new_game", …)` only — it does **not** call `_emit_narration` or `_emit_recovery_narration`, so JSONL shows an `error` event without matching `gm_narration` (same gap APP-071 fixed for `load game`). The UI renders that string in the narration panel via `narration_text`, not the dedicated `error` channel (`[Error: …]` + footer “Error — try again”).

Failures are **fully silent** in two other callers: `_handle_player_death` and the `session_resume` + `run_ended` branch both call `setup_new_game(campaign_slug)` without checking `ok` and then narrate success (“A **new game** has started…”). No toast infrastructure exists anywhere under `app/`. The UI clears the narration panel **before** orchestrator runs on every `new game` submit, so a failed attempt wipes prior context and leaves only the terse engine error line.

Ticket Expected files list only `app/ui/` and `app/main.py`, but failure detection, copy, and JSONL emit today live in `app/gm/orchestrator.py` — PM should expand Expected files or define a UI-only wrapper pattern. `main.py` is a thin bootstrap with no session logic.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| App entry | `app/main.py` | `load_config()` → `App(config).run()` — no error surfacing |
| UI turn thread | `app/ui/app.py` `_process_turn`, `_process_ui_queue` | Queues `clear_narration` on `new game`; `error` channel for exceptions only |
| UI init failure | `app/ui/app.py` `_init_orchestrator` | `("error", f"Init failed: {exc}")` — only startup error surfacing |
| New game command | `app/gm/orchestrator.py` `process_turn` | Lines 535–540: `setup_new_game()` → failure string; no `_emit_*` |
| Lifecycle hub | `app/gm/orchestrator.py` `setup_new_game` | L1–L7 ordering (APP-014/015); early return on L4/L5 failure |
| Silent callers | `app/gm/orchestrator.py` | `_handle_player_death` (~424), `run_ended` resume branch (~558) — no `ok` check |
| Recovery narration helper | `app/gm/orchestrator.py` `_emit_recovery_narration` | Used for APP-071 load failure; **not** used for setup failure |
| JSONL | `app/gm/logger.py` | `log_error`, `log_gm_narration` |
| Bridge / engine | `app/gm/bridge.py`, `play/tomb_gm/domain/{session,campaign}.py` | Error shapes: `campaign already exists`, `campaign not found`, slug validation |
| Suggestion chips | `app/ui/suggestions.py`, `get_player_suggestions` | Post-failure chips from engine `awaiting`; no dedicated “retry new game” footer on setup failure |
| Tests | `app/tests/test_setup_new_game_lifecycle.py`, `test_creation_block_on_new_game.py` | Success + APP-015 disk clear on failure; **no** player-copy / JSONL test for setup failure |
| Related closed | APP-014, APP-015, APP-071 | Lifecycle + load-game friendly copy; APP-019 explicitly split from APP-071 |

## Code-path traces

### Player types `new game` (explicit command — failure)

1. **Entry:** `App._submit` → `_process_turn(text, turn_id)` (`app/ui/app.py:270`)
2. UI queues `("clear_narration", None)` because text ∈ `{new game, new, start}` (283–284) — **panel wiped before outcome known**
3. **Orchestrator:** `process_turn` → `setup_new_game()` (`orchestrator.py:535–536`)
4. **`setup_new_game` (post APP-014/015):** C1 memory reset → C2 disk creation block clear → `end_session` / `force_close_all_sessions` → `wipe_all_data` → `init` → `campaign_new` → on non-`already exists` failure **early return** (396–397); or `session_start` failure return
5. **Failure exit:** `log_error("setup_new_game", error)` → `return f"Could not start game: {error}"` (537–539). Skips `_emit_narration` / `_emit_recovery_narration` / `_creation_turn`
6. UI queues `("narration_text", narration)` with failure string (297); **not** `("error", …)`
7. **`finally`:** `_queue_turn_suggestions` + `_save_session()` if narration not None (319–322) — failure path still autosaves; APP-015 ensures creation block is NAME-fresh on disk even on failure
8. **JSONL:** `player_input` + `error` only — no `gm_narration` for the failure line

### Player types `new game` (success — baseline)

1. Same entry through `setup_new_game` L5 success → L6–L7 reset → `_creation_turn("[SYSTEM: New game started…]")`
2. `_emit_narration` runs inside creation turn path; panel shows LLM desk copy + status footer

### Death restart — silent failure risk

1. Combat resolves PC death → `_handle_player_death` (`orchestrator.py:404–433`)
2. `self.setup_new_game(campaign_slug)` — **return value ignored** (424)
3. Always returns success narration: “This run is over. A **new game** has started…” even if setup failed
4. Player may believe creation started while engine has no session / partial wipe state

### Resume + `run_ended` — silent failure risk

1. `process_turn("load game")` → `session_resume` ok + `run_ended` true (549–558)
2. `self.setup_new_game(campaign_slug)` — **no `ok` check** (558)
3. `_emit_narration(death_msg)` with “new game has started” copy regardless of setup outcome

### UI error channel (exists, unused for setup failure)

1. `_process_ui_queue`: `msg_type == "error"` → `narration.add_line(f"[Error: {data}]", "narrator")` + `_set_turn_idle("Error — try again")` (199–201)
2. Used for: orchestrator not initialized, `_init_orchestrator` exception, uncaught `_process_turn` exception (315–317)
3. **No** `toast` widget or overlay — grep `toast` under `app/` returns zero hits

### Post–APP-014 expected failure rate

- Historical symptoms (`active session already exists`, open-session blocks) addressed by L1/L1b + L2 ordering per domain spec
- Remaining realistic failures: `campaign_new` non-swallowed errors (slug validation, IO on campaign dir), `session_start` → `campaign not found`, DB/permission faults, rare race after partial wipe
- APP-014 human-test plan treats reappearance of **Could not start game** after partial creation as **blocker regression** — APP-019 owns making that message actionable when it does occur

## Existing specs & docs

- **Ticket domain spec:** `tmp/app-session-persistence-spec.md` — § Failure path: `process_turn` surfaces `Could not start game: {error}` + JSONL `error`; APP-019 for richer UI; callers SHOULD check `ok` before success narration
- **APP-071 (closed):** `_emit_recovery_narration` pattern for load failure — explicit split: APP-019 remains open for **`new game`**
- **Logging:** `tmp/app-logging-qa-spec.md` — `gm_narration` = final text to UI; setup failures currently log `error` only
- **APP-014 run artifacts:** death/resume caller `ok` checks deferred to APP-019
- **Ticket AC:** “Show clear error with cause + retry hint” — no mention of toast in ticket body; domain spec mentions toast / UI error channel

## Tests & commands

```bash
# Existing lifecycle / disk-clear tests (no failure copy assertions)
python -m pytest app/tests -q -k "setup_new_game or creation_block_on_new_game"

# Manual smoke — simulate campaign_new failure (requires dev monkeypatch or broken workspace)
cd app && python main.py
# 1. Type "new game" after normal boot → expect NAME desk (regression)
# 2. (Inject failure) expect friendly cause + retry hint in panel; JSONL error + gm_narration

# Inspect today's JSONL for setup_new_game errors
rg "setup_new_game" app/logs/session-2026-05-20.jsonl 2>/dev/null || true
```

**Test gap:** No pytest for `process_turn("new game")` when `setup_new_game` returns `ok: false` (contrast APP-071 `test_session_resume_failure.py`).

## Risks & unknowns

- **Expected files vs orchestrator:** Ticket lists `app/ui/`, `app/main.py` only; primary failure emit is `orchestrator.py:535–539`. PM must expand Expected files or specify UI detection of failure prefix — impl within ticket gate otherwise blocked.
- **Toast vs narration vs error channel:** Domain spec says “toast / UI error channel”; ticket AC says “clear error with cause + retry hint” without mandating toast. APP-071 established narration + `_emit_recovery_narration` as sufficient for load failure — PM should pick one pattern for APP-019 (likely mirror APP-071 + optional UI `error` queue for visibility).
- **Silent death / run_ended paths:** Highest-severity gap — success narration on failed setup. Fixing requires orchestrator edits (out of current Expected files).
- **`clear_narration` before outcome:** Failed `new game` leaves blank history except error line; PM may want to skip clear on failure or restore prior lines.
- **Engine error verbatim exposure:** e.g. `campaign already exists: salt-road` — should map to player-friendly cause (APP-071 did this for `no save session found`).
- **Suggestion chips:** Failure string has no `[Awaiting: …]` footer; chips may not include `new game` retry unless orchestrator adds footer or UI pushes suggestions on failure detection.
- **APP-014 regression overlap:** If failures are rare post-L1–L2, human QA may need injected failure fixtures; do not conflate “no error shown” with “setup always succeeds now.”

## Raw notes

- Failure return (current): `Could not start game: {result.get('error', 'unknown')}` — `orchestrator.py:537–539`
- `campaign_new` swallow: only when `"already exists" in error` — else early return (`394–397`)
- `session_start` errors: `campaign not found: {slug}` (`session.py:166–167`)
- `create_campaign` errors: slug validation, `campaign already exists: {slug}` (`campaign.py:66–71`)
- UI `error` channel status text: “Error — try again” (`app.py:201`) — stronger retry cue than current setup failure narration path
- `_save_session` on failure: still runs in `finally`; APP-015 C1–C2 already ran at setup entry — disk creation at NAME even when L4/L5 fail
- `main.py`: 34 lines — config load + `App.run()` only
- No `setup_new_game` hits in `app/logs/session-2026-05-20.jsonl` at research time — failures may be infrequent post-APP-014 or not yet playtested
- APP-071 drift-check explicitly left `setup_new_game` failure path untouched — APP-019 is the intended follow-up
