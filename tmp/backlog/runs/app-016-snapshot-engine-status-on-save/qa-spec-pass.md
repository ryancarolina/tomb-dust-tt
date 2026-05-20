# QA PASS: spec

**Task:** APP-016-snapshot-engine-status-on-save
**backlog_ticket:** APP-016
**ticket_path:** tmp/backlog/app-016-snapshot-engine-status-on-save.md
**Round:** 2
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md`)
- [x] Acceptance criteria testable
- [x] Code traces match repo (`_save_session()` in `app/ui/app.py` already calls `get_status()` for `session_id` / `campaign_slug`; S5c single-call optimization is accurate)
- [x] AGENTS.md / canon compliance (app persistence only; no `build/` changes)
- [x] Tests/commands listed (T4a–d, pytest `-k "engine_status or save_session"`)
- [x] registry_gap matches reality (`false`; Session persistence row in `tmp/app-master-spec.md`)

## Round 1 findings — remediation verified

| ID | Round 1 issue | Round 2 status |
|----|---------------|----------------|
| **SPEC-001** | Missing domain § APP-016 / persist bullet | **Fixed** — `## Engine status snapshot on save (APP-016)` with S1, S5a–e, batch table, AC; top persist bullet includes `engine_status`; changelog aligned |
| **SPEC-002** | APP-015 vs APP-016 `engine_status` on new game | **Fixed** — option A: APP-015 C2 removes `engine_status` on every `setup_new_game` entry; APP-016 write-only; mirrored in run `spec.md` R3, domain C4, batch tables, **T-015d** |
| **SPEC-003** | Missing consumer note for APP-017/018 | **Fixed** — domain § Consumers; forward Notes on APP-017 and APP-018 tickets |
| **TICKET-001** | Invalid Expected files | **Fixed** — `app/ui/app.py`, `app/tests/`, `tmp/app-session-persistence-spec.md`; orchestrator scoped to APP-015 batch note |

## Cross-checks (re-review focus)

- [x] Domain § APP-016 matches run `spec.md` R1–R3 (snapshot, triggers, batch coordination)
- [x] S5d canonical shape: omit `engine_status` on save failure; absent key and `null` both mean no snapshot
- [x] Run `spec.md` Expected files ⊆ ticket Expected files (real repo paths)
- [x] APP-014 L7 whole-file delete + APP-015 C2 surgical clear + APP-016 `_save_session` write — consistent in both domain sections

## Notes (non-blocking)

- **APP-015 run artifacts:** `runs/app-015-*/spec.md` still indexes C2 as “surgical `creation_state`” without naming `engine_status`; domain C2 is authoritative and now explicit. APP-015 `plan.md` may still say “preserve `engine_status`” — Dev plan QA on APP-015 should reconcile before impl; does not block APP-016 spec PASS.
- **APP-015 qa-spec-pass (round 1)** note that C2 preserves `engine_status` is superseded by domain PM r2 — batch board should treat domain as source of truth.
- **Implement order:** APP-015 C2/T-015d should land with or before APP-016 save snapshot to avoid stale `engine_status` on failure-path new game (per PM r2 handoff).
