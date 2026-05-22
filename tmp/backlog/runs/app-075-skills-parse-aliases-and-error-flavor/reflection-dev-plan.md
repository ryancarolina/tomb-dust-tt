# Reflection: Dev plan — APP-075

**Agent:** Dev  
**Round:** 1  
**Deliverables:** [plan.md](./plan.md)

## Completed

- Mapped ticket AC → spec IDs P1–P3, E1–E2, T1–T3 with file-level touch list matching Expected files exactly.
- Traced Supa repro path (parse fail + flavor bug) and success path after P1 (ticket repro → SPELL_SCHOOLS).
- Locked V2 (skip `_narrate_flavor` on `error=`) over correction-only LLM instruction — matches domain spec preference and eliminates monkeypatched stub leakage in T2/T3.
- Specified `_SKILL_COMPACT_MAP` build rule and exact-before-compact ordering per domain spec resolution table.
- Defined `format_skill_parse_error` logic with normative example strings from domain spec; orchestrator call site at SKILLS parse-fail branch only.
- Split WS1 (parser) / WS2 (orchestrator flavor + integration) with T2b dependency on WS1 noted.
- Regression guards for APP-069/070, golden path, and post-validate key-skill error path.

## Self-critique

- **T3 invalid school input:** Plan uses single `pyromancy` — should reliably hit parse-fail → `_auto_present_schools(..., error=...)`. If school table auto-skips for non-caster, apprentice path is safe; impl should confirm `needs_spell_picks` true after T2b skills.
- **`class_key` in `format_skill_parse_error`:** Parameter required by spec but unused in error text today — kept for API stability; impl could use later for class-specific hints without signature change.
- **Helper vs inline `if error: flavor = ""`:** Plan proposes `_creation_table_flavor` DRY helper — minimal abstraction justified by three identical call sites per ticket AC; could inline if reviewer prefers fewer symbols.
- **Line numbers:** Cited from pre-impl tree; may drift ±few lines during impl — symbols are stable anchors.

## Did I miss anything?

- [x] Ticket scope / Expected files — five paths listed; no `test_creation_parsers.py` fork
- [x] Domain spec / registry_gap / AGENTS.md — normative §§ at L84–148 referenced; changelog deferred to close
- [x] Code paths traced — normalize, parse, SKILLS branch, three `_auto_present_*`, compose
- [x] Tests mapped — T1 gating, T2/T2b/T3 flow with APP-070 pattern reference
- [x] Non-goals — spells glued ids, race/class/equipment flavor, return-type change
- [ ] **Status.md checklist** — not updated (orchestrator owns pipeline stage flip after QA plan)

## Handoff

**Ready for:** QA plan review (Stage 4 gate) → implementation WS1 + WS2  
**Escalate human if:** compact map collision appears when adding skills (unlikely on current catalog); or T3 school invalid input does not trigger error re-show on apprentice path
