# Reflection: QA — APP-019 spec

**Agent:** QA
**Round:** 1
**Deliverables:** qa-spec-report-1.md, reflection-qa-spec.md

## Completed

- Read ticket APP-019, run `spec.md`, `research-brief.md`, domain § New game failure (APP-019), PM reflection.
- Verified code at `orchestrator.py:535–539` (command failure), `424` (death ignore ok), `558–564` (run_ended ignore ok), `_emit_recovery_narration:309–311`, combat death callers `1586–1591` / `1680–1684`.
- Cross-checked APP-071 test style (`test_session_resume_failure.py`) and ticket Expected files vs Affected paths.
- Issued **FAIL** with 1 blocker (death-path emit contract), 1 major, 1 minor.

## Self-critique

- Did not trace every possible `setup_new_game` engine error string from bridge/campaign.py — R5 default bucket likely sufficient; mapping completeness is impl-time.
- T-019c feasibility assumed direct `_handle_player_death` mock is acceptable; did not confirm with existing conftest combat fixtures (none found).
- Run_ended context C emit is clearer in spec than death; may have under-weighted whether C needs explicit “branch before `_emit_narration(death_msg)`” — inline in `process_turn` is probably obvious to Dev.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator + tests aligned; main.py correctly out
- [x] Domain spec / registry_gap — false; § APP-019 present
- [x] Code paths not traced — command, death, run_ended, UI clear_narration
- [x] Tests or AC not mapped — gap on B/C JSONL asserts noted
- [ ] `app-logging-qa-spec.md` cross-link for setup_new_game recovery — non-blocking (APP-071 same note)

## Handoff

**Ready for:** PM spec revision (round 2) addressing SPEC-001
**Escalate human if:** PM insists death callers cannot change — would need architectural decision (new return type vs internal emit-only)
