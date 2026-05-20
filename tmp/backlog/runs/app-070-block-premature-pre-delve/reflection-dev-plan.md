# Reflection: Dev plan — APP-070

**backlog_ticket:** APP-070  
**artifact:** [plan.md](./plan.md)  
**round:** 1

## What the plan covers

- **Root cause:** Thin-LLM flavor invents completion copy while FSM/roster stay on desk steps; APP-009 only gates code finalize.
- **Fix layers:** Compose sanitizer (player-facing) before drift telemetry; no changes to `_auto_finalize` roster gate.
- **Traces delivered:** `_compose_creation_narration` (520–537 + call-site table), `_check_creation_drift` (180–234 + D1a–c), new `sanitize_premature_completion_flavor` in `creation.py`, T1 test aligned to `INPUTS` turn 5 / index 4.

## Decisions locked in plan

| Decision | Rationale |
|----------|-----------|
| Sanitizer in `creation.py`, wire in orchestrator | Matches domain spec § Compose; keeps regex testable; mirrors APP-069/072 helper pattern |
| Blank flavor on any C3 hit | Simplest leak-proof behavior; clerk body+footer still render |
| Sanitizer on flavor only, not `footer=` | C2 — legitimate `WORLD_INTRO` at 1054–1055 must survive |
| `_narrate_flavor` monkeypatch for T1 | Narrower than swapping global mock; targets SKILLS→schools chain turn |
| D2 `premature_completion_copy` optional | QA-spec: compose strip may make drift redundant on T1 |

## Risks called out for implementation

- **`RECEPTION_CHOICE` in T1 assert:** Safe because post-SKILLS code footer is `SPELL_SCHOOLS_INPUT` only — any `RECEPTION_CHOICE` in composed string implies leak or unsanitized flavor.
- **`preparation` vs `PRE_DELVE`:** Drift D1c keys off `creation.active` + `step != WORLD_INTRO`; post-finalize path excluded.
- **APP-073 overlap:** Bracket tags already stripped at 529; plan still strips unbracketed markers and prose per C3.

## QA-spec notes addressed

- D1 rows gated with `roster_len == 0` explicitly in plan (QA note on section intro).
- Line refs verified against current tree (within ~20 lines of qa-spec-pass cites).
- Turn index: domain “turn 5” = fifth `process_turn` = skills input → `SPELL_SCHOOLS`.

## Out of scope (confirmed)

- APP-069 flavor/race alignment, APP-072 table dedup, APP-073 stronger tag strip, `_creation_llm_loop`, engine `test_creation_gating.py` changes.

## Ready for

Stage 4 implementation: claim/focus APP-070, implement §1–3 in plan, run pytest commands, then spec changelog + `release --done`.
