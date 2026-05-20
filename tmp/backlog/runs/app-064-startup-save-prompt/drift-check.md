# Drift Check: APP-064-startup-save-prompt

**backlog_ticket:** APP-064  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Startup save-detection (APP-064) | no | S1–S4 match `_init_orchestrator`; checklist `[x]`; changelog **APP-064 done** row present |
| Run `spec.md` S1–S4, T1–T2 | no | Verified against `app/ui/app.py`, `app/gm/bridge.py`, engine `has_save_session` |
| [`tmp/backlog/app-064-startup-save-prompt-only-when-resumable.md`](../../app-064-startup-save-prompt-only-when-resumable.md) | no | AC checked in ticket file |

## Code ↔ domain spec (APP-064)

| Requirement | Code | Match |
|-------------|------|-------|
| **S1** Startup `has_save` = `bridge.has_save()` only; no active-session override | `app/ui/app.py` L128: single assignment; deleted L129–131 override per git diff | yes |
| **S2** `has_save()` true → "You have a saved game." + `["load game", "new game"]` | L137–141 | yes |
| **S3** `has_save()` false → new-game copy + `["new game"]` only | L142–146 | yes |
| **S4** `session_state.json` not read at boot for prompt; `_load_session` on load command only | Boot path queues narration/suggestions only; `_load_session` via `load_session` queue (L197–198) on load aliases (L281–282) | yes |
| **Non-regression** No change to `session_resume`, `find_save_campaign`, bridge wrappers | No diff in `orchestrator.py`, `bridge.py`, `session.py` | yes |
| Bridge delegates to engine | `bridge.py` L395–397 → `has_save_session(self.ctx.conn)` | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| Startup saved-game + `load game` only when `bridge.has_save()` true | **PASS** |
| Active session, empty roster → new-game path | **PASS** (code; manual T1a deferred Stage 7) |
| Resumable saves unchanged | **PASS** |
| Mid/post-finalize saves passing `has_save_session()` still offer load | **PASS** |
| Domain spec updated with startup save-detection rule | **PASS** |

## Tests run

```bash
python -m pytest app/tests -q
python -m pytest play/tomb_gm/tests -q -k session
```

**Result:** 11 passed (app); 5 passed, 131 deselected (session)

**Note:** Optional **T2** headless startup test not added — acceptable per spec/ticket. Manual **T1a–T1c** not executed in drift round (Stage 7).

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § APP-064 + changelog aligned with code
- [ ] Ticket **Status** → `done` / **Closed** date — orchestrator at `release APP-064 --done`
- [ ] `python tmp/backlog/claim_ticket.py release APP-064 --done` — orchestrator (not QA drift agent)

## Ancillary notes (non-blocking)

- Domain spec **Open work** line still lists APP-064 alongside closed checklist item — pre-existing index wording; no code drift.
- Spec header **Status: In progress** reflects broader session-persistence backlog (APP-014–APP-020), not APP-064 regression.
- APP-071 sections in same domain spec file are separate ticket scope; not evaluated for APP-064 drift beyond shared boot bullet (line 13), which matches code.
