# QA PASS: spec

**Task:** APP-064-startup-save-prompt
**backlog_ticket:** APP-064
**ticket_path:** tmp/backlog/app-064-startup-save-prompt-only-when-resumable.md
**Round:** 1
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` § Startup save-detection (APP-064))
- [x] Acceptance criteria testable (S1–S4, T1a–T1c; optional T2)
- [x] Code traces match repo (`app/ui/app.py` L128–131 override; `session.py` `has_save_session` / `find_save_campaign`)
- [x] AGENTS.md / canon compliance (app session persistence only; no canon mechanics)
- [x] Tests/commands listed (`pytest` session + app; manual Supa/regression in domain spec)
- [x] registry_gap false — Session persistence row in `app-master-spec.md`; no new domain spec required

**Notes:**

- All five ticket ACs mapped in `spec.md` AC table and domain spec § APP-064.
- `registry_gap: false` confirmed: behavior rule belongs in existing session-persistence spec; UI change scoped to `app/ui/app.py` per Expected files.
- APP-071 § in domain spec is pre-planned sibling work; correctly out of APP-064 non-goals.
- Optional headless T2 not elevated — ticket marks `app/tests/` optional.
