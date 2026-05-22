# Reflection: PM — APP-027

**Date:** 2026-05-22  
**Stage:** PM spec draft  
**backlog_ticket:** APP-027

## What went well

- Research brief was complete: engine already validates, bridge catch documented, APP-028 overlap clearly separated from validation AC.
- **registry_gap: false** — combat spec already owned bridge + orchestrator + problem line; no master-spec registry change.
- APP-026 pattern (orchestrator/bridge pre-gate + domain spec § + run `spec.md`) ported cleanly to monster validation.

## Decisions

1. **Layered validation:** `tool_args` for empty/missing list + shared `validate_monster_specs` at bridge top + engine as defense-in-depth — avoids relying on exceptions alone while keeping one format/parser source in `combat.py`.
2. **Empty `monster_specs` in scope:** Explicit fail; research flagged ambiguity — PM chose non-empty required to prevent zero-monster combat starts from LLM tools.
3. **Error substring stability:** Spec requires `monster JSON not found: {id}` to protect APP-028 T1–T3 mocks and live beat short-circuit tests.
4. **Narration AC delegated to APP-028:** APP-027 AC "no fiction" mapped to R5 reference, not re-specifying `all_failed` strip — reduces duplicate spec drift.
5. **Mixed-tool + beat regex + CLI:** Documented non-goals to keep Dev scope within Expected files.

## Risks flagged for QA / Dev

- **V4 happy path** may need session fixture — acceptable deferral to APP-030 if heavy.
- Implementing R1 only in `app/` without importing engine helpers risks duplicate `MONSTER_SPEC_RE` — spec says prefer engine module.
- `tools.py` example `hollow-knight` is optional R6 but strongly recommended to reduce LLM training on bad ids.

## QA spec pass expectations

- Verify V3/V5 distinguish tool_args vs bridge errors (stable strings in tests).
- Confirm ticket AC does not require mixed-tool narration fix.
- Check APP-028 regression called out in V8.

## Handoff

- **Run spec:** `tmp/backlog/runs/app-027-validate-monster-id-combat/spec.md`
- **Domain spec:** `tmp/app-combat-play-spec.md` § Monster id validation at combat start (APP-027)
- **Next:** QA spec adversarial pass → Dev plan → impl
