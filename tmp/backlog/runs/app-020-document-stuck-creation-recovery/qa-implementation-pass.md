# QA PASS: implementation — round 1

**Task:** APP-020-document-stuck-creation-recovery  
**backlog_ticket:** APP-020  
**ticket_path:** [tmp/backlog/app-020-document-stuck-creation-recovery.md](../../app-020-document-stuck-creation-recovery.md)  
**Round:** 1  
**domain_spec_creation:** synced (`tmp/app-session-persistence-spec.md` § Stuck creation recovery — player documentation (APP-020); checklist + changelog updated)

## Verdict

**PASS** — `app/README.md` satisfies R-020a–g and ticket AC; domain spec sync complete; doc-only scope honored (no `app/` code changes).

## Doc verification (T-020a / R-020a–g)

| ID | Requirement | Evidence (`app/README.md`) | Result |
|----|-------------|----------------------------|--------|
| **R-020a** | Dedicated subsection with **`new game`** recovery | `## Stuck during character creation?` (L17); **Recovery:** **`new game`** (L30) | ✓ |
| **R-020b** | ≥2 stuck symptoms | Four bullets (L23–26): relaunch/`new game` only, repeated/blank/wrong-step, setup error footer, partial **`load game`** failure | ✓ |
| **R-020c** | Plain wipe warning | L30 — wipes in-progress creation + campaign session; **cannot be undone** | ✓ |
| **R-020d** | Quick Start corrected — no boot auto-restore from app autosave | L15 — finished save → **`load game`**; stuck → link to section; grep: no `session_state.json`, no `auto-resumes` | ✓ |
| **R-020e** | Features persistence qualified | L90 — autosave 60s + quit; **finished** saves via **`load game`** at relaunch (not implicit boot restore) | ✓ |
| **R-020f** | **`load game`** for finished saves only | L34–35 partial vs finished; L42 command table “Relaunch with a finished save” | ✓ |
| **R-020g** | No hand-edit / CLI recovery | L46 **Do not:** hand-edit saves / `tomb_gm` / `@tomb-gm` (forbidden only, not instructions) | ✓ |

### Grep checks

| Pattern | `app/README.md` | Result |
|---------|-----------------|--------|
| `auto-resumes` | 0 matches | ✓ |
| `session_state.json` | 0 matches | ✓ |
| `restores on relaunch` (unqualified) | 0 matches | ✓ |
| `Stuck during character creation` | L15, L17 | ✓ |
| `Try once first` | L28 | ✓ |
| `cannot be undone` | L30 | ✓ |

## Ticket AC → deliverable

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| `app/README.md` documents stuck creation → type **`new game`** | Stuck section + command table + Quick Start cross-link | ✓ |
| Domain spec updated on close | Checklist APP-020 `[x]` (L149); § APP-020 (L526–597); changelog 2026-05-22 done entry | ✓ |
| No code drift | `git diff` — only `app/README.md` + `tmp/app-session-persistence-spec.md`; no `app/gm` or `app/ui` edits | ✓ |

## Plan / spec alignment (D1–D7)

| ID | Summary | README | Result |
|----|---------|--------|--------|
| **D1** | Stuck subsection | L17–46 | ✓ |
| **D2** | Symptoms list | L21–26 | ✓ |
| **D3** | Recovery **`new game`** + aliases + wipe | L30, L41 | ✓ |
| **D4** | Partial vs finished contrast | L32–35, L41–42 | ✓ |
| **D5** | Quick Start fix | L15 | ✓ |
| **D6** | Features persistence fix | L90 | ✓ |
| **D7** | Retry once before wipe | L28 | ✓ |

**APP-018 nuance (plan non-blocking):** L19 + L34 — desk may resume after relaunch without mandatory **`new game`** when not stuck. Does not contradict stuck-recovery scope.

## Diff scope reviewed

| File | Change | Authorized? |
|------|--------|-------------|
| `app/README.md` | Quick Start, Stuck section, Features bullet | ✓ ticket Expected files |
| `tmp/app-session-persistence-spec.md` | § APP-020, checklist `[x]`, changelog | ✓ ticket spec-sync on close |

## Deferred (non-blocking)

| Item | Note |
|------|------|
| **T-020b** manual playtest | Not executed this QA round — doc-only; human-test-plan / Stage 7 per pipeline |
| Ticket checkbox + `release APP-020 --done` | Parent orchestrator / Stage 6 — ticket AC still `[ ]` in backlog file |

## Notes

- Domain spec diff also marks APP-014 checklist `[x]` and narrows “Open work” — consistent with closed batch tickets; no behavior drift introduced.
- README retains `play/tomb_gm/` references in Architecture/Requirements as engine import paths — not player recovery instructions (R-020g satisfied).
