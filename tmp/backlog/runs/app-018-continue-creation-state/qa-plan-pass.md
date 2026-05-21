# QA PASS: plan

**Task:** APP-018-continue-creation-state  
**backlog_ticket:** APP-018  
**ticket_path:** [tmp/backlog/app-018-continue-restores-creation-state.md](../../app-018-continue-restores-creation-state.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; domain § Creation restore on continue / relaunch (APP-018))

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-session-persistence-spec.md`
- [x] Ticket domain spec matches plan (G1–G3, T-018a–f, APP-017 merge order align with domain § Creation restore and run `spec.md`)
- [x] Acceptance criteria testable — ticket AC maps to helper + G3a–c call sites + T-018a–f table
- [x] Code traces match repo — spot-checked live `app/gm/orchestrator.py`:
  - `process_turn` resume branch ~542–579 (fail path no restore today; success NAME clobber ~573–576)
  - `_restore_history` ~123–137 (creation import + hardcoded `session_state.json` path)
  - `_session_state_path` ~313–314, `import_creation_state` ~198–200
  - `_is_mid_creation_resume_failure` / `_resume_failure_message` ~331–375 (variant B uses in-memory `creation.step`)
  - `_sync_creation_from_status` ~177–191 (post-restore sync; `WORLD_INTRO` → `NAME` only allowed downgrade)
- [x] AGENTS.md / canon compliance — orchestrator-only hydration; no `ui/app.py`; APP-064 boot unchanged
- [x] Tests/commands listed — T-018a–f in new `test_creation_restore.py`; regression pytest block; `_session_state_path` monkeypatch pattern matches `test_creation_block_on_new_game.py`
- [x] Plan files ⊆ ticket Expected files — strict match (see table below)
- [x] QA spec round 2 non-blocking note resolved — `_creation_disk_restore_done` once-only guard documented (W1.1, § Once-only relaunch guard)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — helper, gate, G3a–c, flag, trim `_restore_history` | Yes |
| `app/tests/test_creation_restore.py` (new) — T-018a–f | Yes |
| `app/tests/test_session_resume_failure.py` — optional variant B comment/tweak | Yes |
| `tmp/app-session-persistence-spec.md` — changelog on close (WS3) | Yes (on close) |

**Out of scope (explicit):** `app/ui/app.py`, APP-064 boot, `find_save_campaign` — matches ticket + run spec.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 shared restore helper + G1 gate | § G1 gate, § Restore helper | T-018a–f gate matrix |
| R2 relaunch first turn (G3a) | § Call sites G3a; saved `awaiting` precedence | **T-018b** (`SETUP` live + saved `CHARACTER_CREATION`) |
| R3 resume fail before variant B | § G3b | **T-018a** |
| R4 resume success; remove NAME clobber | § G3c; delete ~573–576 | **T-018c** |
| R5 legacy no `engine_status` | G1a else branch | **T-018d** |
| R6 post-finalize no-op | G1a stale rule + G1d | **T-018e** |
| APP-015 post–`new game` | G1 + gate after wipe | **T-018f** |
| Ticket AC: restore when `CHARACTER_CREATION` | G1–G3 + `import_creation_state` | T-018a–d |
| APP-071 variant A/B non-regression | § Regression pytest block | existing `test_session_resume_failure.py` |
| APP-017 batch merge | § Merge with APP-017 | 018 restore first; 017 consumes helper; 018 tests pass without 017 |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-018 `in_progress`; Session persistence domain |
| Plan ⊆ Expected files | **PASS** | No scope creep beyond ticket |
| Spec G1–G3 / R1–R7 in plan | **PASS** | Matches run `spec.md` + domain § APP-018 |
| Code traces | **PASS** | Line refs and bug paths confirmed in live orchestrator |
| Test plan vs `qa-spec-pass` | **PASS** | T-018a–f cases + pytest commands aligned |
| QA spec r2 once-only guard | **PASS** | `_creation_disk_restore_done` + reset on `setup_new_game` |
| NAME clobber removal | **PASS** | Explicit delete target ~573–576; forbidden post-import NAME |
| APP-017 independence | **PASS** | Helper ships in 018; minimal G3c force-active labeled placeholder |
| Stale snapshot / APP-015 | **PASS** | G1a saved `awaiting` precedence + T-018f |

## Notes (non-blocking — implementation QA)

1. **`_restore_history` path:** Still hardcodes `Path(__file__).parents[1] / "session_state.json"` (~126) while helper uses `_session_state_path()`. Tests patch the method only — consider refactoring `_restore_history` to call `_session_state_path()` in WS1 so history + creation reads share isolation (not required for T-018a–f if G3a/G3b hydrate first).
2. **`process_turn` control flow:** G3a pseudocode requires splitting the current `if new game / elif continue` chain into sequential `if` blocks — plan implies but does not spell out; impl must avoid `elif` after standalone G3a `if`.
3. **Once-only flag timing:** Flag sets only on **successful** restore; if G1 fails turn 1 then player advances in-memory, a later passing G1 could re-read disk (Dev self-critique — acceptable per spec). Impl QA may add first-attempt guard if playtest shows clobber.
4. **T-018b LLM path:** Plan correctly flags spy/light assertion; `conftest` `mock_openrouter_client` should suffice for full `_creation_turn` if needed.
5. **G3c inline force-active:** APP-017 placeholder — when 017 lands, replace with `_reconcile_empty_roster_on_load()` per merge order; 018-only ship should not duplicate 017 reconcile logic beyond minimal `active=True` fallback.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
