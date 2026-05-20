# APP-064: Startup save prompt only when resumable

| Field | Value |
|-------|-------|
| **ID** | APP-064 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

On launch, the PyGame app shows **"You have a saved game"** and offers **load game** whenever any engine session is active — even when `has_save_session()` is **false** (empty roster, no living character). Players then get **"Could not resume: no save session found"** after choosing load. Startup messaging must match engine resume eligibility.

**Repro (supa case):** Active session in `CHARACTER_CREATION` with empty roster → boot shows saved game → `load game` fails.

## Acceptance criteria

- [x] Startup **only** shows "You have a saved game" + `load game` suggestion when `bridge.has_save()` (`has_save_session`) is **true**.
- [x] Active session with **empty roster** and no resumable save shows the **new-game** path (same as no session): prompt to type `new game`, suggestions `["new game"]` only.
- [x] When resumable, behavior unchanged: saved-game line + `["load game", "new game"]`.
- [x] No regression: mid-creation or post-finalize saves that **do** pass `has_save_session()` still offer load.
- [x] Domain spec updated with startup save-detection rule.

## Expected files

- `app/ui/app.py` — remove or narrow `_init_orchestrator` override that sets `has_save = has_save or (has_active and awaiting not in ("SETUP", "SESSION_ENDED"))`
- `tmp/app-session-persistence-spec.md`
- `app/tests/` _(if startup init is testable; optional smoke)_

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

- Root cause: `app/ui/app.py` treats **any** non-ended active session as a save, but `session_resume` / `has_save_session` require a campaign with a **living character on the roster** (`find_save_campaign`).
- **Related:** [APP-017](app-017-reconcile-empty-roster-on-load.md) (load path when roster empty), [APP-009](app-009-finalize-gate---non-empty-roster.md) (finalize must populate roster), [APP-018](app-018-continue-restores-creation-state.md) (continue mid-creation).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-017 | related — load/reconcile when roster empty |
| APP-009 | related — prevents empty roster after finalize |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-064 --task startup-save-prompt
python tmp/backlog/claim_ticket.py release APP-064 --done
```
