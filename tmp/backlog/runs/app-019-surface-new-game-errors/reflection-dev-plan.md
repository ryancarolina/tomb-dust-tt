# Reflection: Dev — APP-019 plan

**Agent:** Dev  
**Round:** 1  
**Deliverables:** plan.md, reflection-dev-plan.md

## Completed

- Read ticket Expected files, research-brief, run spec (PM r2 R1a/R1b), qa-spec-pass round 2, domain § New game failure + § Emit ownership.
- Traced current failure/silent-success paths: command ~535–539, `_handle_player_death` ~424–432, `run_ended` ~558–564, combat callers ~1586 and ~1680.
- Planned reuse of existing `_emit_recovery_narration` (no drift) vs forbidden `_emit_narration` on failure.
- Specified `_map_setup_new_game_cause`, `_setup_new_game_failure_message`, and `PlayerDeathResult` with `already_emitted` for context B (SPEC-001 resolution).
- Mapped contexts A/B/C emit ownership: inline in `process_turn` (A, C); in-handler emit + caller skip (B).
- Scoped combat caller edits to two sites; preserved `None` early exits from `_handle_player_death`.
- Mapped T-019a–f to monkeypatch patterns from `test_session_resume_failure.py` and `conftest.py` orchestrator fixture.
- Deferred R6 optional UI to post-manual-smoke; ticket closes orchestrator-only by default.

## Self-critique

- Did not run pytest in plan phase — impl agent must green T-019a–f and regression filters before `release --done`.
- `PlayerDeathResult` dataclass chosen over tuple for readability; impl may use tuple if module already has similar patterns — contract (`already_emitted`) matters more than type name.
- T-019c caller simulation is explicit in plan but not a shared test helper in repo yet — impl should add minimal `_simulate_combat_death_emit` if duplication across asserts is awkward.
- R4 run_ended failure message builder needs careful lead-line assembly so R3 corpse line is not duplicated — impl should unit-test `{where}` preservation in T-019d only, not re-assert full prose twice.

## Did I miss anything?

- [x] Ticket scope / Expected files (orchestrator, optional ui, tests)
- [x] `_emit_recovery_narration` vs `_emit_narration` / drift (R1, T-019e)
- [x] Context B emit ownership / double JSONL (SPEC-001 / R1b)
- [x] Contexts A and C inline emit (R1a)
- [x] R5 cause mapping table aligned with domain spec
- [x] Success regression R7 / T-019f
- [x] APP-014 / APP-015 / APP-071 non-goals
- [x] QA note: preserve `None` vs result at combat call sites

## Handoff

**Ready for:** QA plan PASS → impl (helpers + three contexts + combat callers + tests + domain close)  
**Escalate human if:** Manual smoke shows weak visibility after command failure despite R2 copy — then minimal R6 `_set_turn_idle` in `app/ui/app.py` (update ticket Expected files before edit).
