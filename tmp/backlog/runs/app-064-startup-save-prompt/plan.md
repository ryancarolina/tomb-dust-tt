# Dev Plan: APP-064 — Startup save prompt only when resumable

**backlog_ticket:** APP-064  
**run-folder:** `tmp/backlog/runs/app-064-startup-save-prompt/`  
**domain_spec:** `tmp/app-session-persistence-spec.md` § Startup save-detection (APP-064)  
**status:** plan (Dev phase)

## Summary

Remove the `_init_orchestrator` override that treats any non-ended active session as a save. After the fix, startup narration and suggestion chips follow **`bridge.has_save()` only** (engine `has_save_session()` / `find_save_campaign()`). One-line code change; spec checklist + changelog on close.

---

## Root cause

```128:131:app/ui/app.py
                has_save = self._orchestrator.bridge.has_save()
                awaiting = status.get("awaiting", "SETUP")
                has_active = status.get("active") is not None
                has_save = has_save or (has_active and awaiting not in ("SETUP", "SESSION_ENDED"))
```

| Layer | Truth | Startup UI (bug) |
|-------|--------|-------------------|
| `bridge.has_save()` → `has_save_session()` | `find_save_campaign()` ≠ None (slotted + alive) | Correct first read |
| Line 131 OR | Active session + `awaiting` ∉ `{SETUP, SESSION_ENDED}` | **Widens** to true for empty-roster `CHARACTER_CREATION` |
| `process_turn("load game")` → `session_resume()` | Fails when `find_save_campaign` is None | Player already offered load |

Engine gate (unchanged):

```100:105:play/tomb_gm/domain/session.py
def _campaign_has_roster(conn: sqlite3.Connection, campaign_slug: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 LIMIT 1",
        (campaign_slug,),
    ).fetchone()
```

```220:222:play/tomb_gm/domain/session.py
    save_campaign = find_save_campaign(conn)
    if not save_campaign:
        return {"ok": False, "error": "no save session found"}
```

---

## Deep code-path traces

### A. Application boot → startup prompt (bug surface)

| Step | Location | Action |
|------|----------|--------|
| A1 | `app/main.py:24-29` | `main()` → `App(config).run()` |
| A2 | `app/ui/app.py:42-49` | `run()` → `_layout()` → `_init_orchestrator()` (daemon thread) |
| A3 | `app/ui/app.py:123-125` | `Orchestrator(self.config)` → `GameBridge()` → `init()` |
| A4 | `app/gm/orchestrator.py` | `get_status()` → `bridge.status()` |
| A5 | `app/gm/bridge.py` | `status()` → `handle_status` (`play/tomb_gm/cli/cmd_core.py`) |
| A6 | `app/ui/app.py:128` | `has_save = bridge.has_save()` → `has_save_session(conn)` |
| A7 | `play/tomb_gm/domain/session.py:116-137` | `find_save_campaign` → False if no slotted alive character |
| A8 | `play/tomb_gm/cli/cmd_core.py:178-180` | Empty roster + no chars → `awaiting: "CHARACTER_CREATION"` |
| A9 | `app/ui/app.py:129-131` | **Bug:** `has_save` forced True when `has_active` and awaiting not SETUP/ENDED |
| A10 | `app/ui/app.py:133-149` | Queue title block; branch on `has_save` → narration + suggestions |
| A11 | `app/ui/app.py:157-151` | Main thread `_process_ui_queue()` drains queue on pygame tick |

**Supa repro state at A8–A9:** `active.json` + open session row, `roster: []`, `has_save() == False`, `has_active == True`, `awaiting == "CHARACTER_CREATION"` → override → saved-game branch.

**Post-fix at A9:** Delete lines 129–131 (or line 131 only); `has_save` stays engine result.

### B. Engine status during partial creation (feeds A8, not startup decision after fix)

| Step | Location | Action |
|------|----------|--------|
| B1 | `play/workspace/.local/active.json` | Present → `payload["active"]` set |
| B2 | `cmd_core.py:102-113` | Session row missing → `awaiting: SETUP` (edge) |
| B3 | `cmd_core.py:177-184` | Open session: no roster + no chars → `CHARACTER_CREATION`; chars but no slots → `ROSTER_SETUP`; else `PLAYER_ACTIONS` |
| B4 | `session.py:find_save_campaign` | Open session without roster on campaign → scan characters; still None if no slotted alive |

After fix, B3 `awaiting` is **informational only** at startup (sidebar status); not used for save prompt.

### C. Player chooses "load game" (unchanged; explains user-visible failure today)

| Step | Location | Action |
|------|----------|--------|
| C1 | `app/ui/app.py:273-292` | `_process_turn`: if text ∈ `{load game, load, continue, resume}` → queue `("load_session", None)` |
| C2 | `app/ui/app.py:292` | `orchestrator.process_turn(text)` same thread |
| C3 | `app/gm/orchestrator.py:444-448` | `bridge.session_resume()`; on failure return `"Could not resume: …"` |
| C4 | `play/tomb_gm/domain/session.py:210-222` | `resume_session` → `find_save_campaign` None → error |
| C5 | `app/ui/app.py:200-201` | Main thread `_load_session()` reads `session_state.json` (UI only; does not fix engine resume) |

APP-064 does **not** modify C3–C5. APP-071 owns friendlier failure copy when user still types load.

### D. Resumable save path (regression guard)

| Step | Location | Action |
|------|----------|--------|
| D1 | Creation finalize / `roster_set` | Slotted alive character on campaign |
| D2 | `find_save_campaign` | Returns campaign slug |
| D3 | `bridge.has_save()` | True **without** UI override |
| D4 | `app/ui/app.py:140-144` | "You have a saved game." + `["load game", "new game"]` |
| D5 | C3 success | `resume_session` ok → orchestrator CHARACTER_CREATION / delve / combat branches |

### E. Bridge wrapper (no change expected)

```395:397:app/gm/bridge.py
    def has_save(self) -> bool:
        from tomb_gm.domain.session import has_save_session
        return has_save_session(self.ctx.conn)
```

---

## Implementation steps

### 1. Code change — `app/ui/app.py`

**File:** `app/ui/app.py`  
**Function:** `_init_orchestrator` → inner `_init()` (lines 128–131)

| Action | Detail |
|--------|--------|
| Remove override | Delete line 131: `has_save = has_save or (has_active and awaiting not in (...))` |
| Remove dead locals | Delete `awaiting` and `has_active` assignments (lines 129–130) — unused after fix |
| Keep | `has_save = self._orchestrator.bridge.has_save()` |
| Keep | Lines 133–149 branches unchanged (S2/S3 table in domain spec) |

**Do not change:** `orchestrator.py`, `bridge.py`, `session.py`, `_process_turn`, `_load_session`, `SAVE_PATH` boot behavior.

### 2. Domain spec — `tmp/app-session-persistence-spec.md` (on ticket close)

| Action | Detail |
|--------|--------|
| Checklist | Mark APP-064 open item `[x]` in Task checklist |
| Changelog | Append dated entry: "APP-064 done: startup prompt uses engine `has_save()` only" |
| Verify | § Startup save-detection (APP-064) already documents S1–S4, T1–T2 — no behavior rewrite unless drift found |

**Do not edit** `tmp/app-master-spec.md` unless registry row is wrong (research: not needed).

### 3. Optional automated test — `app/tests/` (T2)

**Recommendation:** Defer T2; satisfy AC with manual T1a–T1c. Ticket marks tests optional.

If implementing T2:

| Approach | Pros | Cons |
|----------|------|------|
| Extract `startup_suggestions(has_save: bool)` | Easy unit test | Extra abstraction for one branch |
| Mock `Orchestrator` + drain `_ui_queue` on `App` | Tests real `_init_orchestrator` | Requires pygame display or heavy mocking |

Preferred minimal T2 (if required): new `app/tests/test_startup_save_prompt.py` with bridge fixture asserting `has_save()` false/true in isolated workspace scenarios that mirror T1a/T1b **engine** preconditions — documents alignment but does not assert UI queue without pygame.

---

## Edge-case matrix (post-fix)

| Scenario | `has_save()` | `has_active` | `awaiting` | Startup branch |
|----------|--------------|------------|------------|----------------|
| No session / SETUP | False | No/SETUP | SETUP | New game (S3) |
| Partial creation, empty roster | False | Yes | CHARACTER_CREATION | New game (S3) — **fixes Supa** |
| ROSTER_SETUP, no resumable save | False | Yes | ROSTER_SETUP | New game (S3) |
| `session_state.json` only, no engine save | False | Maybe | * | New game (S4) |
| Post-finalize / in-delve, living slotted | True | Yes | PLAYER_ACTIONS / COMBAT | Saved game (S2) |
| SESSION_ENDED | False* | Yes | SESSION_ENDED | New game unless engine save elsewhere |

\*Engine may still find save via character scan if session ended but characters remain; trust `has_save()` only.

**Known UX (not regression):** Partial creation with only app save sees new-game path; player types `new game` → `setup_new_game` (APP-014/018 scope).

---

## Test plan

### Commands

```bash
python -m pytest play/tomb_gm/tests -q -k session
python -m pytest app/tests -q
```

### Manual (required — domain spec T1)

| ID | Steps | Expected |
|----|-------|----------|
| **T1a** | Partial creation → quit → `cd app && python main.py` | No "You have a saved game"; chip `new game` only |
| **T1b** | Complete character → quit → relaunch | Saved-game line + `load game` + `new game`; load succeeds |
| **T1c** | Fresh workspace / no save | New-game path only |

### Regression checks

- Sidebar still receives `("status", status)` at init (line 126).
- Title narration block unchanged (lines 133–137).
- Load path still calls `session_resume` then `_load_session` on user action.

---

## Files (subset of ticket Expected files)

| File | Change |
|------|--------|
| `app/ui/app.py` | Remove lines 129–131 (override + dead locals) |
| `tmp/app-session-persistence-spec.md` | Checklist + changelog on close |
| `app/tests/test_startup_save_prompt.py` | _(optional)_ engine-aligned or UI mock test |

**Out of scope (per spec non-goals):** `app/gm/orchestrator.py`, `app/gm/bridge.py`, `play/tomb_gm/domain/session.py`, `app/README.md`, APP-071/017/018.

---

## Acceptance criteria checklist (Dev impl)

- [ ] Startup saved-game + `load game` only when `bridge.has_save()` true (S1, S2)
- [ ] Active empty roster → new-game path (S3)
- [ ] Resumable saves unchanged (T1b)
- [ ] Domain spec checklist + changelog (close)
- [ ] `python -m pytest play/tomb_gm/tests -q -k session` green
- [ ] Manual T1a–T1c executed or noted in run `status.md`

---

## Risk notes

| Risk | Mitigation |
|------|------------|
| Players expect load mid-creation | Documented in spec; APP-018/071 |
| Dead code lint on removed vars | Remove `awaiting`/`has_active` with override |
| False confidence from engine-only pytest | Manual T1a still required |

---

## Estimated diff

~3 lines removed in `app/ui/app.py`; spec metadata on close. No engine/bridge/orchestrator changes.
