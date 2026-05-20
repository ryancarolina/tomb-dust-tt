# Research Brief: APP-071-friendly-load-no-save

**Date:** 2026-05-20
**Question:** Why does `load game` with no resumable save leave players without actionable recovery, and what code paths must change for friendly narration + logging?

**backlog_ticket:** APP-071
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md
**domain_spec:** tmp/app-session-persistence-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) owns resume flow, `session_state.json`, and orchestrator session lifecycle (`setup_new_game`, resume). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row: **Session persistence** → `app-session-persistence-spec.md` → `session_state.json`, autosave, resume. Cross-cutting JSONL behavior is documented in [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) (`error` + `gm_narration` event types) but does not own resume failure copy — no new domain spec required.

## Summary

`load game` is handled in `Orchestrator.process_turn` (lines 444–448): it calls `bridge.session_resume()` and, on failure, logs `log_error("session_resume", …)` and returns a one-line string (`Could not resume: … Try 'new game' instead.`). That return value reaches the narration panel via `ui/app.py` → `narration_text`, but the failure path **does not** call `_emit_narration`, so JSONL logs show only an `error` event — matching the Supa session evidence (no `gm_narration` for the player message).

The message is engine-centric (`no save session found`), offers no creation-step context, and does not update suggestion chips ( `_extract_suggestions` only parses `[Awaiting: …]` footers). Mid-creation players who type `load game` while `creation.active` is true still hit `session_resume` first and get the generic error instead of guidance to continue creation or start over. Engine resume eligibility (`has_save_session` / `find_save_campaign`) requires a living slotted character; open sessions with empty roster (typical mid-creation) are not resumable — overlapping APP-064 startup messaging that offers `load game` when `has_active` but not `has_save`.

Implementation should enrich the orchestrator failure branch (creation-aware copy, `_emit_narration` for JSONL parity), optionally push suggestion chips from UI on failure, and document resume-failure behavior in the session-persistence spec. APP-019 (UI toast for `new game` failures) has no toast infrastructure today; coordinate messaging patterns but keep APP-071 scope in orchestrator + spec unless PM expands Expected files.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Load/resume command | `app/gm/orchestrator.py` `process_turn` | Lines 444–448 failure branch; no `_emit_narration` |
| Narration emit + JSONL | `app/gm/orchestrator.py` `_emit_narration` | Calls `log_gm_narration`; unused on resume failure |
| JSONL logger | `app/gm/logger.py` | `log_error`, `log_gm_narration`; no `log_player_message` |
| Engine resume gate | `play/tomb_gm/domain/session.py` | `resume_session`, `has_save_session`, `find_save_campaign` |
| Bridge wrapper | `app/gm/bridge.py` | `session_resume()`, `has_save()` |
| UI turn thread | `app/ui/app.py` `_process_turn`, `_process_ui_queue` | Queues `load_session`, then `narration_text` |
| App-side restore | `app/ui/app.py` `_load_session` | Restores `session_state.json` on every load command |
| Creation FSM | `app/gm/creation.py` | `CreationState`, `format_creation_status`, `CREATION_STATUS_LABELS` |
| Creation sync | `app/gm/orchestrator.py` `_sync_creation_from_status` | Sets `creation.active` when engine awaiting creation + empty roster |
| Startup save prompt | `app/ui/app.py` `_init_orchestrator` | `has_save \|\| (has_active && awaiting not SETUP/ENDED)` — APP-064 overlap |
| Related tickets | `tmp/backlog/app-019-*.md`, `app-064-*.md` | Toast vs narration; startup false-positive save prompt |

## Code-path traces

### Player types `load game` (failure — no engine save)

1. **Entry:** `App._submit` → `_process_turn(text, turn_id)` (`app/ui/app.py:273`)
2. UI queues `("processing", …)`, `("player", text)`, then `("load_session", None)` because text ∈ `{load game, load, continue, resume}` (284–285)
3. **Orchestrator:** `process_turn("load game")` → `log_player_input` → `bridge.session_resume()` (`orchestrator.py:444–445`)
4. **Engine:** `resume_session` → `find_save_campaign(conn)` returns `None` → `{"ok": False, "error": "no save session found"}` (`session.py:220–222`)
5. **Failure exit:** `log_error("session_resume", error)` → return f-string (447–448). **Skips** `_emit_narration` / `log_gm_narration`
6. UI thread: `_process_ui_queue` may run `_load_session()` — if `app/session_state.json` exists, replays saved narration + `import_creation_state` (430–452)
7. UI queues `("narration_text", narration)` with failure string (300); `_extract_suggestions` returns `[]` (no status footer)
8. **Persistence:** `_save_session()` in `finally` if narration not None (327–328)

### Player types `load game` (success — has roster save)

1. Same entry through `session_resume` → ok
2. `_restore_history`, `_sync_creation_from_status`, `_sync_combat_from_status` (466–468)
3. If `awaiting == CHARACTER_CREATION` and empty roster → `_creation_turn` with resume system prompt (472–479)
4. Else builds recap summary and falls through to normal LLM turn (483–492)

### Mid-creation in memory (Supa scenario)

1. Player already in `_creation_turn` flow; `self.creation.active == True`, `creation.step` e.g. `RACE`
2. Engine: open session, `awaiting: CHARACTER_CREATION`, `roster: []` → `has_save_session()` **false**
3. Player types `load game` → resume branch runs **before** line-494 `if self.creation.active` guard
4. `session_resume` fails → generic error; no copy like “you’re already creating a character at step X”
5. Autosave may have written `creation_state` to `session_state.json`; `_load_session` may re-import it while showing error — potentially confusing but creation state preserved

### Startup → misleading load suggestion (APP-064, not APP-071 scope)

1. `_init_orchestrator`: `has_save = bridge.has_save()` then OR `(has_active && awaiting not in SETUP/SESSION_ENDED)` (128–131)
2. If true → narration “You have a saved game.” + suggestions `["load game", "new game"]` (140–144)
3. Mid-creation open session satisfies `has_active` → user encouraged to load → hits failure path above

## Existing specs & docs

- **Ticket domain spec:** `tmp/app-session-persistence-spec.md` — lists `session_resume → no save session found` as known problem; no resume-failure player-copy requirement yet
- **Logging:** `tmp/app-logging-qa-spec.md` — `gm_narration` = “Final text to UI”; `error` = setup failures; failure path currently only logs latter
- **GameBridge:** `tmp/app-gamebridge-spec.md` — documents `session_resume`, `has_save`
- **APP-019:** open; UI toast for `new game` failures; QA note points to APP-071 for load-game copy
- **APP-064:** open; startup prompt should gate on `has_save_session()` only

## Tests & commands

```bash
# Manual smoke (no automated load-game failure test today)
cd app && python main.py
# 1. Fresh workspace: type "load game" → expect friendly narration + JSONL error + gm_narration
# 2. Mid-creation: "new game" → name → "load game" → expect creation-aware message

# Engine save gate (headless)
python -c "
from pathlib import Path
import sqlite3
from tomb_gm.domain.session import has_save_session, resume_session
from tomb_gm.runtime.config import load_config
cfg = load_config(Path('play/workspace'))
conn = sqlite3.connect(cfg.db_path)
conn.row_factory = sqlite3.Row
print('has_save', has_save_session(conn))
print('resume', resume_session(conn, cfg))
"

# Existing app tests (no load-game coverage)
python -m pytest app/tests -q -k "creation" --ignore=app/tests/test_creation_flow.py 2>/dev/null || python -m pytest app/tests -q
```

## Risks & unknowns

- **`_load_session` on failed resume:** Restoring `session_state.json` before showing error may duplicate or clash with failure copy; PM should decide whether to skip `_load_session` when resume will fail (would need pre-check or reorder).
- **Mid-creation detection signals:** Prefer `self.creation.active` + `creation.step`; also consider `bridge.has_save()`, `SAVE_PATH.exists()`, and engine `awaiting == CHARACTER_CREATION` for message variants per AC.
- **Suggestion chips:** Failure strings lack `[Awaiting: …]`; may need explicit `("suggestions", ["new game"])` from UI or footer in orchestrator message for chip UX.
- **APP-019 toast:** No `toast` references in `app/`; ticket AC “extend APP-019 or close together” may mean shared error-surfacing pattern, not mandatory toast for APP-071.
- **`log_player_message`:** Ticket mentions optional helper — **does not exist**; use `_emit_narration` / `log_gm_narration` per logging spec.
- **Test gap:** No pytest for `process_turn("load game")` failure; recommend adding in APP-071 or APP-049 follow-up.

## Raw notes

- Failure return (current): `Could not resume: no save session found. Try 'new game' instead.` — present since initial app commit (`0499afa`).
- Ticket evidence: JSONL `{"context":"session_resume","error":"no save session found"}` only — consistent with missing `_emit_narration`.
- `find_save_campaign`: requires `characters.slot IS NOT NULL AND alive = 1` (`session.py:100–105`, `116–120`).
- UI error channel (`msg_type == "error"`) prefixes `[Error: …]` — used for exceptions, not orchestrator return strings.
- `setup_new_game` failure (437–441) same pattern: `log_error` + return string, no `_emit_narration`.
- Orchestrator init loads creation from `session_state.json` in `_restore_history` (104–118) but only on successful resume path calls `_restore_history` at 466.
