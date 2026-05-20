# Workstreams: APP-068-name-advance-must-present-race-table

**backlog_ticket:** APP-068

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | NAME→RACE orchestrator fix | — | `app/gm/orchestrator.py` | NAME success returns `_auto_present_race` directly; chain RACE fallthrough guard before clerk-waits default; manual grep confirms no bare fallthrough at RACE with empty race |
| WS2 | NAME→RACE regression tests | WS1 | `app/tests/test_creation_flow.py` | `test_name_advance_presents_race_table` + extended `test_full_creation_apprentice_caster` turn-2 assertions; `pytest tests/test_creation_flow.py -q` green |

**Stream count:** 2 — WS1 is the belt-and-suspenders orchestrator fix (plan tasks 1–2, single file); WS2 depends on WS1 behavior and owns pytest AC (plan task 3).

**Out of workstreams (ticket release):** `tmp/app-character-creation-spec.md` changelog + AC checkboxes + `claim_ticket.py release APP-068 --done` (plan task 4).

---

## WS1 — NAME→RACE orchestrator fix

**Scope:** Plan §1–2 — `_handle_creation_response` NAME success path and `_chain_after_creation_choice` RACE fallthrough guard.

**Requirements covered:** spec R1 (same-turn `_auto_present_race` body + footer), R2 (no bare `"The clerk waits."` at RACE with race unset).

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | Direct `_auto_present_race` on NAME success | `_handle_creation_response` NAME branch ~721–724 | §1 |
| 2 | Chain fallthrough guard | `_chain_after_creation_choice`, before `return prior or "The clerk waits."` ~867 | §2 |

### Task 1 — NAME handler (plan §1)

**Before:**

```python
return self._chain_after_creation_choice("")
```

**After:**

```python
return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")
```

**Leave unchanged on NAME branch:** `_execute_creation_choice` failure → `_auto_present_name(..., error=...)`; short name / bracket prefix → `return None`; equipment confirm → `_auto_present_name` error.

**Rationale:** Removes `_chain_after_creation_choice("")` as single point of failure when chain entry does not match `step == "RACE"` at call time (~867 fallthrough).

### Task 2 — Chain fallthrough guard (plan §2)

**Insert immediately before** `return prior or "The clerk waits."` (~867):

```python
if self.creation.step == "RACE" and not self.creation.race:
    extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
    return f"{prior}\n\n{extra}".strip() if prior else extra
return prior or "The clerk waits."
```

**Keep** existing `if self.creation.step == "RACE":` block (~843–845) for non-NAME chain callers. Guard catches any path that reaches fallthrough while still at `RACE` with empty `race` (SPELL skip edges, resume, future callers).

**Optional debug:** `log_entry("chain_after", ...)` — **omit** unless PM/QA asks after fix.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| `_auto_present_race` unchanged | ~681–691: sets `races_table_shown = True`; flavor + `format_races_table()` + `_compose_creation_narration` → `Awaiting: RACE_INPUT` |
| `advance()` flag order | `_execute_creation_choice` NAME sets `races_table_shown = False` on entering RACE (`creation.py` ~219–220); `_auto_present_race` must set `True` before return |
| Invalid NAME | No race table until valid NAME — do not change re-prompt paths |
| Recovery at RACE | Repeat name at RACE → duplicate LLM+code tables possible — **non-goal** (spec) |
| Out of scope | `creation.py`, tests (WS2), domain spec edit |

### Test gates (WS1 done when)

```bash
# Smoke — full file may fail until WS2; optional focused manual after WS1:
cd app && python main.py
# new game → name "Caddy" → same response must include | Race | and Awaiting: RACE_INPUT
```

**Minimum WS1 close:** Both edits in `orchestrator.py`; grep confirms NAME success branch does not call `_chain_after_creation_choice("")`; fallthrough guard present before clerk-waits default.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-068
ticket: tmp/backlog/app-068-name-advance-must-present-race-table.md
run-folder: tmp/backlog/runs/app-068-name-advance-must-present-race-table/
spec: spec.md | plan: plan.md §1–2 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only — orchestrator NAME→RACE fix per plan §1–2 (direct _auto_present_race + chain RACE fallthrough guard).
AGENTS.md: claim APP-068 before app/ edits; stay within Expected files; no test edits.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — NAME→RACE regression tests

**Scope:** Plan §3 — `test_name_advance_presents_race_table` + extend `test_full_creation_apprentice_caster` turn-2 assertions.

**Depends on:** WS1 — tests assert fixed NAME→RACE narration behavior.

**Requirements covered:** spec R3 (ticket AC: integration test name → table + `RACE_INPUT`).

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | New focused test | `test_name_advance_presents_race_table(orchestrator)` | §3a |
| 2 | Extend full-flow test | When `text == "Dumpy"`, assert table + footer + flag | §3b |

### `test_name_advance_presents_race_table` (plan §3a)

| # | Action |
|---|--------|
| 1 | `orchestrator.process_turn("new game")` — assert `creation.step == "NAME"` |
| 2 | `narration = orchestrator.process_turn("Dumpy")` |
| 3 | Assert `creation.step == "RACE"` |
| 4 | Assert `creation.races_table_shown is True` |
| 5 | Assert `"Pick **one race**" in narration` |
| 6 | Assert `"| Race | Adjustments | Description |" in narration` |
| 7 | Assert `"Awaiting: RACE_INPUT" in narration` |
| 8 | Assert `narration.strip() != "The clerk waits."` |

Uses existing `orchestrator` + `mock_openrouter_client` fixtures (stub flavor `"Test narration."` prepended — assertions target **code** table strings and footer).

### Extend `test_full_creation_apprentice_caster` (plan §3b)

Inside input loop, when `text == "Dumpy"`:

```python
assert "Pick **one race**" in last
assert "| Race | Adjustments | Description |" in last
assert "Awaiting: RACE_INPUT" in last
assert last.strip() != "The clerk waits."
assert orchestrator.creation.races_table_shown is True
```

Keeps APP-057 step FSM checks; APP-068 narration AC on the same turn.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| No new fixtures | No `monkeypatch` on roll until `"human"` turn |
| Stub flavor | `mock_openrouter_client` returns `"Test narration."` — do not assert flavor text |
| Out of scope | `orchestrator.py` (WS1), `creation.py`, bridge/system_prompt |

### Test gates (WS2 done when all pass)

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

Focused:

```bash
cd app && python -m pytest tests/test_creation_flow.py::test_name_advance_presents_race_table -q
cd app && python -m pytest tests/test_creation_flow.py::test_full_creation_apprentice_caster -q
```

### Post-impl (not WS2 — ticket release)

- `tmp/app-character-creation-spec.md`: mark APP-068 § NAME→RACE / § Tests items satisfied; changelog: `APP-068 done: NAME success returns _auto_present_race directly; chain RACE fallthrough guard; test_name_advance_presents_race_table`
- `python tmp/backlog/claim_ticket.py release APP-068 --done`

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-068
ticket: tmp/backlog/app-068-name-advance-must-present-race-table.md
run-folder: tmp/backlog/runs/app-068-name-advance-must-present-race-table/
spec: spec.md | plan: plan.md §3 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS2

Prerequisite: WS1 present — orchestrator NAME→RACE fix merged.
Implement WS2 only — test_creation_flow.py per plan §3a–3b.
AGENTS.md: claim APP-068 if not active; no orchestrator edits unless WS1 incomplete.
Run: cd app && python -m pytest tests/test_creation_flow.py -q
Write reflection-dev-impl-WS2.md before return.
```
