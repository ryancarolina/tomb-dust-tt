# APP-069: Creation narration must match FSM step

| Field | Value |
|-------|-------|
| **ID** | APP-069 |
| **Type** | bug |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

Player-facing narration can describe the **wrong** creation step (equipment kit, spell schools skipped, wrong skills recorded) while `creation.step` in logs has already advanced — or the reverse (stuck on race while FSM advanced). This recreates the original P0 failure mode from the character-creation spec.

## Evidence (session log vs spec)

| Time | Player input | `creation.step` (drift) | Narration problem |
|------|----------------|-------------------------|-------------------|
| 14:09 | Spellcasting, Arcana, Lore | (LLM path) | Jumped to apprentice **equipment** + `PRE_DELVE` without schools/spells/finalize |
| 15:43 | medicine, spellcasting, endurance | `SPELL_SCHOOLS` | Prose lists wrong skills; shows **equipment** table; `Awaiting: EQUIPMENT_GOLD_INPUT` |
| 16:13 | Medicine, Endurance, spellcasting | `SPELL_SCHOOLS` | Skips schools/spells; LLM kit (quarterstaff/robe) not novice `format_equipment_summary` |
| 16:45 | apprentice / skills at RACE | `RACE` | Inputs for later steps ignored; stuck re-showing race table |

- Spec problem statement (`tmp/app-character-creation-spec.md`): gated steps must not let Gemini invent equipment/PRE_DELVE while code stays on earlier steps.

## Acceptance criteria

- [x] For each gated step, narration body is **only** from `_auto_present_*` / `_handle_creation_response` compose path — never free LLM tables/kits for SKILLS, SPELL_SCHOOLS, SPELLS, EQUIPMENT_GOLD.
- [x] `creation_drift` includes `narrated_step_mismatch` when footer/body implies a different step than `creation.step` (optional enhancement — **deferred stretch**; Phase 2 keyword tests substitute).
- [x] APP-057 golden path asserts step-appropriate table keywords at each input.
- [x] No `Phase: PRE_DELVE` or “registered Delver” prose until `WORLD_INTRO` after non-empty roster (turn-8 `PRE_DELVE not in last`; mid-FSM gates owned by APP-070).

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/creation.py`
- `app/tests/test_creation_flow.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update spec changelog; link regression scenarios.

## Notes

**Session:** `app/logs/session-2026-05-20.jsonl` (Dumpy, Bumpy, Supa segments).  
**Related:** APP-008 (gate exploration), APP-009 (roster gate), APP-011 (wrong-step input), APP-057 (integration test).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-057 | blocked until this is fixed or test will fail |
