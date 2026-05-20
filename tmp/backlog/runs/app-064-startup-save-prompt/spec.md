# Spec: APP-064-startup-save-prompt

**Status:** draft (PM round 1)  
**backlog_ticket:** APP-064  
**ticket_path:** [tmp/backlog/app-064-startup-save-prompt-only-when-resumable.md](../../app-064-startup-save-prompt-only-when-resumable.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md)  
**registry_gap:** false (per research-brief)  
**Domain specs touched:** `tmp/app-session-persistence-spec.md`

## Problem

On launch, `_init_orchestrator` in `app/ui/app.py` calls `bridge.has_save()` (engine `has_save_session()`), then **widens** it: any active session whose `awaiting` is not `SETUP` or `SESSION_ENDED` is treated as resumable. That includes `CHARACTER_CREATION` with an **empty roster** (Supa repro) — where `find_save_campaign()` returns `None` because resume requires a living slotted character.

Players see **"You have a saved game"** + **load game** chip, then **"Could not resume: no save session found"** after choosing load. Startup messaging must match engine resume eligibility, not merely "active session exists."

## Goals

- **P0:** Startup saved-game prompt and suggestions follow **`bridge.has_save()` only** (no active-session override).
- **P0:** Empty-roster partial creation shows the **new-game** path (same as no session).
- **P0:** Document startup save-detection rule in session-persistence domain spec.

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Friendly copy when load fails after user picks load | APP-071 |
| Restore mid-creation from `session_state.json` without engine save | APP-018 |
| Reconcile empty roster on load path | APP-017 |
| Auto-read `session_state.json` at boot | Out of scope — app save loads only on explicit **load game** |
| Fix `app/README.md` "auto-resumes" wording | Not in Expected files |

## Requirements (summary)

Full behavior and test contracts live in the domain spec § **Startup save-detection (APP-064)**.

| ID | Summary | Domain spec |
|----|---------|-------------|
| **S1** | Startup `has_save` = `bridge.has_save()` only; remove active-session OR override | § Detection rule |
| **S2** | When `has_save()` true: saved-game narration + `["load game", "new game"]` (unchanged) | § UI branches |
| **S3** | When `has_save()` false (incl. active empty roster): new-game copy + `["new game"]` only | § UI branches |
| **S4** | Prompt follows **engine** resumability, not `session_state.json` presence at boot | § Engine vs app save |
| **T1** | Manual repro + regression cases (post-finalize still offers load) | § Tests APP-064 |
| **T2** | Optional headless unit test mocking `Orchestrator` / `bridge.has_save()` | § Tests APP-064 |

## Acceptance criteria mapping

| Ticket AC | Spec / deliverable |
|-----------|-------------------|
| Startup shows saved game + load only when `has_save()` true | S1, S2 |
| Active empty roster → new-game path | S1, S3 |
| Resumable saves unchanged | S2, T1 regression |
| Mid/post-finalize saves passing `has_save_session()` still offer load | S2, T1 |
| Domain spec updated with startup save-detection rule | Domain spec § APP-064 |

## Implementation pointers (Dev plan)

| Area | Path | Notes |
|------|------|-------|
| Bug | `app/ui/app.py` `_init_orchestrator` ~128–131 | Delete or narrow: `has_save = has_save or (has_active and awaiting not in (...))` |
| Engine gate | `play/tomb_gm/domain/session.py` | `has_save_session` ≡ `find_save_campaign` (slotted + alive) |
| Load path | `app/gm/orchestrator.py` `process_turn` | `session_resume` fails when `find_save_campaign` None — unchanged |
| Bridge | `app/gm/bridge.py` `has_save()` | Thin wrapper — no change expected |

**Minimal fix:** trust `bridge.has_save()` result; remove line 131 override.

## Test plan

```bash
# Engine session domain (indirect has_save_session coverage)
python -m pytest play/tomb_gm/tests -q -k session

# App tests (optional new startup test)
python -m pytest app/tests -q
```

Manual cases in domain spec § Tests APP-064.

## Human playtest hints (for Stage 7)

- **Supa repro:** Partial creation (empty roster) → quit → relaunch → must **not** show saved game or load chip; only new-game prompt.
- **Regression:** Complete character → quit → relaunch → must still show saved game + load + new game chips; load succeeds.
- **Mid-delve:** Save with living character on roster → relaunch → saved-game prompt unchanged.

## Affected paths

Must match ticket **Expected files**:

- `app/ui/app.py` — `_init_orchestrator` startup branch
- `tmp/app-session-persistence-spec.md` — § Startup save-detection (APP-064)
- _(optional)_ `app/tests/` — headless startup suggestion test

## Pointers (source of truth)

| Topic | Location |
|-------|----------|
| Startup save-detection behavior & tests | [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Startup save-detection (APP-064) |
| Research traces & code paths | [`research-brief.md`](research-brief.md) |
| Engine resume eligibility | `play/tomb_gm/domain/session.py` — `find_save_campaign`, `has_save_session`, `resume_session` |
| Bridge API | `tmp/app-gamebridge-spec.md` — `has_save`, `session_resume` |
| Bug site | `app/ui/app.py` `_init_orchestrator` ~128–149 |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-064) |
