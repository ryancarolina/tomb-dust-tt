# QA PASS: spec

**Task:** APP-014-setupnewgame-session-lifecycle  
**backlog_ticket:** APP-014  
**ticket_path:** tmp/backlog/app-014-setupnewgame-session-lifecycle.md  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; behavior in existing `tmp/app-session-persistence-spec.md`)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`app-session-persistence-spec.md`)
- [x] Acceptance criteria testable
- [x] Code traces match repo (`setup_new_game` ~348–361 wipe-first; `bridge.end_session` / `force_close_all_sessions` / `wipe_all_data` present; callers at ~383, ~495–500, resume `run_ended` ~518)
- [x] AGENTS.md / canon compliance (app session lifecycle only; no mechanics drift)
- [x] Tests/commands listed (T-014a–c; pytest `-k` filters in domain spec)
- [x] registry_gap matches reality (false — session-persistence spec + `app-master-spec.md` registry row)
- [x] Batch boundaries APP-015/016 documented; no APP-015 failure-path or APP-016 `engine_status` scope creep in APP-014 requirements

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; `in_progress`; domain spec link correct |
| registry_gap | **PASS** | false per research-brief + PM spec; no new domain file |
| Drift policy | **PASS** | Authoritative § setup_new_game lifecycle (APP-014) in domain spec; run `spec.md` is index + pointers |
| AC coverage | **PASS** | Ticket AC maps to L1/L1b → L2 → L4 → L5; L3 `init()` documented as existing step between wipe and campaign |
| Batch boundaries | **PASS** | APP-014 owns engine end-before-wipe; APP-015 owns C1–C3 disk/memory clear before L1; APP-016 save snapshot independent; merge note in domain § Batch |
| Testability | **PASS** | T-014a–c + manual APP-064 follow-on; historical log strings explicitly non-assertable |
| Code traces | **PASS** | Research line refs match current `orchestrator.py` / `bridge.py` / `session.end_session` return shapes |

## Acceptance criteria mapping

| Ticket AC | Spec / domain coverage | Testable |
|-----------|------------------------|----------|
| `setup_new_game()`: session end → wipe_all_data → campaign new → session start | Domain § Required order L1/L1b, L2, L4, L5; run spec L1–L2 | T-014a, T-014b |
| Domain spec updated | § setup_new_game lifecycle (APP-014), changelog 2026-05-20 | Reviewed |
| Stuck partial creation → `new game` → clean NAME (manual) | L6 on success + human playtest hints; failure-path disk stale deferred to APP-015 | T-014a + manual |

## Notes (non-blocking)

- **Ticket Expected files:** `app/main flow` is not a repo path (interpreted as orchestrator + UI turn pipeline). Before pytest impl, add concrete paths — at minimum `app/gm/orchestrator.py` and `app/tests/` (or named test module) — per APP-066/071 precedent.
- **L1b in orchestrator:** `bridge.end_session()` only auto-invokes `force_close_all_sessions` on **exception**; spec requires orchestrator to call `force_close_all_sessions()` when L1 returns `not ok` (e.g. `no active session`, `session already ended`) — Dev plan must encode this explicitly.
- **Human playtest “no stale step in footer”:** On **successful** `setup_new_game`, L6 sets `creation.step == NAME`. Stale footer after **failed** setup remains APP-015 / APP-019 scope (domain § Failure path).
- **Tests:** No `setup_new_game` / T-014 tests in repo yet — expected pre-impl; add under ticket Expected files before Dev edits tests.
- **Run `spec.md` status:** Still `draft (PM round 1)` — orchestrator may advance to `qa-review` / checklist when recording gate.
- **Changelog:** APP-014 behavior draft in domain spec; dated **done** changelog on ticket close per Spec sync (not a spec-gate blocker).

**Verdict:** PASS — ready for Stage 3 (Dev plan + QA plan round 1).
