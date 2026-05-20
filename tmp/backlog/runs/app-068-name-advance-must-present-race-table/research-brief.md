# Research Brief: APP-068-name-advance-must-present-race-table

**Date:** 2026-05-20
**Question:** Why does a valid NAME commit sometimes return only “The clerk waits.” with no code race table on the same turn, while `creation_advanced` logs `NAME` → `RACE`?

**backlog_ticket:** APP-068
**ticket_path:** tmp/backlog/app-068-name-advance-must-present-race-table.md
**domain_spec:** tmp/app-character-creation-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) owns `app/gm/creation.py`, the creation branch of `app/gm/orchestrator.py`, and documents NAME→RACE chain behavior (§ Table-shown gating, § Integration test). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** maps to that spec. APP-068 is a bug fix inside the existing owner — no new domain spec.

## Summary

After a valid NAME, the code-first path calls `_execute_creation_choice("NAME", …)` (advances to `RACE`, logs `creation_advanced`), then `_chain_after_creation_choice("")` to append the race table via `_auto_present_race()`. Session log evidence shows intermittent failure: narration is exactly **`The clerk waits.`** with **no** `llm_request` (no `_narrate_flavor`) and **no** `format_races_table()` body — while `creation_step` immediately after records `step: RACE`. That string is **only** produced by the default branch of `_chain_after_creation_choice` (`orchestrator.py` ~867: `return prior or "The clerk waits."`), which runs when `self.creation.step` is **not** one of `RACE`, `ROLL_STATS`, `SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, `EQUIPMENT_GOLD`, or `FINALIZE` at chain time. Success turns always log an `llm_request` right after `creation_advanced` (thin flavor inside `_auto_present_race`). The integration test (`test_full_creation_apprentice_caster`) asserts step transitions but **not** same-turn race table content — so pytest can stay green while manual play fails. Recommended fix: belt-and-suspenders NAME handler that always returns `_auto_present_race()` on success (or hard-fail the chain fallthrough when `race` is empty), plus a regression test on narration after `"Dumpy"` / `"Caddy"`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Turn routing | `app/gm/orchestrator.py` | `_creation_turn_body`, `_handle_creation_response`, `_chain_after_creation_choice` |
| Race table | `app/gm/creation.py` | `format_races_table()`, `races_table_shown`, `CreationState.advance()` resets flag on `RACE` |
| Auto-present | `app/gm/orchestrator.py` | `_auto_present_race()` sets `races_table_shown`, `_narrate_flavor` + compose |
| Commit | `app/gm/orchestrator.py` | `_execute_creation_choice()` → `advance()` + `log_creation_advanced` |
| Legacy LLM loop | `app/gm/orchestrator.py` | `_creation_llm_loop` — **uncalled** on code-first path (dead for NAME) |
| UI thread | `app/ui/app.py` | `_process_turn` in background thread; `turn_lock` around `process_turn` |
| Tests | `app/tests/test_creation_flow.py` | Step FSM only; no NAME→table assertion |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | Caddy @ 16:44:25; Dumpy fail @ 16:45:58 |

## Code-path traces

### Happy path (NAME → RACE, same turn)

1. Entry: `Orchestrator.process_turn(player_input)` → `_creation_turn` when `creation.active` (`orchestrator.py` ~455–456)
2. `_creation_turn_body`: `step == "NAME"` → `_handle_creation_response` (`orchestrator.py` ~585–588)
3. NAME branch: `len(text) >= 2` → `_execute_creation_choice("NAME", text)` (`orchestrator.py` ~712–724)
4. `_execute_creation_choice`: set `creation.name`, `creation.advance()` (NAME→RACE, `races_table_shown=False`), `log_creation_advanced`, return `ok` (`orchestrator.py` ~1193–1286, `creation.py` ~215–220)
5. Return: `_chain_after_creation_choice("")` (`orchestrator.py` ~724)
6. Chain: `if self.creation.step == "RACE":` → `_auto_present_race("[SYSTEM: …]")` → `format_races_table()` + `format_creation_status` footer (`orchestrator.py` ~843–845, ~681–691)
7. Exit: `_emit_narration`, history append (`orchestrator.py` ~647–649)

### Failure path (observed)

1. Steps 1–4 identical — log shows `creation_advanced` `NAME` → `RACE` (`session-2026-05-20.jsonl` ~172–174)
2. Step 5: `_chain_after_creation_choice("")` hits **no** step branch → `return prior or "The clerk waits."` with `prior == ""` (`orchestrator.py` ~867)
3. **No** `llm_request` between `creation_advanced` and `gm_narration` — `_auto_present_race` / `_narrate_flavor` not invoked
4. `creation_step` snapshot still `step: RACE` (`orchestrator.py` `_log_creation_step_snapshot` in `finally`)

### Recovery on next input (Caddy @ RACE)

1. Player repeats `"Caddy"` at `RACE` — `parse_player_race` fails → `_handle_creation_response` returns `None`
2. `_creation_turn_body` uses `_auto_present_race(..., error=…)` or `not races_table_shown` branch — **then** LLM + code table appear (`session` ~176–179; may duplicate LLM table + code table)

## Existing specs & docs

- Ticket: `tmp/backlog/app-068-name-advance-must-present-race-table.md`
- Domain spec: `tmp/app-character-creation-spec.md` — chain after NAME→RACE (APP-057); table-shown gating; tests list `test_creation_flow.py`
- Related: APP-057 (integration test, chain), APP-059 (table catalog), APP-066 (awaiting drift), APP-067 (ROLL_STATS code table)
- APP-057 research noted `_creation_llm_loop` unused on code-first path — NAME uses `_handle_creation_response`, not tools

## Tests & commands

```bash
cd app && python -m pytest app/tests/test_creation_flow.py -q
cd app && python main.py
# Watch: app/logs/session-YYYY-MM-DD.jsonl
# After NAME: expect creation_advanced → llm_request (flavor) → gm_narration contains "| Race |" and "Awaiting: RACE_INPUT"
```

**Proposed regression (for Dev/PM):** After `process_turn("Dumpy")` on fresh `new game`, assert narration contains `Pick **one race**` (or `format_races_table` header) and `Awaiting: RACE_INPUT`; assert narration != `"The clerk waits."`

## Risks & unknowns

- **Root cause at chain entry:** Log proves `advanced_to: RACE` but not which `creation.step` value `_chain_after_creation_choice` read; add temporary `log_entry("chain_after", {"step": self.creation.step})` if repro is elusive.
- **Intermittent:** Same codebase shows pass (pytest mock + many `16:51+` log runs with `llm_request` after NAME) and fail (Caddy 16:44:25, Dumpy 16:45:58) — may be timing, partial deploy, or rare state; not reproduced in static read.
- **Test gap:** `test_full_creation_apprentice_caster` only checks `creation.step` after `"Dumpy"`, not narration content on that turn.
- **Duplicate tables:** Recovery turn may stack LLM-invented race markdown with `format_races_table()` (Caddy log ~179).
- **APP-066 noise:** `creation_drift` on every healthy creation turn does not cause this bug but obscures session triage.
- **UI threading:** `app/ui/app.py` runs `process_turn` on a worker thread; unlikely to explain same-turn FSM log order unless overlapping turns (guarded by `turn_id`).

## Raw notes

### Session log signatures

| Time | Input | After `creation_advanced` | `gm_narration` | `llm_request` before narration? |
|------|-------|---------------------------|----------------|----------------------------------|
| 16:44:25 | Caddy | NAME→RACE | `The clerk waits.` | **No** |
| 16:44:39 | Caddy (repeat) | — | LLM flavor + tables | Yes |
| 16:45:58 | Dumpy | NAME→RACE | `The clerk waits.` | **No** |
| 16:45:58 | human (next) | — | `Test narration.` + race table | Yes (pytest mock) |
| 16:51:08 | Dumpy | NAME→RACE | race table + `Awaiting: RACE_INPUT` | **Yes** |

### Exact fallback source

```841:867:app/gm/orchestrator.py
    def _chain_after_creation_choice(self, prior: str) -> str:
        ...
        if self.creation.step == "RACE":
            extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        ...
        return prior or "The clerk waits."
```

### `advance()` on entering RACE

```215:220:app/gm/creation.py
        if self.step == "RACE":
            self.races_table_shown = False
```

### Related ticket scope

| Ticket | Relevance |
|--------|-----------|
| APP-057 | Introduced NAME→RACE chain; test does not assert table on NAME turn |
| APP-059 | `format_races_table()` exists; failure is presentation not formatter absence |
| APP-066 | Engine `awaiting: CHARACTER_CREATION` vs footer `RACE_INPUT` — orthogonal |
| APP-067 | ROLL_STATS still LLM-heavy; separate from NAME→RACE |
