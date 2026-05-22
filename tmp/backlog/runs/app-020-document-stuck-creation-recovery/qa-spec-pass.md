# QA PASS: spec

**Task:** APP-020-document-stuck-creation-recovery
**backlog_ticket:** APP-020
**ticket_path:** tmp/backlog/app-020-document-stuck-creation-recovery.md
**Round:** 1
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` § Stuck creation recovery — player documentation (APP-020))
- [x] Acceptance criteria testable (ticket AC → R-020a–g checklist + T-020a–b manual cross-check)
- [x] Code traces match repo (`app/README.md` L15/L59 stale copy; `orchestrator.py` `setup_new_game` / `_reset_creation_for_new_game` / `_clear_creation_block_on_disk`; `ui/app.py` `_init_orchestrator` APP-064 `has_save()` branch)
- [x] AGENTS.md / canon compliance (PyGame canonical play; no hand-edit / `tomb_gm` CLI recovery; doc-only chore)
- [x] Tests/commands listed (R-020 checklist review; optional manual APP-014 TC-1 cross-check; no pytest required)
- [x] registry_gap false — Session persistence row in `app-master-spec.md`; no new domain spec required

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 chore; `in_progress`; domain spec linked |
| registry_gap | **PASS** | `false` — behavior contract belongs in existing session-persistence spec |
| domain_spec_creation | **PASS** | `not_needed` |
| AC testability | **PASS** | Single ticket AC maps to D1–D3 / R-020a–c; D5–D7 are README correctness extensions within Expected file |
| Drift policy | **PASS** | Spec explicitly doc-only; README must match APP-014/015/064/071/019 behavior — no implied code change |
| Domain spec sync | **PASS** | Run `spec.md` D1–D7 ↔ domain § APP-020 R-020a–g aligned; task checklist + changelog entry present |
| Expected files | **PASS** | Impl scope `app/README.md` only; domain spec update is ticket-mandated spec sync (not impl scope creep) |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| `app/README.md` documents stuck creation → type **`new game`** | D1–D3; R-020a–c; § Recovery command | T-020a checklist grep; T-020b manual | **PASS** |
| Domain spec updated on close | § APP-020 + task checklist `[ ]` + changelog 2026-05-22 | Checklist close on impl | **PASS** (draft contract ready) |
| No code drift | Non-goals + § Non-regression | Dev plan gate | **PASS** |

## Notes (non-blocking — Dev / plan stage)

1. **APP-018 nuance:** Domain § Partial vs finished save and D5 Quick Start wording frame partial creation around boot **`new game`** prompt and **`new game`** reset. APP-018 G3a can restore mid-creation FSM on first non–`new game` `process_turn` after relaunch when not stuck. Dev should avoid README prose that tells players they *must* wipe with **`new game`** after every mid-creation quit — scope here is **stuck** recovery; optional one-line “if the desk resumes normally, keep playing” is acceptable but not required by R-020.
2. **Heading string:** PM left subsection title flexible (“Stuck during character creation?” or equivalent). Dev plan may pin one heading for T-020a review consistency.
3. **`tmp/app-master-spec.md`:** No priority-table change needed — doc-only ticket; PM omission correct per ticket spec-sync note.

**Verdict:** **PASS** — ready for Dev plan.
