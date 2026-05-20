# QA PASS: spec

**Task:** APP-071-friendly-load-no-save
**backlog_ticket:** APP-071
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md
**Round:** 2
**domain_spec_creation:** not_needed (registry_gap false)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md`)
- [x] Acceptance criteria testable (R0–R5, T1–T3 / domain T3a–T3c, manual TC-A/B/C)
- [x] Code traces match repo (`orchestrator.py` 444–448 failure branch; `_emit_narration` 286–288 → drift; `ui/app.py` 300 narration queue, 342–350 chip parse)
- [x] AGENTS.md / canon compliance (app-only; no canon drift)
- [x] Tests/commands listed; `app/tests/test_session_resume_failure.py` in ticket Expected files
- [x] registry_gap false — session-persistence spec owns behavior
- [x] Round 1 blockers resolved (see below)

## Round 1 resolution

| Finding | Round 1 | Round 2 status |
|---------|---------|----------------|
| **SPEC-001** — `_emit_narration` + recovery footers cause spurious `creation_drift` | Blocker | **Resolved** — R1 mandates `_emit_recovery_narration` (`log_gm_narration` only, no `_check_creation_drift`); R2 allows `[Awaiting: new game]` when drift scope false; R3 requires `[{format_creation_status(creation)}]` bracket token; human phrases prose-only |
| **SPEC-002** — overlapping R2/R3 predicates | Major | **Resolved** — R0 ordered decision tree (variant B signals first); mirrored in domain § Resume failure |
| **TICKET-001** — APP-019 toast bundled ambiguity | Major | **Resolved** — ticket AC item 4 + scope notes; spec R4 scope split table |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 bug; `in_progress`; domain spec linked |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | All four ticket AC map to R1–R4 + tests |
| Drift / logging alignment | **PASS** | Recovery emit + footer rules align with `app-logging-qa-spec.md` § `creation_drift` healthy path |
| Code traces | **PASS** | Failure path, emit helper contract, UI chip extraction verified |
| Domain spec sync | **PASS** | Run `spec.md` ↔ domain § Resume failure table consistent |
| Expected files | **PASS** | Test file added per round 1 WARN |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Player-facing narration; not silent | R1, R2, R3 | T1/T2, TC-A/B | **PASS** |
| JSONL `error` retained; player-visible log | R1 recovery emit + `log_gm_narration` | T3 | **PASS** |
| Distinguish no save vs mid-creation | R0, R2 vs R3 | T1 vs T2 | **PASS** |
| APP-019 / toast scope | R4; ticket AC item 4 | N/A for APP-071 close | **PASS** |

## Notes (non-blocking)

- Ticket AC still mentions optional `log_player_message`; spec non-goals correctly redirect to `log_gm_narration` via recovery emit — Dev should not add a new logger symbol.
- R0 signal #2 (`SAVE_PATH` / exported creation state) is the fuzziest branch predicate; T2 covers the primary mid-creation path (`new game` → name → `load game`).
- Optional follow-up (not APP-071 gate): explicit “recovery narration exempt from drift” bullet in `tmp/app-logging-qa-spec.md` if Dev wants cross-spec discoverability.

**Verdict:** **PASS** — ready for Dev plan.
