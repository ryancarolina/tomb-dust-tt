# Research Brief: APP-064-startup-save-prompt

**Date:** 2026-05-20  
**Question:** Why does startup offer "load game" when `session_resume` / `has_save_session()` cannot succeed, and what is the minimal fix that aligns UI messaging with engine resume eligibility?

**backlog_ticket:** APP-064  
**ticket_path:** tmp/backlog/app-064-startup-save-prompt-only-when-resumable.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec [`tmp/app-session-persistence-spec.md`](../../app-session-persistence-spec.md) is already registered in [`tmp/app-master-spec.md`](../../app-master-spec.md) § Spec registry as **Session persistence** — owns `session_state.json`, autosave, resume, and `play/workspace/`. APP-064 is explicitly listed in that spec's open checklist (APP-064 startup save-detection rule). UI implementation lives in `app/ui/app.py` (PyGame UI spec), but the **behavior rule** (when a save is considered resumable) belongs to session persistence; no new domain spec row is required.

## Summary

On launch, `_init_orchestrator` in `app/ui/app.py` calls `bridge.has_save()` (wrapper for engine `has_save_session()`), then **overrides** it: any active session whose `awaiting` is not `SETUP` or `SESSION_ENDED` is treated as a save. That includes `CHARACTER_CREATION` with an empty roster — the common Supa repro — where `find_save_campaign()` returns `None` because resume requires a living character with a roster slot (`slot IS NOT NULL AND alive = 1`).

When the player clicks **load game**, `orchestrator.process_turn` calls `bridge.session_resume()` → `resume_session()` → fails with `"no save session found"`. UI `_load_session()` (restores `session_state.json`) is queued but never helps because engine resume fails first and returns the error narration.

The fix is a one-line removal (or equivalent narrowing): trust `bridge.has_save()` alone for the startup branch. Post-finalize and in-progress delves with a living roster continue to pass `has_save_session()` and keep the saved-game prompt. Mid-creation with only an active session and empty roster will show the new-game path — matching ticket AC and avoiding a false load offer. Continuing mid-creation without a resumable engine save remains a separate gap (APP-018, APP-071, APP-017); APP-064 does not add a new resume path.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Startup UI init | `app/ui/app.py` — `_init_orchestrator`, `_process_turn`, `_load_session` | Bug: lines 128–131 widen `has_save` beyond engine |
| Turn / load handler | `app/gm/orchestrator.py` — `process_turn` (`load game` branch) | Calls `session_resume`; handles CHARACTER_CREATION only **after** successful resume |
| Bridge API | `app/gm/bridge.py` — `has_save()`, `session_resume()`, `status()` | Thin wrappers to `tomb_gm.domain.session` and `handle_status` |
| Engine save eligibility | `play/tomb_gm/domain/session.py` — `has_save_session`, `find_save_campaign`, `resume_session` | Resume requires `find_save_campaign` ≠ None |
| Engine status / awaiting | `play/tomb_gm/cli/cmd_core.py` — `handle_status` | Empty roster + no chars → `awaiting: CHARACTER_CREATION` |
| App entry | `app/main.py` | No startup resume; only `App.run()` → `_init_orchestrator` |
| App-side persistence | `app/session_state.json` | Written by `_save_session`; read by `_load_session` only on **load game**, not at boot |
| Related tickets | APP-017, APP-018, APP-071 | Load/reconcile, creation restore, friendly load failure copy |

## Code-path traces

### Startup save prompt (buggy path)

1. Entry: `app/main.py:main()` → `App.run()` → `_init_orchestrator()` (background thread).
2. `Orchestrator(config)` → `GameBridge()` → engine init.
3. `status = orchestrator.get_status()` → `bridge.status()` → `handle_status` (`play/tomb_gm/cli/cmd_core.py`).
4. `has_save = bridge.has_save()` → `has_save_session(conn)` → `find_save_campaign(conn)` (false if no living slotted character).
5. **Override:** `has_save = has_save or (has_active and awaiting not in ("SETUP", "SESSION_ENDED"))` — true for active `CHARACTER_CREATION` with empty roster.
6. UI queue: if `has_save` → narration "You have a saved game." + suggestions `["load game", "new game"]`; else new-game copy + `["new game"]`.
7. Exit: player sees misleading load offer; no auto-restore of `session_state.json` at this stage.

### Player chooses "load game"

1. Entry: `App._submit` → `_process_turn(text, turn_id)` (worker thread).
2. If text ∈ `{load game, load, continue, resume}` → queue `("load_session", None)` for main thread.
3. `orchestrator.process_turn("load game")` → `bridge.session_resume()` → `resume_session()`.
4. `find_save_campaign(conn)` → `None` → `{"ok": False, "error": "no save session found"}`.
5. Return: `"Could not resume: no save session found. Try 'new game' instead."` (APP-071 scope for friendlier copy).
6. Parallel: `_load_session()` may restore narration from `session_state.json`, but orchestrator already failed; creation/engine state not resumed via DB.

### Engine: when is a save resumable?

1. `find_save_campaign(conn)`:
   - Open session row via `_get_save_session`; if campaign has roster (`_campaign_has_roster`: slotted + alive) → return slug.
   - Else scan `characters` for slotted alive non-test campaigns.
2. `has_save_session` ≡ `find_save_campaign is not None`.
3. `resume_session` fails immediately if `save_campaign` is None — never reaches orchestrator's CHARACTER_CREATION restore block (orchestrator.py ~472–479).

### Engine status during partial creation

1. `active.json` present → session row loaded.
2. No characters / empty roster → `awaiting = "CHARACTER_CREATION"` (cmd_core.py ~178–180).
3. `has_active = True`, `has_save() = False`, current override → startup shows saved game (**mismatch**).

### Post-finalize / in-delve (regression guard)

1. Finalize populates character + `roster_set` → slotted alive character.
2. `find_save_campaign` returns campaign slug → `has_save()` true without override.
3. Startup saved-game prompt unchanged after fix.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-session-persistence-spec.md`](../../app-session-persistence-spec.md) — lists APP-064 open item; documents `session_resume` / empty roster problem class.
- Master registry: [`tmp/app-master-spec.md`](../../app-master-spec.md) — Session persistence row covers this behavior.
- PyGame UI spec: [`tmp/app-pygame-ui-spec.md`](../../app-pygame-ui-spec.md) — owns `ui/app.py` layout/controls; startup save **eligibility** should be documented in session-persistence spec per ticket AC.
- GameBridge spec: [`tmp/app-gamebridge-spec.md`](../../app-gamebridge-spec.md) — documents `has_save`, `session_resume`.
- Player README: [`app/README.md`](../../../app/README.md) line 15 — claims "auto-resumes if session_state.json or workspace save exists"; **inaccurate** for boot (no auto-resume; only manual load game triggers restore). Out of APP-064 Expected files; note for drift/human docs later.

## Tests & commands

```bash
# Engine session domain (indirect coverage of has_save_session)
python -m pytest play/tomb_gm/tests -q -k session

# App tests (no startup-save tests today)
python -m pytest app/tests -q

# Manual repro (Supa case)
cd app && python main.py
# Preconditions: active session in CHARACTER_CREATION, empty roster (e.g. partial creation, quit)
# Expect today: "You have a saved game" + load chip → error on load
# Expect after fix: new-game prompt only

# Manual regression: post-finalize save
# Complete character → quit → relaunch → must still show saved game + load game
```

No existing `app/tests` coverage for `_init_orchestrator` or startup suggestions. Ticket marks `app/tests/` optional — a headless unit test mocking `Orchestrator`/`bridge.has_save()` and `get_status()` would lock AC without PyGame display.

## Risks & unknowns

- **Mid-creation without resumable save:** After fix, players with only `session_state.json` + active empty-roster session see new-game path; they must type `new game` (wiping via `setup_new_game`) to proceed — may feel like progress loss until APP-018/071 improve continue UX. Not a regression of resume (load already failed).
- **`ROSTER_SETUP` edge:** Active session, characters exist but no slots — `has_save()` likely false, `awaiting` = `ROSTER_SETUP`; fix hides load (correct per engine); reconcile belongs to APP-017.
- **`session_state.json` vs engine truth:** App save can exist while `has_save()` is false; startup never reads it automatically. Spec should state: startup prompt follows **engine** resumability, not mere presence of `session_state.json`.
- **README drift:** "Auto-resumes" wording may confuse QA; not in ticket Expected files.
- **Thread timing:** `_load_session` queued before `process_turn` on load game — irrelevant to startup bug but relevant for APP-018 load path.
- **Test gap:** No automated guard; manual playtest required for AC sign-off.

## Raw notes

- Root override (bug):

```128:131:app/ui/app.py
                has_save = self._orchestrator.bridge.has_save()
                awaiting = status.get("awaiting", "SETUP")
                has_active = status.get("active") is not None
                has_save = has_save or (has_active and awaiting not in ("SETUP", "SESSION_ENDED"))
```

- Engine roster gate:

```100:105:play/tomb_gm/domain/session.py
def _campaign_has_roster(conn: sqlite3.Connection, campaign_slug: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 LIMIT 1",
        (campaign_slug,),
    ).fetchone()
    return row is not None
```

- Resume failure:

```220:222:play/tomb_gm/domain/session.py
    save_campaign = find_save_campaign(conn)
    if not save_campaign:
        return {"ok": False, "error": "no save session found"}
```

- Planned change (ticket Expected files): delete or narrow line 131 in `app/ui/app.py`; add startup save-detection rule + changelog to `tmp/app-session-persistence-spec.md`.
- Related in_progress: APP-071 (player-facing load failure message) — complementary, not blocking APP-064.
