# Reflection: Dev — APP-068 WS2

**backlog_ticket:** APP-068  
**workstream:** WS2 — NAME→RACE regression tests  
**date:** 2026-05-20

## What shipped

- **`test_name_advance_presents_race_table(orchestrator)`** — focused regression: `new game` → `Dumpy` asserts `step == RACE`, `races_table_shown is True`, code table intro/header, `Awaiting: RACE_INPUT`, and narration ≠ `"The clerk waits."`.
- **Extended `test_full_creation_apprentice_caster`** — same APP-068 assertions on the `"Dumpy"` turn inside the existing FSM loop (turn 2), preserving APP-057 step checks and APP-067 human-turn roll assertions unchanged.

## Design choices

- **No new fixtures** — reused `orchestrator` + `mock_openrouter_client`; stub flavor `"Test narration."` not asserted (code-owned table strings only).
- **No orchestrator edits** — WS1 already merged; tests validate fixed NAME→RACE behavior only.
- **Dedicated + full-flow coverage** — focused test isolates NAME→RACE AC; full-flow test guards against future FSM regressions on the same turn.

## Verification

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
# ..  [100%]
# 2 passed in 0.67s
```

Focused:

```bash
cd app && python -m pytest tests/test_creation_flow.py::test_name_advance_presents_race_table -q
cd app && python -m pytest tests/test_creation_flow.py::test_full_creation_apprentice_caster -q
```

Both pass as part of full file run.

## Handoff (ticket release — not WS2)

- Update `tmp/app-character-creation-spec.md`: mark APP-068 § NAME→RACE / § Tests AC satisfied; changelog entry.
- `python tmp/backlog/claim_ticket.py release APP-068 --done`

## Risks / notes

- Tests assert code table strings from `format_races_table()` / `format_creation_status()` — if APP-059 changes column layout, update assertions in same ticket.
- Recovery duplicate-table edge at RACE remains non-goal per spec; not covered here.
