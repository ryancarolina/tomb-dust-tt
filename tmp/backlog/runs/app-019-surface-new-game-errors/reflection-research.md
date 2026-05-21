# Reflection: Research — APP-019 surface-new-game-errors

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read AGENTS.md, ticket APP-019, domain spec `app-session-persistence-spec.md`, dev-team templates.
- Traced explicit `new game` path: `ui/app.py` → `orchestrator.process_turn` → `setup_new_game` → bridge/engine.
- Identified JSONL gap ( `log_error` only, no `_emit_recovery_narration` ) — parallel to pre-APP-071 load failure.
- Found silent failure callers: `_handle_player_death` and `run_ended` resume branch ignore `setup_new_game` return `ok`.
- Confirmed no toast infrastructure under `app/`; UI `error` channel exists but unused for setup failure.
- Noted Expected files mismatch (orchestrator owns emit; ticket lists ui/main only).
- Set `registry_gap: false` with session-persistence spec + app-master-spec citation.

## Self-critique

- Did not run live PyGame smoke or inject a real `campaign_new` failure — relied on code trace and APP-014/015 test coverage.
- Did not inspect full session JSONL history beyond grep for `setup_new_game` on today's file (zero hits).
- Assumed ticket “silent failures” includes JSONL-only logging and death-path false-success narration, not a hard UI render bug — explicit `new game` failure string does reach `narration_text`.

## Did I miss anything?

- [x] Ticket scope / Expected files — flagged orchestrator gap for PM
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (UI, orchestrator, bridge, engine errors, logging, silent callers)
- [x] Tests / AC mapped — gap vs APP-071 resume failure tests
- [ ] Product decision toast vs narration-only — escalated to PM in risks

## Handoff

**Ready for:** PM spec draft (friendly failure copy, `_emit_recovery_narration` or error-channel routing, caller `ok` guards, Expected files expansion, spec § APP-019 requirements + tests)
**Escalate human if:** Product requires new toast UI component rather than narration/error-channel pattern established by APP-071
