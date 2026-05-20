# Implementation Plan: APP-067-code-owned-roll-stats-table

**Status:** draft  
**backlog_ticket:** APP-067  
**ticket_path:** tmp/backlog/app-067-code-owned-roll-stats-table.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Close the last LLM-owned creation table gap: move ROLL_STATS attribute breakdown from `_narrate_only()` JSON instructions to `format_roll_stats_table(roll_result)` in `creation.py`, then refactor `_auto_roll_stats()` to the APP-006 thin-flavor pattern (`_narrate_flavor` + code body + `_compose_creation_narration`). Embed `format_classes_table(eligible)` in the roll response, set `classes_table_shown`, and remove the duplicate `_auto_present_class` append in `_chain_after_creation_choice` (APP-057 added that chain; APP-067 reverses the class half).

Roll logic stays in `GameBridge.roll_attributes`; tests use an updated `FIXED_ROLL` shaped like production output.

---

## Code-path traces (current → planned)

### Flow A: Race pick → roll + class (canonical chain)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `orchestrator.py:_handle_creation_response` RACE | `_execute_creation_choice("RACE", …)` | unchanged |
| 2 | `creation.py:CreationState.advance` | step → `ROLL_STATS` | unchanged |
| 3 | `orchestrator.py:_chain_after_creation_choice` | `ROLL_STATS` → `_auto_roll_stats` + if `CLASS` → `_auto_present_class` | **`_auto_roll_stats` only** — return single narration |
| 4 | `orchestrator.py:_auto_roll_stats` | `roll_attributes` → store → advance → `_narrate_only` with table JSON | roll → store → advance → `_narrate_flavor` → `format_roll_stats_table` + `format_classes_table` → `_compose_creation_narration`; **`classes_table_shown = True`** |
| 5 | `creation.py:format_roll_stats_table` | _(missing)_ | new formatter from payload only |
| 6 | `orchestrator.py:_compose_creation_narration` | not used on roll path | flavor + body + `format_creation_status` → `Awaiting: CLASS_INPUT` (step already `CLASS`) |

### Flow B: Direct `ROLL_STATS` step (`_creation_turn_body`)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `orchestrator.py:_creation_turn_body` ~579–580 | `step == "ROLL_STATS"` → `_auto_roll_stats` | same entry |
| 2 | `_auto_roll_stats` | LLM table | same refactored body as Flow A (stats + class tables, flag set) |

No chain caller — class table still included inside `_auto_roll_stats` per domain spec.

### Flow C: Direct `CLASS` without roll (resume / invalid / system)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `_creation_turn_body` ~597–598 | `CLASS` + `not classes_table_shown` → `_auto_present_class` | **unchanged** — one-liner `**Final attributes:**` + `format_classes_table` only |
| 2 | `_execute_creation_choice` CLASS ~1211–1213 | requires `classes_table_shown` | satisfied by Flow A flag before player sees class table |

### Flow D: Regression guard — no duplicate class table

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `_chain_after_creation_choice` ~846–850 | concatenates roll + `_auto_present_class` | **delete** `class_part` branch; `return roll_part` when step was `ROLL_STATS` |
| 2 | Test after `"human"` | no table assertions | assert `Pick **one tier-1 class**` appears **once**; `**Final attributes:**` must **not** appear in same narration (chain dedup signal) |

---

## Task breakdown

### 1. `format_roll_stats_table(roll_result)` — `app/gm/creation.py`

**Placement:** after `format_races_table` / before `format_classes_table` (~L556), matching other `format_*_table` helpers.

**Signature:** `def format_roll_stats_table(roll_result: dict) -> str`

**Algorithm (per domain spec § `format_roll_stats_table`, R1):**

1. Read `life_event = roll_result.get("life_event", {})`; intro line: `Life event: {life_event.get("name", "Unknown")}`.
2. Blank line; header row: `| Attr | Base | Genetic | Life Evt | Racial | Final |` with alignment row `|:------|-----:|--------:|---------:|-------:|------:|` (mirror `format_classes_table` style).
3. For `attr in ("STR", "AGI", "STA", "INT", "SPI")`:
   - Base = `roll_result["base_rolls"][attr]`
   - Genetic = `roll_result["genetic_factors"][attr]["mod"]` (assume dict shape from bridge)
   - Life Evt = `life_event.get("mods", {}).get(attr, 0)`
   - Racial = `roll_result.get("racial_adjustments", {}).get(attr, 0)`
   - Final = `roll_result["final_attributes"][attr]` — **do not** recompute sum
4. LUC row: `| LUC | — | — | — | — | {final_attributes["LUC"]} |` (em dash or ASCII `—` consistently).
5. Blank line; HP: `sta = final_attributes["STA"]`, `hp = 10 + sta * 5`; line `**HP:** {hp} (10 + STA {sta} × 5)`.
6. Return `"\n".join(lines)`.

**Non-goals in formatter:** no `eligible_classes`, no class table (orchestrator appends).

**Edge cases:** missing keys → use `.get` defaults consistent with bridge; formatter must not call `bridge` or random.

---

### 2. Refactor `_auto_roll_stats` — `app/gm/orchestrator.py`

**Import:** add `format_roll_stats_table` to `from gm.creation import (...)` block (~L16–26).

**Replace body** (~L924–956):

| # | Action |
|---|--------|
| 1 | Keep: `result = bridge.roll_attributes(...)`, `log_tool_call`, `creation.roll_result = result`, `creation.advance()`, `_remember_creation_step("ROLL_STATS")` |
| 2 | `eligible = result.get("eligible_classes", ["peasant"])` |
| 3 | `flavor = _narrate_flavor(_creation_flavor_messages("Present attribute roll results briefly — the Registry clerk reads the dice.", player_input))` — **no** stat numbers or table instructions |
| 4 | `body = format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)` |
| 5 | `self.creation.classes_table_shown = True` **before** return (CLASS commit guard) |
| 6 | `return _compose_creation_narration(flavor, body)` |
| 7 | **Delete:** `context` JSON block, custom `messages`, `return _narrate_only(messages)` |
| 8 | Update docstring: "code rolls and formats tables; LLM flavor only" |

**HP:** owned by `format_roll_stats_table` — remove duplicate `hp`/`sta` locals in orchestrator unless needed elsewhere (they are not after refactor).

**Reference pattern:** `_auto_present_skills` (~L869–880).

---

### 3. Chain dedup — `app/gm/orchestrator.py`

**File:** `_chain_after_creation_choice` ~L846–851.

**Change:**

```python
# Before (APP-057):
if self.creation.step == "ROLL_STATS":
    roll_part = self._auto_roll_stats("[SYSTEM: Step auto-advanced. Continue.]")
    if self.creation.step == "CLASS":
        class_part = self._auto_present_class("[SYSTEM: Step auto-advanced. Continue.]")
        return f"{roll_part}\n\n{class_part}".strip()
    return roll_part

# After (APP-067):
if self.creation.step == "ROLL_STATS":
    return self._auto_roll_stats("[SYSTEM: Step auto-advanced. Continue.]")
```

**Leave unchanged:** `_auto_present_class` implementation (still sets flag, still used for Flow C).

**Note:** After race commit, `advance()` lands on `ROLL_STATS`; `_auto_roll_stats` advances to `CLASS` before return — chain condition `step == "ROLL_STATS"` is true **before** roll runs, not after. Existing APP-057 chain already calls `_auto_roll_stats` when step is `ROLL_STATS` post-RACE advance — verify in impl: `_execute_creation_choice` advances RACE → step `ROLL_STATS`, then chain fires. No change to that trigger.

---

### 4. Tests — `app/tests/test_creation_flow.py`

**Prefer** extending existing integration test (ticket allows `test_creation_tables.py`; no file today — optional unit test only if formatter logic needs isolation).

#### 4.1 Update `FIXED_ROLL` (~L5–21) to production shape

| Field | Change |
|-------|--------|
| `base_rolls` | Remove `LUC`; keep STR–SPI only |
| `genetic_factors` | Per attr: `{"roll": 2, "mod": 0}` (mods 0 preserve current finals with base/racial as today) |
| `final_attributes`, `eligible_classes`, `life_event`, `racial_adjustments` | Keep values so FSM path still reaches `apprentice` |

**Example genetic_factors block:**

```python
"genetic_factors": {
    a: {"roll": 2, "mod": 0}
    for a in ("STR", "AGI", "STA", "INT", "SPI")
},
```

#### 4.2 Assertions after turn 3 (`"human"`)

Inside `test_full_creation_apprentice_caster`, when `text == "human"` (after `process_turn`):

| Assert | Expected |
|--------|----------|
| `creation.step` | `"CLASS"` (existing loop) |
| `creation.classes_table_shown` | `True` |
| Header | `"Attr | Base | Genetic | Life Evt | Racial | Final" in last` |
| Life event | `"Life event: Unremarkable Youth" in last` |
| Finals | For each attr in `FIXED_ROLL["final_attributes"]`, row contains `| {attr} |` … `| {final} |` — e.g. `| STR |` and `| 10 |` as Final cell (use substring matching resilient to column spacing) |
| LUC | `| LUC |` and `| 10 |` (Final); `—` in intermediate columns optional |
| HP | `"**HP:** 60"` in `last` and `"(10 + STA 10 × 5)"` or tolerant `STA 10` + `60` |
| Class table once | `last.count("Pick **one tier-1 class**") == 1` |
| No chain duplicate | `"**Final attributes:**" not in last` (roll path must not chain `_auto_present_class`) |
| Flavor | `"Test narration." in last` (mock LLM still present) |

**Optional:** `test_format_roll_stats_table_returns_expected_markdown()` in same file or new `test_creation_tables.py` — call formatter directly with `FIXED_ROLL`; not required for ticket AC if integration asserts pass.

#### 4.3 Commands

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

---

### 5. Spec changelog on close — `tmp/app-character-creation-spec.md`

**Not in implementation diff until ticket release** — Dev impl stage should:

1. Confirm domain spec § `format_roll_stats_table`, ROLL_STATS orchestration, APP-067 tests already match code (draft from PM).
2. On `claim_ticket.py release APP-067 --done`, append changelog row:

`| 2026-05-20 | APP-067 done: code-owned ROLL_STATS table; chain dedup; test assertions |`

3. Mark backlog ticket AC checkboxes + **Closed** date.

**Optional note** (spec prose only, no code): `get_step_prompt` / `system_prompt.py` still mention LLM roll table — flavor-only after APP-067 (non-goal cleanup).

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/creation.py` | Add `format_roll_stats_table` |
| `app/gm/orchestrator.py` | Import formatter; refactor `_auto_roll_stats`; chain dedup |
| `app/tests/test_creation_flow.py` | `FIXED_ROLL` shape + APP-067 assertions after `"human"` |
| `tmp/app-character-creation-spec.md` | Changelog on close (verify draft sections; no behavior drift) |

**Out of scope (explicit):** `app/gm/bridge.py`, `system_prompt.py`, `get_step_prompt`, new `test_creation_tables.py` unless optional unit test added.

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `cd app && python -m pytest tests/test_creation_flow.py -q` | all pass |
| 2 | Manual grep | `_auto_roll_stats` has no `_narrate_only` call |
| 3 | Manual grep | `_chain_after_creation_choice` ROLL_STATS branch has no `_auto_present_class` |

---

## Rollback / flags

Single cohesive revert of four files restores LLM table path. No feature flags. If class commits fail with "Class table must be shown", check `classes_table_shown` is set in `_auto_roll_stats` before return.

---

## Open questions

- **None blocking.** LUC row uses `—` per domain spec; HP formatting uses `×` in spec example — match `format_roll_stats_table` and test substring accordingly.
- **Active ticket:** ensure session claims APP-067 before impl (`tmp/.active-ticket.json` may still show APP-066 per QA spec note).
