# QA PASS: Implementation

**Task:** APP-064-startup-save-prompt  
**backlog_ticket:** APP-064  
**ticket_path:** tmp/backlog/app-064-startup-save-prompt-only-when-resumable.md  
**Round:** 1  
**Reviewer role:** QA (implementation review)  
**Verdict:** **PASS**

## Summary

Minimal fix matches plan and domain spec: startup `has_save` is **`bridge.has_save()` only**; the active-session OR override is removed. S2/S3 narration and suggestion branches are unchanged. Domain spec § Startup save-detection (APP-064) is on disk with checklist `[x]` and changelog entry. Mandated pytest suites are green.

**Blocker count:** 0

---

## Diff reviewed

| File | Change | Verdict |
|------|--------|---------|
| `app/ui/app.py` | Deleted L129–131: `awaiting`, `has_active`, and `has_save = has_save or (...)` | **Correct** — S1 |
| `tmp/app-session-persistence-spec.md` | § Startup save-detection (APP-064); behavior bullets; checklist + changelog | **Aligned** with code |

**Diff scope:** ⊆ ticket Expected files. No unauthorized edits to `orchestrator.py`, `bridge.py`, or `session.py`.

---

## Tests run

| Command | Result |
|---------|--------|
| `python -m pytest app/tests -q` | **pass** — 8 passed in 1.39s |
| `python -m pytest play/tomb_gm/tests -q -k session` | **pass** — 5 passed, 131 deselected in 1.69s |

**Note:** No new `test_startup_save_prompt.py` (T2 optional per plan). Existing suite does not assert empty-roster boot suggestions; manual T1a–T1c remains required for Stage 7.

---

## Ticket AC → implementation

| Ticket AC | On disk | QA |
|-----------|---------|-----|
| Startup saved-game + `load game` only when `bridge.has_save()` true | `_init_orchestrator`: `has_save = self._orchestrator.bridge.has_save()` then branch (L128–146); override gone | **PASS** |
| Active session, empty roster → new-game path | When `has_save()` false, else branch: new-game copy + `["new game"]` only (L142–146) | **PASS** (code); manual **T1a** pending |
| Resumable saves unchanged | `if has_save:` branch unchanged (L137–141) | **PASS** |
| Mid/post-finalize saves passing `has_save_session()` still offer load | No change when engine returns true; bridge `has_save()` → `has_save_session` | **PASS** |
| Domain spec updated with startup save-detection rule | § Startup save-detection (APP-064); checklist `[x]`; changelog 2026-05-20 | **PASS** |

---

## Spec S1–S4 → code

| Req | Status | Evidence |
|-----|--------|----------|
| **S1** Engine-only `has_save` at boot | **PASS** | `app/ui/app.py` L128; no widening |
| **S2** Resumable: saved-game line + both chips | **PASS** | L137–141 |
| **S3** Non-resumable: new-game copy + `["new game"]` | **PASS** | L142–146 |
| **S4** `session_state.json` not read at boot for prompt | **PASS** | `_load_session` only on `load_session` queue (L197–198); spec behavior bullets match |

---

## Independent verification

| Claim | Evidence | Result |
|-------|----------|--------|
| Override removed | `git diff app/ui/app.py` — 3 lines deleted | **Match** |
| Single saved-game narration site | Grep `app/`: only `app/ui/app.py:139` | **Match** |
| Bridge delegates to engine | `app/gm/bridge.py:395-397` → `has_save_session` | **Match** |
| Out of scope untouched | No diff in `orchestrator.py`, `bridge.py`, `session.py` | **Match** |

---

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Impl ⊆ Expected files | **PASS** | `app/ui/app.py`, `tmp/app-session-persistence-spec.md` |
| Plan minimal fix | **PASS** | Matches `plan.md` § Implementation steps |
| Spec ↔ code (APP-064 §) | **PASS** | Detection rule + UI table match branches |
| Automated tests | **PASS** | App + session smoke |
| Manual T1a–T1c | **DEFER** | Stage 7 `human-test-plan.md`; do not block impl PASS |

---

## Non-blocking (release / Stage 7)

- Manual playtest **T1a** (Supa partial-creation boot), **T1b** (post-finalize load), **T1c** (fresh workspace) not executed in this QA round.
- Optional **T2** headless startup test still absent — acceptable per ticket/plan.
- Ticket **Status** still `in_progress`; orchestrator runs `release APP-064 --done` after drift check.
- `status.md` pipeline checklist not yet advanced past spec stage — parent updates on batch close.

---

## Handoff

**Ready for:** Drift check, `release APP-064 --done`, Stage 7 human playtest (T1a–T1c), batch board progression.
