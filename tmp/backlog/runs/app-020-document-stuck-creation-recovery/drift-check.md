# Drift Check: APP-020-document-stuck-creation-recovery

**backlog_ticket:** APP-020  
**domain_spec:** [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md)  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Stuck creation recovery — player documentation (APP-020) | no | R-020a–g checklist matches `app/README.md`; task checklist `[x]` APP-020; changelog **APP-020 done** row present |
| Run [`spec.md`](spec.md) D1–D7, T-020a–b | no | README satisfies D1–D7; T-020a pass; T-020b manual deferred Stage 7 |
| [`tmp/backlog/app-020-document-stuck-creation-recovery.md`](../../app-020-document-stuck-creation-recovery.md) | no | AC checked below; **Status** → `done`; **Closed** 2026-05-22 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Session persistence row unchanged; doc-only ticket — no priority-table update required |

## README ↔ domain spec (R-020a–g)

| ID | Requirement | README evidence | Result |
|----|-------------|-----------------|--------|
| **R-020a** | Dedicated stuck subsection + **`new game`** recovery | `## Stuck during character creation?` (L17); **Recovery:** **`new game`** (L30) | **PASS** |
| **R-020b** | ≥2 stuck symptoms | Four bullets (L23–26) | **PASS** |
| **R-020c** | Plain wipe warning | L30 — in-progress creation + campaign session; **cannot be undone** | **PASS** |
| **R-020d** | Quick Start — no boot auto-restore from app autosave alone | L15 — finished save → **`load game`**; stuck link; no `session_state.json` / `auto-resumes` | **PASS** |
| **R-020e** | Features persistence qualified | L90 — autosave 60s + quit; **finished** saves via **`load game`** at relaunch | **PASS** |
| **R-020f** | **`load game`** for finished saves only | L34–35, L42 command table | **PASS** |
| **R-020g** | No hand-edit / CLI recovery instructions | L46 **Do not:** only (forbidden paths) | **PASS** |

### Negative grep (`app/README.md`)

| Pattern | Matches | Result |
|---------|---------|--------|
| `auto-resumes` | 0 | **PASS** |
| `session_state.json` | 0 | **PASS** |
| `Could not start game` (verbatim legacy error) | 0 | **PASS** |

## README ↔ code (behavior source — no APP-020 code changes)

| README claim | Code / spec source | Match |
|--------------|-------------------|-------|
| **`new game`** / **`start`** / **`new`** reset | `orchestrator.py` L824–831 `process_turn` → `setup_new_game()` | yes |
| **`load game`** / **`continue`** / **`load`** / **`resume`** for finished saves | `orchestrator.py` L836+ `session_resume()`; `ui/app.py` L281–282 | yes |
| Partial creation boot → **`new game`** chip only | `ui/app.py` L128–146 — `has_save = bridge.has_save()`; false branch suggestions `["new game"]` (APP-064 S3) | yes |
| Finished save boot → **`load game`** chip | `ui/app.py` L137–141 (APP-064 S2) | yes |
| **`new game`** → NAME desk, wipes in-progress creation + session | `setup_new_game()` L665–683 — `_reset_creation_for_new_game`, `_clear_creation_block_on_disk`, wipe, `CreationState(step="NAME")`, `_delete_save_file()` on success (APP-014/015) | yes |
| Partial **`load game`** fails — steer to **`new game`** | `_resume_failure_message` / variant A+B (APP-071) | yes |
| Setup failure → retry **`new game`** | `_setup_new_game_failure_message` (APP-019) | yes |
| Desk may resume after relaunch when not stuck (APP-018) | L19, L34 — `_restore_creation_from_session_state()` G3a on first non–`new game` turn | yes |
| No code drift in `app/gm` or `app/ui` | `git diff` — only `app/README.md` + domain spec | yes |

## Ticket AC ↔ deliverable

| Acceptance criterion | Result |
|----------------------|--------|
| `app/README.md` documents stuck creation → type **`new game`** | **PASS** — Stuck section, command table, Quick Start cross-link |

## Tests ↔ domain spec § Tests APP-020

| Spec ID | Case | Result |
|---------|------|--------|
| **T-020a** | Checklist review R-020a–g | **PASS** (this drift check) |
| **T-020b** | Manual partial creation → relaunch → README-only recovery | **DEFERRED** Stage 7 / `human-test-plan.md` |

No pytest required per ticket scope.

## Diff scope (authorized)

| File | Change | Authorized? |
|------|--------|---------------|
| `app/README.md` | Quick Start, Stuck section, Features bullet | yes — ticket Expected files |
| `tmp/app-session-persistence-spec.md` | § APP-020, checklist, changelog, open-work line | yes — ticket spec-sync on close |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria satisfied (see table above)
- [x] Domain spec § APP-020 + checklist + changelog aligned with `app/README.md`
- [x] README prose aligned with APP-014/015/064/071/019 behavior (no doc↔code drift)
- [x] Ticket **Status** → `done` / **Closed** 2026-05-22 (backlog file updated in drift round)
- [ ] `python tmp/backlog/claim_ticket.py release APP-020 --done` — orchestrator (clears session + backlog README row)

## Ancillary notes (non-blocking)

1. **T-020b manual playtest** not executed in drift round — doc-only ticket; Stage 7 human plan covers APP-014 TC-1 cross-check.
2. **Domain spec header** **Status: In progress** reflects broader session-persistence domain, not APP-020 regression.
3. **APP-018 nuance** in README (desk may resume without mandatory wipe) matches live restore gate — not contradictory to stuck-recovery scope.
4. **`play/tomb_gm/`** references in Architecture/Requirements are engine import paths, not player recovery instructions (R-020g satisfied).
