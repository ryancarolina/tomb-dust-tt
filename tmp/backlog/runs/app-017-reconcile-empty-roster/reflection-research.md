# Reflection: Research — APP-017 reconcile empty roster

**Agent:** Research
**Round:** 1
**Deliverables:** `research-brief.md`, `reflection-research.md`

## Completed

- Read AGENTS.md, ticket APP-017, domain spec `app-session-persistence-spec.md`, dev-team templates.
- Traced load paths: `_load_session`, `_restore_history`, `process_turn` resume branch, `_sync_creation_from_status`.
- Confirmed APP-016 write-only `engine_status` — no read path in repo yet.
- Mapped engine status fields (`roster` vs `characters`, `awaiting` rules in `handle_status`).
- Identified symptom link to empty suggestion chips (`test_inactive_creation_ignores_step`).
- Documented APP-017/018 batch boundary and Expected-files constraint.
- Proposed test IDs T-017a–e and pytest commands.

## Self-critique

- Did not run pytest or manual PyGame repro — conclusions are static analysis only; T-017 cases are proposed, not executed.
- Boot-time reconcile (fresh orchestrator with active DB session, no load command) is noted as out-of-scope but could still confuse players; may need a follow-up ticket if PM expands scope.
- `ROSTER_SETUP` with empty roster but orphan `characters` rows was not traced with a concrete fixture — flagged as risk, not verified in DB.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths not traced — covered load, resume, sync, save producer
- [x] Tests or AC not mapped — proposed T-017 table; no existing tests
- [ ] `play/tomb_gm/domain/session.py` `find_save_campaign` — referenced via spec, not re-read for this brief (low risk; APP-064 already documented)

## Handoff

**Ready for:** PM spec draft (define reconcile algorithm, live-vs-saved precedence, APP-018 boundary, optional Expected-files expansion if UI must call new API)

**Escalate human if:** Product wants boot-time auto-reconcile without an explicit load command — not in current ticket AC.
