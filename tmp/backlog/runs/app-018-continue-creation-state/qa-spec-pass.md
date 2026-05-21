# QA PASS: spec

**Task:** APP-018-continue-creation-state  
**backlog_ticket:** APP-018  
**ticket_path:** tmp/backlog/app-018-continue-restores-creation-state.md  
**Round:** 2  
**domain_spec_creation:** not_needed (registry_gap false; § Creation restore on continue / relaunch (APP-018) in existing domain spec)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` — § Creation restore G1–G3, Tests T-018a–f, merge order, changelog r2)
- [x] Acceptance criteria testable (R1–R7 + T-018a–f; resume fail/success + relaunch first-turn paths)
- [x] Code traces match repo (`orchestrator.py` `process_turn` ~542–579, `_is_mid_creation_resume_failure`, NAME clobber ~573–576; `import_creation_state` exists)
- [x] AGENTS.md / canon compliance (orchestrator-only hydration; no `ui/app.py`; APP-064 boot unchanged)
- [x] Tests/commands listed (T-018a–f; pytest modules in ticket Expected files; run spec § Test plan commands)
- [x] Plan files ⊆ ticket Expected files — N/A (spec stage)
- [x] registry_gap matches reality (`false` — Session persistence row owns APP-018 read path per APP-016 Consumers)
- [x] If registry_gap true: N/A

## Round 1 blocker resolution

| Finding | Round 2 status | Evidence |
|---------|----------------|----------|
| **SPEC-001** — relaunch live-only vs G1 saved precedence | **RESOLVED** | Run `spec.md` PM decisions § Relaunch (G1, not live-only); **R2**; domain **G3a** + **T-018b** (live `SETUP` + saved `CHARACTER_CREATION`) |
| **TICKET-001** — test paths missing from Expected files | **RESOLVED** | Ticket Expected files: `app/tests/test_session_resume_failure.py`, `app/tests/test_creation_restore.py`; run `spec.md` § Affected paths matches |

## Ticket AC coverage

| Ticket AC | Spec / domain mapping |
|-----------|------------------------|
| When `awaiting == CHARACTER_CREATION`, restore creation from save | **G1** gate (saved `awaiting` precedence when snapshot present; else live); **G2** `import_creation_state`; **G3a–c** call sites; **R1–R7** |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-018 `in_progress`; domain spec = Session persistence |
| registry_gap | **PASS** | false; domain § APP-018 exists with G1–G3, T-018a–f |
| Round 1 blockers | **PASS** | Single normative **G1** for relaunch + resume; test modules authorized |
| Merge order vs APP-017 | **PASS** | Run spec + domain § R3 / Merge order: **018 restore → 017 force-active → sync** |
| `import_creation_state` / NAME clobber | **PASS** | G2 forbids post-import NAME reset; R4 removes ~573–576; T-018f APP-015 regression |
| Relaunch scope | **PASS** | First `process_turn` (non–`new game`) when G1 passes; boot chips APP-064 unchanged |
| Resume fail/success ordering | **PASS** | R3 before `_resume_failure_message`; R4 before `_sync_creation_from_status` + CHARACTER_CREATION branch |
| Stale snapshot rule | **PASS** | Saved `awaiting != CHARACTER_CREATION` → no restore even if live matches; R5 legacy fallback when no snapshot |
| Code traces | **PASS** | Research-brief paths align; bug lines and variant B gap confirmed |
| Scope / Expected files | **PASS** | orchestrator + listed test modules + domain spec on close |

## Notes (non-blocking — Dev plan)

- **G3a once-only:** Domain and run spec say *first* `process_turn` after relaunch — Dev plan should specify a session flag or equivalent so repeated turns do not re-import stale disk over in-memory progress.
- **Domain pytest path:** Domain § Tests APP-018 uses `cd app && python -m pytest app/tests …` — from `app/` cwd the target should be `tests/` (run spec § Test plan has correct paths). Fix on ticket close if desired.
- **APP-017 run spec:** May still carry stale merge-order wording; domain + APP-018 run spec are canonical for batch impl.

**Verdict:** PASS — ready for Stage 3 (Dev plan + QA plan).
