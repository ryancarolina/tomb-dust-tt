# QA PASS: plan

**Task:** APP-020-document-stuck-creation-recovery
**backlog_ticket:** APP-020
**ticket_path:** tmp/backlog/app-020-document-stuck-creation-recovery.md
**Round:** 1
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` § Stuck creation recovery — player documentation (APP-020))
- [x] Acceptance criteria testable (R-020a–g checklist + T-020a–b manual cross-check)
- [x] Code traces match repo (independent re-trace below)
- [x] AGENTS.md / canon compliance (PyGame canonical play; no hand-edit / `tomb_gm` CLI recovery; doc-only chore)
- [x] Tests/commands listed (T-020a checklist review; T-020b manual APP-014 TC-1; optional pytest smoke only)
- [x] Plan impl files ⊆ ticket Expected files (`app/README.md` only; domain spec sync deferred to close per ticket)
- [x] registry_gap not applicable at plan stage (spec QA confirmed `not_needed`)

## Independent code trace (adversarial)

| Claim | Repo evidence | Verdict |
|-------|---------------|---------|
| Stale Quick Start L15 auto-resume claim | `app/README.md:15` — "auto-resumes if `session_state.json` or a workspace save exists" | Confirmed — plan root cause correct |
| Stale Features L59 persistence claim | `app/README.md:59` — "auto-saves every 60s, restores on relaunch" | Confirmed |
| Boot uses `has_save()` only | `app/ui/app.py:128` → `bridge.has_save()`; branches `137–146` | Confirmed |
| Engine save gate | `play/tomb_gm/domain/session.py:116–137` — `find_save_campaign` / `has_save_session`; slotted living character | Confirmed |
| Bridge wrapper | `app/gm/bridge.py:395–397` | Confirmed |
| `new game` aliases | `app/ui/app.py:283`; `orchestrator.py:824` — `new game`, `start`, `new` | Confirmed |
| `setup_new_game` lifecycle | `orchestrator.py:665–683` — reset, clear block, end/wipe/init, NAME, `_delete_save_file` | Confirmed |
| APP-018 restore on first non–`new game` turn | `orchestrator.py:833–834` → `_restore_creation_from_session_state`; gate `547–571` | Confirmed |
| APP-071 variant B copy | `orchestrator.py:645–656` — "Keep answering the clerk's prompts… or type **new game**" | Confirmed |
| Autosave interval | `app/ui/app.py:216–220` — 60s `_autosave` | Confirmed |

## AC mapping (plan → ticket / spec)

| Ticket AC / Spec | Plan coverage |
|------------------|---------------|
| README documents stuck creation → **`new game`** (D1–D3) | Step 2 subsection + Step 3 command table |
| Quick Start / Features corrected (D5–D6, R-020d–e) | Steps 1 and 4 with before/after substance |
| Partial vs finished save (D4, R-020f) | Step 2 §6 + Step 3 **`load game`** row |
| Wipe warning (R-020c) | Step 2 §5 |
| ≥2 symptoms (R-020b) | Step 2 §2 (four listed) |
| Retry once before wipe (D7) | Step 2 §3 |
| No hand-edit / CLI recovery (R-020g) | Step 2 §7; § G forbidden paths |
| Domain spec updated on close | Close checklist — not impl phase |
| No code drift | Scope table + non-regression; reference-only traces |

## Scope gate

| File | In ticket Expected? | In plan impl? |
|------|---------------------|---------------|
| `app/README.md` | Yes | Yes — Steps 1–4 |
| `tmp/app-session-persistence-spec.md` | Spec sync on close | Close checklist only (correct) |
| `app/gm/orchestrator.py`, `app/ui/app.py`, tests | No | Explicitly excluded |

## Notes (non-blocking)

1. **Step 3 placement:** Plan allows **`### Commands`** under Quick Start *or* under the Stuck subsection. Spec PM preference is dedicated subsection after Quick Start; impl should pick one placement for T-020a grep consistency (heading already pinned in Step 2).
2. **APP-018 nuance:** Plan correctly scopes **`new game`** to **stuck** recovery and includes optional "keep answering if desk resumes" (qa-spec-pass note #1). Avoid prose that mandates wipe after every mid-creation quit.
3. **T-020b is the behavioral gate:** Checklist review (T-020a) alone cannot prove README usability; impl QA must run manual partial-creation → relaunch → **`new game`** per APP-014 TC-1.
4. **Optional pytest:** `-k "setup_new_game or creation_block or session_resume or creation_restore"` is regression smoke only — no README assertion; aligns with spec "no pytest for README prose."

**Verdict:** PASS — plan is implementation-ready; README-only edits match spec D1–D7 and domain R-020a–g; no blockers.
