# Reflection: Research — APP-014 setup_new_game session lifecycle

**Agent:** Research
**Round:** 1
**Deliverables:** `research-brief.md`, `reflection-research.md`; `status.md` research checklist (orchestrator updates research stage when synced)

## Completed

- Read AGENTS.md, ticket APP-014, domain spec `app-session-persistence-spec.md`, dev-team templates, batch board APP-014/015/016.
- Traced `setup_new_game`, `process_turn("new game")`, bridge session/campaign methods, engine `session.py` / `campaign.py`, UI autosave and `clear_narration`.
- Confirmed `registry_gap: false` against app-master-spec Session persistence row.
- Documented AC gap (missing `end_session` before wipe), failure partial-return path, corpse table exclusion, and test gaps.

## Self-critique

- Did not reproduce a live `play/workspace` failure in PyGame — analysis is static; historical error strings in the spec may be from older engine builds.
- Did not read JSONL logs in `app/logs/` for a concrete failing session ID — grep found no matching error literals in current Python.
- “main flow” in ticket Expected files is ambiguous (`main.py` vs UI turn path); brief assumes orchestrator + `ui/app.py` unless PM narrows.

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py`, main/turn flow)
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (new game, death, resume run_ended, bridge/engine)
- [x] Tests / AC mapped (spec tests + proposed T-014a–c)
- [ ] Live log sample proving current failure mode — not available in repo artifacts reviewed

## Handoff

**Ready for:** PM spec draft (`spec.md`) — define ordered lifecycle R1, `end_session`/`force_close` fallback, failure-path creation/save reset, changelog for `app-session-persistence-spec.md`; optional `app-gamebridge-spec.md` bridge note.
**Escalate human if:** Product requires preserving `session.ended` JSONL events on every new game (needs explicit `log_event` in bridge/orchestrator, not only wipe).
