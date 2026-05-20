# Reflection: Research — APP-064 startup-save-prompt

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md, reflection-research.md

## Completed

- Read AGENTS.md, ticket APP-064, domain spec `app-session-persistence-spec.md`, and dev-team research template.
- Traced startup path: `main.py` → `App._init_orchestrator` → `has_save` override vs `bridge.has_save()`.
- Traced load path: `_process_turn` → `orchestrator.process_turn` → `session_resume` → `find_save_campaign`.
- Confirmed engine eligibility in `play/tomb_gm/domain/session.py` and status derivation in `cmd_core.handle_status`.
- Mapped related tickets APP-017, APP-018, APP-071 and documented regression cases (post-finalize / in-delve).
- Set `registry_gap: false` with master-spec registry citation.

## Self-critique

- Did not run manual PyGame repro or pytest with a live Supa workspace DB; conclusions are from static trace and ticket evidence. A dev with `play/workspace/` in CHARACTER_CREATION state should confirm before close.
- Did not fully enumerate every `awaiting` value that the override treats as "saved" (ROSTER_SETUP, COMBAT_TURN, etc.); brief notes ROSTER_SETUP but deeper matrix could help PM spec edge-case section.
- Assumed finalize always sets roster slot before PLAYER_ACTIONS; relied on orchestrator finalize path grep, not a full creation FSM read.

## Did I miss anything?

- [x] Ticket scope / Expected files — focused on `app/ui/app.py` + session-persistence spec; optional tests noted.
- [x] Domain spec / registry_gap / AGENTS.md — session persistence owns behavior; no new spec file.
- [x] Code paths not traced — `_load_session` timing and no boot-time auto-restore documented.
- [x] Tests or AC not mapped — manual + optional mock test described per AC.
- [ ] Live workspace state — not inspected (`play/workspace/` may contain active Supa session; static analysis only).

## Handoff

**Ready for:** PM spec draft (run-local `spec.md`) — problem/goals already clear; PM should add explicit startup rule bullet to session-persistence spec and human playtest cases for empty-roster vs post-finalize.  
**Escalate human if:** Product wants mid-creation continue without engine roster (would expand scope beyond APP-064 into APP-018/017 design).
