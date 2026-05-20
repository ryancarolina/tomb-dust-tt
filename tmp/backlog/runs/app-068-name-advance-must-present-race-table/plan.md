# Implementation Plan: APP-068-name-advance-must-present-race-table

**Status:** draft  
**backlog_ticket:** APP-068  
**ticket_path:** tmp/backlog/app-068-name-advance-must-present-race-table.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Belt-and-suspenders fix for intermittent NAME→RACE narration: after a successful NAME commit, return `_auto_present_race()` **directly** from `_handle_creation_response` instead of relying on `_chain_after_creation_choice("")` to match `step == "RACE"`. Add a **chain fallthrough guard** so `creation.step == "RACE"` with race unset never yields bare `"The clerk waits."`. Add regression assertions on turn-2 narration in `test_creation_flow.py`.

Root cause (research): `creation_advanced` logs `NAME`→`RACE` but `_chain_after_creation_choice` sometimes hits the default `return prior or "The clerk waits."` (~867) without calling `_auto_present_race` (no `llm_request` in session log). Direct return removes the chain as single point of failure for NAME.

---

## Code-path traces (current → planned)

### Flow A: Valid NAME → same-turn race table (bug target)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `orchestrator.py:process_turn` → `_creation_turn` | active creation | unchanged |
| 2 | `orchestrator.py:_creation_turn_body` ~585–588 | `step == "NAME"` → `_handle_creation_response` or name re-prompt | unchanged |
| 3 | `orchestrator.py:_handle_creation_response` NAME ~712–724 | `len(text) >= 2` → `_execute_creation_choice("NAME", text)` | unchanged |
| 4 | `orchestrator.py:_execute_creation_choice` NAME ~1193–1197 | set `creation.name`, `advance()` → `RACE`, `races_table_shown = False` (`creation.py` ~219–220), `log_creation_advanced` | unchanged |
| 5 | `_handle_creation_response` NAME success return ~724 | `return self._chain_after_creation_choice("")` | **`return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")`** |
| 6 | `_chain_after_creation_choice` RACE ~843–845 | `if step == "RACE":` → `_auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")` | unchanged for RACE/CLASS/SKILLS/… chain callers; **not** on NAME success path |
| 7 | `_auto_present_race` ~681–691 | `races_table_shown = True`; flavor + `format_races_table()` + `_compose_creation_narration` → footer `Awaiting: RACE_INPUT` | unchanged |
| 8 | `_creation_turn_body` ~647–649 | `_emit_narration`, history append | unchanged |

**Failure path (observed):** Step 5 calls chain with `prior == ""`; no branch matches at chain entry → step 6 skipped → `return prior or "The clerk waits."` → narration exactly `"The clerk waits."`, `races_table_shown` stays `False`.

**Planned:** Step 5 bypasses chain; step 7 always runs on NAME success.

### Flow B: `_creation_turn_body` RACE routing after NAME (unchanged)

| Step | File:symbol | Behavior |
|------|-------------|----------|
| 1 | ~590–591 | Next turn: `step == "RACE"` and (`is_system_trigger` or `not races_table_shown`) → `_auto_present_race` |
| 2 | ~592–596 | Else: `_handle_creation_response` or re-prompt with error |

After fix, turn 1 after NAME has `races_table_shown == True`, so turn 2 uses the `elif self.creation.step == "RACE"` commit branch (~592–596), not duplicate auto-present unless input invalid.

### Flow C: Recovery — repeat name at RACE (edge, non-goal duplicate tables)

| Step | File:symbol | Current | After fix |
|------|-------------|---------|-----------|
| 1 | Player sends `"Caddy"` at `RACE` | `parse_player_race` fails → `_handle_creation_response` returns `None` | unchanged |
| 2 | ~592–596 | `or` → `_auto_present_race(..., error="Pick one race...")` | unchanged; may stack stub flavor + code table (session Caddy ~176–179) — **out of scope** per spec non-goals |

### Flow D: Chain fallthrough guard (R2 belt)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `_chain_after_creation_choice` ~864–867 | `FINALIZE` branch then `return prior or "The clerk waits."` | **Before** default: if `self.creation.step == "RACE" and not self.creation.race.strip()`: `return self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")` (or merge with `prior` like existing RACE branch) |
| 2 | Callers still using chain after NAME | N/A after Flow A | Guard covers SPELL skip edges, resume, and any future caller that advances to `RACE` without table |

Use same `prior` merge as existing RACE branch when `prior` non-empty:

```python
if self.creation.step == "RACE" and not self.creation.race:
    extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
    return f"{prior}\n\n{extra}".strip() if prior else extra
```

Place **after** the explicit `if self.creation.step == "RACE":` block (~843–845) is redundant if identical — instead **replace** the early RACE block logic with the guard that also checks `not race`, OR keep early branch and add guard only on fallthrough. Cleanest: **widen** existing RACE branch condition to `step == "RACE"` (unchanged) and add **pre-fallthrough** guard duplicate only if early branch removed. Recommended: single RACE block at ~843; add fallthrough guard before line 867 for `step == "RACE"` when early branch was skipped (defensive duplicate is OK; Dev may collapse to one RACE block).

---

## Task breakdown

### 1. NAME handler direct `_auto_present_race` — `app/gm/orchestrator.py`

**Location:** `_handle_creation_response`, NAME branch ~721–724.

**Change:**

```python
# Before:
return self._chain_after_creation_choice("")

# After:
return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")
```

**Unchanged on this branch:** `_execute_creation_choice` failure still returns `_auto_present_name(..., error=...)`; short name / bracket prefix still `return None`; equipment confirm still `_auto_present_name` error.

**Rationale:** Matches chain output for NAME→RACE (same system trigger string pattern as ~844) without depending on `self.creation.step` inside `_chain_after_creation_choice` at call time.

---

### 2. Chain fallthrough guard — `app/gm/orchestrator.py`

**Location:** `_chain_after_creation_choice`, immediately before `return prior or "The clerk waits."` (~867).

**Change:**

```python
if self.creation.step == "RACE" and not self.creation.race:
    extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
    return f"{prior}\n\n{extra}".strip() if prior else extra
return prior or "The clerk waits."
```

**Note:** Existing `if self.creation.step == "RACE":` block (~843–845) remains for non-NAME chain callers (e.g. hypothetical resume). Guard catches any path that reaches fallthrough while still at `RACE` with empty `race`.

**Optional debug (only if QA cannot repro after fix):** `log_entry("chain_after", {"step": self.creation.step, "race": self.creation.race})` — **not required** for AC; omit unless PM asks.

---

### 3. Regression tests — `app/tests/test_creation_flow.py`

**Option (recommended):** New focused test + light assertions on full-flow turn 2.

#### 3a. `test_name_advance_presents_race_table(orchestrator)`

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

Uses existing `orchestrator` + `mock_openrouter_client` fixtures (flavor stub `"Test narration."` prepended — still satisfies table/footer AC).

#### 3b. Extend `test_full_creation_apprentice_caster` turn 2

Inside the input loop, when `text == "Dumpy"`:

```python
assert "Pick **one race**" in last
assert "| Race | Adjustments | Description |" in last
assert "Awaiting: RACE_INPUT" in last
assert last.strip() != "The clerk waits."
assert orchestrator.creation.races_table_shown is True
```

Keeps APP-057 step FSM checks; APP-068 narration AC on the same turn.

**No new fixtures** — no `monkeypatch` on roll until `"human"` turn.

---

### 4. Domain spec sync on ticket close — `tmp/app-character-creation-spec.md`

**Not in implementation diff unless QA asks for AC checkbox updates during impl.**

On `release --done`:

- Mark APP-068 § NAME→RACE / § Tests APP-068 items satisfied (already drafted ~L61–68, ~L230–242).
- Changelog row: `APP-068 done: NAME success returns _auto_present_race directly; chain RACE fallthrough guard; test_name_advance_presents_race_table`.

---

## Test commands

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

Focused:

```bash
cd app && python -m pytest tests/test_creation_flow.py::test_name_advance_presents_race_table -q
cd app && python -m pytest tests/test_creation_flow.py::test_full_creation_apprentice_caster -q
```

**Manual (session log):** `cd app && python main.py` → new game → name `Caddy` → same response must include `| Race |` and `Awaiting: RACE_INPUT`; log should show `creation_advanced` then `llm_request` then `gm_narration` with table (not bare clerk-waits).

---

## Edge cases

| Case | Expected behavior |
|------|-------------------|
| **Invalid NAME** (`"A"`, `"["`) | `_handle_creation_response` returns `None`; `_creation_turn_body` re-prompts via `_auto_present_name` — **no** race table until valid NAME |
| **Equipment confirm at NAME** (`yes`/`ready`) | `_auto_present_name` error — **no** advance, **no** race table |
| **`races_table_shown` on NAME success** | `_execute_creation_choice` / `advance()` sets `False` on entering `RACE`; `_auto_present_race` sets `True` before return — required for RACE commit guard in `_execute_creation_choice` (~1200–1201) on next turn |
| **Recovery turn** (repeat name at `RACE`) | `races_table_shown` already `True` from fixed NAME turn; invalid race input → error re-prompt; duplicate LLM+code tables possible — **non-goal** |
| **Chain with empty `prior` from other steps** | RACE guard prevents clerk-waits when `step == RACE` and `race` empty |
| **Concurrent `process_turn`** | UI `turn_lock` — out of scope; fix is synchronous FSM |
| **Stub flavor in tests** | `mock_openrouter_client` returns `"Test narration."`; assertions target **code** table strings and footer, not flavor text |

---

## Acceptance mapping

| Spec / ticket AC | Plan task |
|------------------|-----------|
| R1: same-turn `_auto_present_race` body + footer | Task 1 |
| R2: no bare `"The clerk waits."` at RACE | Tasks 1 + 2 |
| R3: integration test name → table + `RACE_INPUT` | Task 3 |
| Ticket: `_chain_after` / NAME always returns race table | Tasks 1 + 2 |
| Spec changelog on close | Task 4 |

---

## Files touched ( ⊆ ticket Expected files )

| File | Changes |
|------|---------|
| `app/gm/orchestrator.py` | Task 1–2 |
| `app/tests/test_creation_flow.py` | Task 3 |
| `tmp/app-character-creation-spec.md` | Task 4 on close only |
