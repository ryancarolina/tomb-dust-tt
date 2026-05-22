# Reflection: Research — APP-075 skills-parse-error-flavor

**Agent:** Research  
**Round:** 1  
**Deliverables:** `research-brief.md`, `reflection-research.md`

## Completed

- Read ticket APP-075, domain spec `app-character-creation-spec.md`, and dev-team research template.
- Traced `SKILL_PARSE_ALIASES`, `normalize_skill_slug`, `parse_player_skills` in `app/gm/creation.py`.
- Traced SKILLS error path: `_handle_creation_response` → `_auto_present_skills(..., error=)` → `_narrate_flavor` / `_compose_creation_narration` in `app/gm/orchestrator.py`.
- Confirmed repro locally: `manacontrol` → `None`; spaced `mana control` parses; all 9 hyphenated skills fail glued form; compact keys are collision-free.
- Mapped existing tests (`test_creation_gating.py`, `test_creation_flow.py`) and gaps vs ticket AC.
- Checked schools/spells normalizers for stretch scope; spell glued ids fail, schools OK (single-word).
- Set `registry_gap: false` with master-spec / domain-spec justification.

## Self-critique

- Did not inspect gitignored session JSONL for Supa turn — relied on ticket + live parser repro; line-level log quotes would strengthen evidence.
- Error-flavor failure mode is inferred from code structure and ticket symptom (“Smart choices…”) rather than a captured LLM response in this workspace.
- Did not trace `set_creation_choice` tool path for SKILLS failures — live desk path is code-first via `_handle_creation_response`; tool path is secondary during creation.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths not traced — `_creation_turn_body` fallthrough error strings also call `_auto_present_skills` with error
- [x] Tests or AC mapped
- [ ] `_auto_present_race` / `_auto_present_class` same error-flavor pattern — noted as out of scope unless PM expands
- [ ] Whether PM wants parser changes duplicated in engine vs app-only (single `gm.creation` module serves both via PYTHONPATH)

## Handoff

**Ready for:** PM spec draft — two workstreams (parser + error-flavor) can be parallelized; shared `_auto_present_*` error-flavor helper optional third stream.  
**Escalate human if:** Product wants glued-token parsing for spell ids (`embertouch`) in same ticket — currently stretch only.
