# Workstreams: APP-067-code-owned-roll-stats-table

**backlog_ticket:** APP-067

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Roll-stats table formatter | — | `app/gm/creation.py` | `format_roll_stats_table` matches domain spec R1; optional unit call returns expected markdown |
| WS2 | Roll orchestration + tests | WS1 | `app/gm/orchestrator.py`, `app/tests/test_creation_flow.py` | Thin-flavor `_auto_roll_stats`, chain dedup, `FIXED_ROLL` + APP-067 assertions; `pytest tests/test_creation_flow.py -q` green |

**Stream count:** 2 — WS1 is a pure formatter with no orchestrator coupling; WS2 imports it and owns end-to-end narration + regression tests (plan tasks 2–4).

**Out of workstreams (ticket release):** `tmp/app-character-creation-spec.md` changelog + `claim_ticket.py release APP-067 --done` (plan task 5).

---

## WS1 — Roll-stats table formatter

**Scope:** Plan §1 — add `format_roll_stats_table(roll_result)` in `creation.py` after `format_races_table` / before `format_classes_table` (~L556).

**Requirements covered:** spec R1 (ticket AC: code-owned attribute table from payload only).

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | Signature + placement | `def format_roll_stats_table(roll_result: dict) -> str` beside other `format_*_table` helpers | §1 |
| 2 | Life event intro | `Life event: {life_event.get("name", "Unknown")}` | §1 step 1 |
| 3 | Markdown table | Header `Attr \| Base \| Genetic \| Life Evt \| Racial \| Final` + alignment row; STR–SPI rows from payload fields only | §1 steps 2–3 |
| 4 | Final column | Use `final_attributes[attr]` — **do not** recompute sum | §1 step 3, spec R1 |
| 5 | LUC row | `—` for Base/Genetic/Life Evt/Racial; Final from `final_attributes["LUC"]` | §1 step 4 |
| 6 | HP line | `sta = final_attributes["STA"]`, `hp = 10 + sta * 5`; `**HP:** {hp} (10 + STA {sta} × 5)` | §1 step 5 |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Payload-only | No `bridge`, no random, no `eligible_classes`, no class table in formatter |
| Missing keys | `.get` defaults consistent with `GameBridge.roll_attributes` shape |
| Genetic column | `genetic_factors[attr]["mod"]` (dict with `roll` + `mod`) |
| Style | Mirror `format_classes_table` markdown conventions (pipes, alignment row) |
| Out of scope | `orchestrator.py`, tests (WS2), domain spec edit |

### Test gates (WS1 done when)

```bash
# Optional — if unit test added in WS1 (plan allows; not required for ticket AC)
cd app && python -m pytest tests/test_creation_tables.py::test_format_roll_stats_table_returns_expected_markdown -q
# OR manual: python -c "from gm.creation import format_roll_stats_table; ..." with FIXED_ROLL-shaped dict
```

**Minimum WS1 close:** formatter callable with production-shaped `roll_result` dict; output contains life event line, table header, LUC row, HP line per domain spec.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-067
ticket: tmp/backlog/app-067-code-owned-roll-stats-table.md
run-folder: tmp/backlog/runs/app-067-code-owned-roll-stats-table/
spec: spec.md | plan: plan.md §1 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only — format_roll_stats_table in app/gm/creation.py per plan §1 and domain spec § format_roll_stats_table.
AGENTS.md: claim APP-067 before app/ edits; stay within Expected files; no orchestrator or test edits.
Optional: test_format_roll_stats_table in test_creation_flow.py or new test_creation_tables.py — not required to close WS1.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Roll orchestration + tests

**Scope:** Plan §2–4 — refactor `_auto_roll_stats`, dedupe `_chain_after_creation_choice` ROLL_STATS branch, update `FIXED_ROLL` and integration assertions in `test_creation_flow.py`.

**Depends on:** WS1 — `_auto_roll_stats` imports `format_roll_stats_table`.

**Requirements covered:** spec R2–R4 (ticket AC: thin flavor, HP, single class table, test cells match fixture).

### Implementation order (within stream)

| # | Task | File | Plan ref |
|---|------|------|----------|
| 1 | Import `format_roll_stats_table` | `orchestrator.py` ~L16–26 | §2 |
| 2 | Refactor `_auto_roll_stats` | `orchestrator.py` ~L924–956 | §2 |
| 3 | Chain dedup | `orchestrator.py` ~L846–851 | §3 |
| 4 | Update `FIXED_ROLL` production shape | `test_creation_flow.py` ~L5–21 | §4.1 |
| 5 | APP-067 assertions after `"human"` turn | `test_creation_flow.py` | §4.2 |

### `_auto_roll_stats` body (plan §2)

| Step | Action |
|------|--------|
| Keep | `bridge.roll_attributes`, `log_tool_call`, `creation.roll_result = result`, `creation.advance()`, `_remember_creation_step("ROLL_STATS")` |
| Add | `eligible = result.get("eligible_classes", ["peasant"])` |
| Flavor | `_narrate_flavor(_creation_flavor_messages("Present attribute roll results briefly — the Registry clerk reads the dice.", player_input))` — no stat numbers |
| Body | `format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)` |
| Flag | `self.creation.classes_table_shown = True` **after** `advance()` |
| Return | `_compose_creation_narration(flavor, body)` |
| Delete | `context` JSON, custom `messages`, `return _narrate_only(messages)` |

**Reference pattern:** `_auto_present_skills` (~L869–880).

### Chain dedup (plan §3)

```python
# After (APP-067): ROLL_STATS branch returns _auto_roll_stats only — no _auto_present_class append
if self.creation.step == "ROLL_STATS":
    return self._auto_roll_stats("[SYSTEM: Step auto-advanced. Continue.]")
```

**Leave unchanged:** `_auto_present_class` (Flow C: direct CLASS entry when `not classes_table_shown`).

### Test assertions after `"human"` (plan §4.2)

| Assert | Expected |
|--------|----------|
| `creation.step` | `"CLASS"` |
| `creation.classes_table_shown` | `True` |
| Table header | `"Attr \| Base \| Genetic \| Life Evt \| Racial \| Final" in last` |
| Life event | `"Life event: Unremarkable Youth" in last` |
| Finals | Each `FIXED_ROLL["final_attributes"]` attr appears in row with Final cell |
| LUC | `\| LUC \|` and final `10` in `last` |
| HP | `"**HP:** 60"` and `"(10 + STA 10 × 5)"` or tolerant STA+60 |
| Class once | `last.count("Pick **one tier-1 class**") == 1` |
| No duplicate | `"**Final attributes:**" not in last` |
| Flavor | `"Test narration." in last` |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Flag order | Set `classes_table_shown` after `advance()` to CLASS (advance resets flag on CLASS entry — set after) |
| No LLM table | `_auto_roll_stats` must not call `_narrate_only` |
| Flow C preserved | `_auto_present_class` unchanged for resume / invalid CLASS |
| `FIXED_ROLL` | Remove LUC from `base_rolls`; `genetic_factors[attr] = {"roll": 2, "mod": 0}` per attr STR–SPI |
| Out of scope | `bridge.py`, `system_prompt.py`, `get_step_prompt`, mandatory new `test_creation_tables.py` |

### Test gates (WS2 done when all pass)

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

**Manual verification (plan § Tests):**

- Grep: `_auto_roll_stats` has no `_narrate_only` call
- Grep: `_chain_after_creation_choice` ROLL_STATS branch has no `_auto_present_class`

### Post-impl (not WS2 — ticket release)

- Verify domain spec § `format_roll_stats_table` / ROLL_STATS orchestration matches code (draft already in spec)
- `tmp/app-character-creation-spec.md` changelog: `| 2026-05-20 | APP-067 done: code-owned ROLL_STATS table; chain dedup; test assertions |`
- `python tmp/backlog/claim_ticket.py release APP-067 --done`

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-067
ticket: tmp/backlog/app-067-code-owned-roll-stats-table.md
run-folder: tmp/backlog/runs/app-067-code-owned-roll-stats-table/
spec: spec.md | plan: plan.md §2–4 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS2

Prerequisite: WS1 present — format_roll_stats_table in creation.py.
Implement WS2 only — orchestrator _auto_roll_stats + chain dedup + test_creation_flow.py per plan §2–4.
AGENTS.md: claim APP-067 if not active; no bridge/system_prompt edits.
Run: cd app && python -m pytest tests/test_creation_flow.py -q
Manual greps per plan § Tests (no _narrate_only in _auto_roll_stats; no _auto_present_class in ROLL_STATS chain).
Write reflection-dev-impl-WS2.md before return.
```
