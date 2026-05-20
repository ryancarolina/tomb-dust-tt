# Spec: APP-068-name-advance-must-present-race-table

**Status:** qa-review  
**backlog_ticket:** APP-068  
**ticket_path:** tmp/backlog/app-068-name-advance-must-present-race-table.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**registry_gap:** false  
**Domain specs touched:** tmp/app-character-creation-spec.md

## Problem

After a valid NAME (`len >= 2`), `creation_advanced` logs `NAME` → `RACE` but the same turn sometimes narrates only **"The clerk waits."** with no code race table and no `llm_request` (no `_auto_present_race` / `_narrate_flavor`). Session evidence: `app/logs/session-2026-05-20.jsonl` (Caddy @ 16:44:25, Dumpy @ 16:45:58). That string is the default fallthrough of `_chain_after_creation_choice` when no step branch matches at chain time.

`test_full_creation_apprentice_caster` asserts `creation.step == RACE` after `"Dumpy"` but not same-turn narration — pytest can stay green while manual play fails.

## Goals

- Guarantee same-turn race table presentation after every successful NAME commit.
- Eliminate bare `"The clerk waits."` when at `RACE` with race unset.
- Add regression test on narration content for the NAME turn.

## Non-goals

- APP-059 column/catalog redesign for `format_races_table()`.
- APP-066 engine `awaiting` vs footer label drift.
- Removing duplicate LLM+code race tables on recovery re-prompt (follow-up if needed).
- New domain spec file (`registry_gap: false`).

## Requirements

**Authoritative behavior:** [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) § NAME→RACE same-turn presentation (APP-068), § Tests (APP-068).

### R1: Same-turn code race table after NAME

**Acceptance criteria**

- [ ] After valid NAME in `_handle_creation_response`, the **same** `process_turn` return includes `_auto_present_race()` composition: thin flavor (optional) + `format_races_table()` body + `format_creation_status()` footer.
- [ ] Body includes intro `Pick **one race**` and table header `| Race | Adjustments | Description |`.
- [ ] Footer includes `Awaiting: RACE_INPUT`.
- [ ] `races_table_shown` is `True` before narration is emitted.

### R2: No bare clerk-waits at RACE

**Acceptance criteria**

- [ ] When `creation.step == "RACE"` and race is unset, narration MUST NOT be exactly `"The clerk waits."` (or prior-empty equivalent from `_chain_after_creation_choice` default).
- [ ] `_chain_after_creation_choice` after NAME MUST hit the `RACE` branch or an equivalent direct `_auto_present_race()` return — not the `return prior or "The clerk waits."` fallthrough.

**Dev hint (research):** Belt-and-suspenders — NAME success may `return self._auto_present_race(...)` directly after `_execute_creation_choice` instead of relying only on chain step matching; optional `log_entry("chain_after", {"step": ...})` if repro is elusive.

### R3: Regression test

**Acceptance criteria**

- [ ] `app/tests/test_creation_flow.py`: after `new game` + name input (`"Dumpy"` or dedicated test), assert narration contains race table header and `Awaiting: RACE_INPUT`; assert narration != `"The clerk waits."`.
- [ ] Existing full-flow test may gain assertions on turn 2 or a focused `test_name_advance_presents_race_table`.

## Test plan

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

**Session log (manual):** After NAME, expect `creation_advanced` → `llm_request` (flavor) → `gm_narration` with `| Race |` and `Awaiting: RACE_INPUT`.

## Human playtest hints (Stage 7)

- New game → enter name (e.g. Caddy) → same response shows full race markdown table, not one-line clerk wait.
- Repeat invalid name at NAME, then valid name — table still appears on advance turn.

## Affected paths

- `app/gm/orchestrator.py` — `_handle_creation_response` (NAME), `_chain_after_creation_choice`, `_auto_present_race`
- `app/tests/test_creation_flow.py`
- `tmp/app-character-creation-spec.md` (this ticket; changelog on close)

## References

- [research-brief.md](./research-brief.md)
- [ticket](../../app-068-name-advance-must-present-race-table.md)
- Related: APP-057 (chain introduced), APP-059 (`format_races_table`)
