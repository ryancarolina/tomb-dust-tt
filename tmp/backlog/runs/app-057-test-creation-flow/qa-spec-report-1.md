# QA Report: spec — round 1

**Task:** APP-057-test-creation-flow
**backlog_ticket:** APP-057
**ticket_path:** tmp/backlog/app-057-test-creation-flow.md
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)
**domain_spec_creation:** not_needed (registry_gap false; domain spec draft present)
**Finding count:** 4

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` R3 input table (turns 3–4: `human`, `apprentice`); `app/gm/orchestrator.py` `_creation_turn_body`
- **Issue:** RACE and CLASS routing use `not self.creation.race` / `not self.creation.chosen_class` as auto-present triggers. While those fields are empty, **every** player turn hits `_auto_present_race` / `_auto_present_class` and never reaches `_handle_creation_response`, so picks are never committed. SKILLS+ steps correctly gate on `*_table_shown` flags; RACE/CLASS have no equivalent.
- **Code evidence:**

```590:603:app/gm/orchestrator.py
        elif self.creation.step == "RACE" and (is_system_trigger or not self.creation.race):
            narration = self._auto_present_race(player_input)
        elif self.creation.step == "RACE":
            narration = self._handle_creation_response(player_input) or self._auto_present_race(
                player_input,
                error="Pick one race from the table.",
            )
        elif self.creation.step == "CLASS" and (is_system_trigger or not self.creation.chosen_class):
            narration = self._auto_present_class(player_input)
        elif self.creation.step == "CLASS":
            narration = self._handle_creation_response(player_input) or self._auto_present_class(
```

- **Runtime verification:** QA replayed the spec’s 8 inputs with APP-049-equivalent fixtures (isolated workspace, stubbed `create_client`, patched `roll_attributes`). After turn 2 (`Dumpy`) step=`RACE`; turns 3–8 never advance past `RACE`; roster empty; no finalize.
- **Suggested fix:** Align RACE/CLASS with SKILLS pattern (`races_table_shown` / `classes_table_shown`, set in `_auto_present_*`, gate auto-present on `not *_table_shown` or `is_system_trigger` only). **Prerequisite for APP-057 test green** — not optional.

### SPEC-002 — blocker

- **Location:** `spec.md` R3 (8-turn input table); `app/gm/orchestrator.py` `_chain_after_creation_choice`, `_auto_roll_stats`
- **Issue:** Spec assumes one player input per FSM commit (8 turns total). Code chains table presentation for SKILLS→SPELL_SCHOOLS→SPELLS→EQUIPMENT but **not** for NAME→RACE or ROLL_STATS→CLASS:
  - After NAME, `_chain_after_creation_choice` has no `RACE` handler — race table not shown in the Dumpy response (`research-brief` trace overstates auto-present).
  - After RACE (if fixed), chain calls `_auto_roll_stats`, which advances to `CLASS` but returns `_narrate_only` **without** `format_classes_table()` (unlike `_auto_present_class`).
  - With table-shown gating (SPEC-001 fix), turns 3 and 4 become present-only unless chain auto-presents in the **prior** turn’s chain output.
- **Suggested fix:** (a) Add `_chain_after_creation_choice` handlers for `RACE` and post-roll `CLASS` (mirror SKILLS chain); and/or (b) embed `format_classes_table()` in `_auto_roll_stats` return. Update R3 input table or document required chain behavior so Dev/QA agree on turn count.

### SCOPE-001 — blocker

- **Location:** `spec.md` § Non-goals (“Changes to `creation.py` / `orchestrator.py` behavior (test-only ticket)”)
- **Issue:** SPEC-001 and SPEC-002 require orchestrator/creation routing changes for the spec’s assertions to pass. Ticket AC and R3 post-finalize assertions (`WORLD_INTRO`, non-empty roster, `PLAYER_ACTIONS`) are **not achievable** under test-only scope on current code.
- **Suggested fix:** Either (a) split — prerequisite ticket (e.g. APP-057a) for RACE/CLASS table-shown + chain fixes, then APP-057 test-only; or (b) expand APP-057 Expected files and non-goals to include minimal orchestrator fixes; or (c) narrow spec AC to parser-level tests only (contradicts ticket intent).

### SPEC-003 — major

- **Location:** `spec.md` R1; `tmp/app-character-creation-spec.md` § Integration test (APP-057)
- **Issue:** Domain spec lists fixtures `orchestrator`, **`mock_openrouter_client`**; run spec R1 names only `orchestrator`. Relies on pytest dependency chain (works today via `conftest.py`) but omits explicit rule that test module must not import `Orchestrator` at module level before patches (APP-049 lesson).
- **Suggested fix:** Add R1 bullet: test function may depend on `orchestrator` only (transitively applies `mock_openrouter_client`); forbid module-level `from gm.orchestrator import Orchestrator`.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Ticket AC ⊆ spec R3; Expected files aligned |
| Registry/drift | **PASS** | `registry_gap: false`; domain spec § Integration test (APP-057) drafted |
| Code trace (inputs 5–8) | **PASS** | Skills/schools/spells/equipment names match `creation.py` parsers + `build/data/spells/spells.json`; `ember-touch`/`static-lash` tier-1 for `pyromancy`/`ether` confirmed in `test_creation_gating.py` |
| Assertions (shape) | **PASS** | `status["roster"][0]["display_name"]`, `base_class`, `awaiting == PLAYER_ACTIONS`, footer substrings match `cmd_core.py` + `_auto_finalize` when finalize runs |
| Achievability (E2E) | **FAIL** | 8-input sequence does not reach finalize on current orchestrator |
| Adversarial | **FAIL** | SPEC-001–003, SCOPE-001 |

## Verified (positive)

| Claim | Evidence |
|-------|----------|
| Spell/skill IDs valid | `parse_player_skills("Lore, Spellcasting, Arcana", "apprentice")`; `parse_player_schools("pyromancy, ether", "apprentice")`; `test_creation_gating.py` apprentice spell table |
| Post-finalize assertions (when reached) | `_auto_finalize` footer `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` (`orchestrator.py:1048`); roster `display_name`/`base_class` in `cmd_core.py:164-168` |
| APP-049 fixtures sufficient | `app/tests/conftest.py` — `orchestrator`, `mock_openrouter_client`, isolated workspace |
| Militia deferral | PM decision documented; ticket AC satisfied by single apprentice path |
| Domain spec synced | `tmp/app-character-creation-spec.md` § Integration test, checklist, changelog draft |

## Summary

Spec quality is strong on fixtures, assertion table, and domain-spec alignment, but **round 1 FAIL** because the canonical 8-input integration path is not runnable on current code and non-goals forbid the required orchestrator fixes. Resolve SPEC-001/002 (and SCOPE-001) before Dev plan.

## Re-review focus

- RACE/CLASS `*_table_shown` gates + chain handlers documented in spec
- Turn-count table matches chain auto-present behavior
- Scope: prerequisite ticket vs expanded APP-057 Expected files
- R1 mock/import discipline bullet
