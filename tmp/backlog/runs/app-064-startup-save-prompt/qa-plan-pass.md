# QA PASS: plan

**Task:** APP-064-startup-save-prompt
**backlog_ticket:** APP-064
**ticket_path:** tmp/backlog/app-064-startup-save-prompt-only-when-resumable.md
**Round:** 1
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` § Startup save-detection (APP-064))
- [x] Acceptance criteria testable (S1–S4, T1a–T1c; optional T2)
- [x] Code traces match repo (independent re-trace below)
- [x] AGENTS.md / canon compliance (app UI only; no engine/canon edits)
- [x] Tests/commands listed (`pytest` session smoke + app; manual T1a–T1c required)
- [x] Plan files ⊆ ticket Expected files (`app/ui/app.py`, `tmp/app-session-persistence-spec.md`, optional `app/tests/`)
- [x] registry_gap not applicable at plan stage (spec QA confirmed `not_needed`)

## Independent code trace (adversarial)

| Claim | Repo evidence | Verdict |
|-------|---------------|---------|
| Bug override at startup | `app/ui/app.py:128-131` — `has_save` widened by `has_active and awaiting not in ("SETUP", "SESSION_ENDED")` | Confirmed |
| Only startup site for saved-game copy | Grep: `"You have a saved game"` appears only in `app/ui/app.py:142` | Confirmed — no missed UI path |
| Engine gate | `play/tomb_gm/domain/session.py:116-137` — `has_save_session` ≡ `find_save_campaign`; requires slotted + alive | Confirmed |
| Bridge thin wrapper | `app/gm/bridge.py:395-397` — delegates to `has_save_session` | Confirmed |
| Supa repro awaiting | `play/tomb_gm/cli/cmd_core.py:178-180` — empty roster + no chars → `CHARACTER_CREATION` | Confirmed |
| Load failure path unchanged | `app/gm/orchestrator.py:444-448` — `session_resume` error when no save | Confirmed |
| Post-fix branch logic | Lines 140-149 unchanged; `has_save` alone drives S2/S3 | Correct |
| `status` still needed after removing locals | Line 126 queues `("status", status)` for sidebar before branch | Confirmed — safe to drop `awaiting`/`has_active` |

## AC mapping (plan → ticket)

| Ticket AC | Plan coverage |
|-----------|---------------|
| Saved game + load only when `has_save()` true | Steps §1 remove override; edge matrix rows 1–4 |
| Empty roster → new-game path | Edge matrix row 2 (Supa); manual T1a |
| Resumable behavior unchanged | Trace D; manual T1b; non-regression note |
| Mid/post-finalize with `has_save_session()` still offers load | Trace D; relies on engine truth without override |
| Domain spec updated | Step §2 checklist + changelog on close |

## Scope gate

| File | In ticket Expected? | In plan? |
|------|----------------------|----------|
| `app/ui/app.py` | Yes | Yes — delete L129-131 |
| `tmp/app-session-persistence-spec.md` | Yes | Yes — close metadata |
| `app/tests/` (optional) | Yes | Yes — deferred T2 |
| `app/gm/orchestrator.py`, `bridge.py`, `session.py` | No (correctly out) | Explicitly excluded |

## Notes (non-blocking)

1. **Typo in plan trace A11:** `157-151` should read `157-158` (`_process_ui_queue` drain). Does not affect implementation.
2. **Weak automated guard:** `python -m pytest play/tomb_gm/tests -q -k session` is smoke/regression only — no test asserts `has_save_session()` false with empty-roster open session. Plan correctly mandates manual T1a–T1c; impl QA must not sign off on pytest alone.
3. **Optional T2:** Existing `app/tests/conftest.py` `bridge` + `isolated_workspace` fixtures support engine-only assertions if Dev adds `test_startup_save_prompt.py`; plan's deferral aligns with ticket optional tests.
4. **Known follow-on UX:** Partial-creation boot → new-game chip → `setup_new_game` may hit active-session errors (APP-014). Plan documents; not APP-064 scope.
5. **Mid-delve regression:** Domain spec T1b includes in-delve; plan manual table says "Complete character" — sufficient if slotted living character exists; impl may add explicit in-delve relaunch if T1b alone feels thin.

**Verdict:** PASS — plan is implementation-ready; minimal fix matches spec S1–S4; no blockers.
