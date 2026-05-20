# Implementation Plan: APP-057-test-creation-flow

**Status:** draft
**backlog_ticket:** APP-057
**ticket_path:** tmp/backlog/app-057-test-creation-flow.md
**domain_spec:** tmp/app-character-creation-spec.md
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Deliver R1–R6 in dependency order: fix `CreationState` table-shown flags and orchestrator routing/chain/execute guards (R6) so the canonical 8-input Apprentice path reaches `_auto_finalize`, then add `test_creation_flow.py` (R1–R3) that drives `process_turn` with a deterministic `roll_attributes` monkeypatch. No conftest changes unless roll mock is duplicated elsewhere (R4: inline only). Domain spec changelog on ticket close (R5 — not in impl PR).

**Root cause (round 1):** RACE/CLASS auto-present gates on empty `race` / `chosen_class`, so after a failed or replayed turn the table re-shows instead of accepting player input; NAME→RACE and ROLL_STATS→CLASS are not chained, so tables never appear in the same narration as commits.

---

## 1. `app/gm/creation.py` — `CreationState` (R6)

### 1.1 New fields (after `spells_table_shown`, ~L210)

```python
races_table_shown: bool = False
classes_table_shown: bool = False
```

Mirror existing `skills_table_shown` / `schools_table_shown` / `spells_table_shown` pattern.

### 1.2 `advance()` reset blocks (after step increment, ~L217–225)

Add symmetric resets when **entering** a gated step (same pattern as SKILLS/SPELL_SCHOOLS/SPELLS):

| When `self.step ==` | Reset |
|---------------------|-------|
| `"RACE"` | `races_table_shown = False` |
| `"CLASS"` | `classes_table_shown = False` |

Do **not** clear `race` / `chosen_class` on advance — only the table-shown flags (SKILLS clears picks because re-pick is required; RACE/CLASS values are set on commit *before* advance).

Existing blocks unchanged:

```213:226:app/gm/creation.py
    def advance(self):
        idx = CREATION_STEPS.index(self.step)
        if idx < len(CREATION_STEPS) - 1:
            self.step = CREATION_STEPS[idx + 1]
        if self.step == "SKILLS":
            self.skills_table_shown = False
            ...
        skip_inapplicable_spell_steps(self)
```

Insert RACE/CLASS blocks **before** the SKILLS block (order matches step sequence).

### 1.3 `to_dict()` (~L231–248)

Add keys:

```python
"races_table_shown": self.races_table_shown,
"classes_table_shown": self.classes_table_shown,
```

Place alongside other `*_table_shown` keys (after `spells_table_shown`).

### 1.4 `from_dict()` (~L251–268)

Add kwargs:

```python
races_table_shown=bool(data.get("races_table_shown", False)),
classes_table_shown=bool(data.get("classes_table_shown", False)),
```

Default `False` preserves resume behavior for saves missing new keys (APP-010 edge case — acceptable per QA).

---

## 2. `app/gm/orchestrator.py` — routing, chain, execute (R6)

### 2.1 `_creation_turn_body` — auto-present gates (~L590–603)

**Current (broken):**

```590:603:app/gm/orchestrator.py
        elif self.creation.step == "RACE" and (is_system_trigger or not self.creation.race):
            narration = self._auto_present_race(player_input)
        ...
        elif self.creation.step == "CLASS" and (is_system_trigger or not self.creation.chosen_class):
            narration = self._auto_present_class(player_input)
```

**Change:**

| Line | From | To |
|------|------|-----|
| ~590 | `not self.creation.race` | `not self.creation.races_table_shown` |
| ~597 | `not self.creation.chosen_class` | `not self.creation.classes_table_shown` |

SKILLS reference (unchanged, ~L604):

```604:605:app/gm/orchestrator.py
        elif self.creation.step == "SKILLS" and (is_system_trigger or not self.creation.skills_table_shown):
```

After fix: on turn 3 (`"human"`), step is `RACE`, `race` still empty but `races_table_shown` is True from turn 2 chain → route to `_handle_creation_response`, not re-present.

### 2.2 `_auto_present_race` (~L681–690)

At **start** of method (before flavor), set flag — mirror `_auto_present_skills` L862:

```python
self.creation.races_table_shown = True
```

### 2.3 `_auto_present_class` (~L692–704)

At **start** of method:

```python
self.creation.classes_table_shown = True
```

### 2.4 `_chain_after_creation_choice` (~L839–858)

**Add NAME→RACE branch** (insert before `ROLL_STATS`, after docstring):

```python
if self.creation.step == "RACE":
    extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
    return f"{prior}\n\n{extra}".strip() if prior else extra
```

Trigger: NAME commit → `advance()` → step `RACE` → turn 2 narration includes race table.

**Extend ROLL_STATS→CLASS chain** — replace current single-line handler (~L841–842):

```python
if self.creation.step == "ROLL_STATS":
    return self._auto_roll_stats("[SYSTEM: Step auto-advanced. Continue.]")
```

With:

```python
if self.creation.step == "ROLL_STATS":
    roll_part = self._auto_roll_stats("[SYSTEM: Step auto-advanced. Continue.]")
    if self.creation.step == "CLASS":
        class_part = self._auto_present_class("[SYSTEM: Step auto-advanced. Continue.]")
        return f"{roll_part}\n\n{class_part}".strip()
    return roll_part
```

`_auto_roll_stats` (~L915–947) already calls `advance()` to `CLASS` and returns `_narrate_only` (mock LLM string). Chained `_auto_present_class` appends code-owned `format_classes_table()` + stats line — satisfies turn 3 AC without rewriting stats prompt.

**Do not add** a standalone `if self.creation.step == "CLASS"` chain branch — CLASS is reached only via ROLL_STATS in this path; a duplicate branch could double-present.

Existing SKILLS→SPELL_SCHOOLS→SPELLS→EQUIPMENT_GOLD→FINALIZE chains (~L843–857) unchanged.

### 2.5 `_execute_creation_choice` — table-shown guards (~L1190–1209)

**RACE** — insert immediately after `if step != self.creation.step` block, before parsing (~L1190):

```python
elif step == "RACE":
    if not self.creation.races_table_shown:
        return {"ok": False, "error": "Race table must be shown before recording picks."}
    race = value.strip().lower().replace(" ", "-")
    ...
```

**CLASS** — insert before eligible check (~L1200):

```python
elif step == "CLASS":
    if not self.creation.classes_table_shown:
        return {"ok": False, "error": "Class table must be shown before recording picks."}
    chosen = value.strip().lower()
    ...
```

Mirror SKILLS guard (~L1212–1213):

```1211:1213:app/gm/orchestrator.py
        elif step == "SKILLS":
            if not self.creation.skills_table_shown:
                return {"ok": False, "error": "Skills table must be shown before recording picks."}
```

### 2.6 Unchanged paths (verify only)

| Symbol | Lines | Notes |
|--------|-------|-------|
| `_handle_creation_response` RACE/CLASS | 724–751 | Already calls `_execute_creation_choice` then `_chain_after_creation_choice` |
| `_auto_roll_stats` | 915–947 | No change; chain wraps output |
| `_auto_finalize` | 963–1049 | Footer `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` — test asserts these |
| `_creation_llm_loop` tool chain | 1136–1160 | Not on code-first path for APP-057 inputs |

---

## 3. `app/tests/test_creation_flow.py` (R1–R3)

### 3.1 Module structure

```python
"""Integration test: full character creation FSM through finalize (APP-057)."""

# Module-level constant only — NO Orchestrator import (R1 / APP-049)

FIXED_ROLL: dict = { ... }

def test_full_creation_apprentice_caster(orchestrator, monkeypatch):
    ...
```

- **Fixtures:** `orchestrator` only (+ pytest-injected `monkeypatch`). Transitive: `mock_openrouter_client`, `isolated_workspace`.
- **Forbidden:** `from gm.orchestrator import Orchestrator` at module level.
- **Forbidden:** duplicate `mock_openrouter_client` inline.
- **Forbidden:** import from `play/tomb_gm/tests/test_creation_gating.py`.

### 3.2 `FIXED_ROLL` constant

```python
FIXED_ROLL = {
    "ok": True,
    "race": "human",  # overridden by lambda to echo argument
    "racial_adjustments": {"STR": 1, "INT": 1},
    "base_rolls": {"STR": 9, "AGI": 9, "STA": 9, "INT": 11, "SPI": 9, "LUC": 9},
    "genetic_factors": {"STR": 0, "AGI": 0, "STA": 0, "INT": 0, "SPI": 0, "LUC": 0},
    "life_event": {"roll": 20, "name": "Unremarkable Youth", "mods": {}},
    "final_attributes": {"STR": 10, "AGI": 10, "STA": 10, "INT": 12, "SPI": 10, "LUC": 10},
    "eligible_classes": ["peasant", "laborer", "urchin", "apprentice", "militia", "novice"],
}
```

Requirements: `ok: True`, `INT >= 8`, `apprentice` ∈ `eligible_classes`, `militia`/`peasant` included for future tests.

### 3.3 `roll_attributes` monkeypatch (R2)

Before turn loop:

```python
monkeypatch.setattr(
    orchestrator.bridge,
    "roll_attributes",
    lambda race: {**FIXED_ROLL, "race": race},
)
```

Patches instance method on isolated workspace bridge — no conftest change.

### 3.4 Turn loop and per-step assertions (R3)

```python
INPUTS = [
    ("new game", "NAME"),
    ("Dumpy", "RACE"),
    ("human", "CLASS"),
    ("apprentice", "SKILLS"),
    ("Lore, Spellcasting, Arcana", "SPELL_SCHOOLS"),
    ("pyromancy, ether", "SPELLS"),
    ("ember-touch, static-lash", "EQUIPMENT_GOLD"),
    ("yes", "WORLD_INTRO"),
]

last = ""
for text, expected_step in INPUTS:
    last = orchestrator.process_turn(text)
    assert orchestrator.creation.step == expected_step, (
        f"After {text!r}: step={orchestrator.creation.step}, expected {expected_step}"
    )
```

Turn 1: after `"new game"`, assert `orchestrator.creation.active is True`.

Optional mid-loop (nice-to-have, not AC blockers):

- Turn 2: `"Pick **one race**"` or `format_races_table` marker in `last`
- Turn 3: `"Final attributes"` and `"Pick **one tier-1 class**"` in narration

### 3.5 Post-finalize assertions (required)

After loop, `status = orchestrator.bridge.status()`:

| Assert | Expected | Source |
|--------|----------|--------|
| `orchestrator.creation.active` | `False` | `_auto_finalize` L1023 |
| `orchestrator.creation.step` | `"WORLD_INTRO"` | L1024 |
| `len(status["roster"])` | `>= 1` | `cmd_core.py` roster payload |
| `status["awaiting"]` | `"PLAYER_ACTIONS"` | engine after roster populated |
| `status["roster"][0]["display_name"]` | `"Dumpy"` | `cmd_core.py` L164 |
| `status["roster"][0]["base_class"]` | `"apprentice"` | `cmd_core.py` L168 |
| `"Awaiting: RECEPTION_CHOICE" in last` | True | footer L1048 |
| `"Phase: preparation" in last` | True | footer L1048 |
| `"PRE_DELVE" not in last` | True | regression guard |

Optional: `status.get("party", {}).get("phase") == "preparation"` if present.

### 3.6 Isolation

`orchestrator` fixture uses `isolated_workspace` — no writes under `play/workspace`. Verify workspace path assertion already in conftest L89.

---

## 4. `app/tests/conftest.py` (R4)

**No changes** — roll mock stays inline in `test_creation_flow.py`. Revisit only if a second module duplicates `FIXED_ROLL`.

---

## 5. Domain spec sync (R5 — on ticket close, not impl)

- Mark integration test checklist item done in `tmp/app-character-creation-spec.md`
- Append dated changelog entry
- `release --done` per backlog gate

---

## Task breakdown (implementation order)

| # | Task | File | Requirement |
|---|------|------|-------------|
| 1 | Add `races_table_shown`, `classes_table_shown` + serialization + `advance()` resets | `creation.py` | R6 |
| 2 | Swap `_creation_turn_body` RACE/CLASS gates | `orchestrator.py` ~590, ~597 | R6 |
| 3 | Set flags in `_auto_present_race` / `_auto_present_class` | `orchestrator.py` ~681, ~692 | R6 |
| 4 | Add RACE chain + extend ROLL_STATS→CLASS chain | `orchestrator.py` ~839 | R6 |
| 5 | Add RACE/CLASS execute guards | `orchestrator.py` ~1190, ~1200 | R6 |
| 6 | Create `test_full_creation_apprentice_caster` | `test_creation_flow.py` (new) | R1–R3 |
| 7 | Run pytest gates | — | R3 |
| 8 | Spec changelog + ticket close | domain spec, ticket | R5 |

**Workstream suggestion:** WS1 = steps 1–5 (orchestrator fixes); WS2 = step 6 (test). WS2 depends on WS1.

---

## Files (must ⊆ ticket Expected files)

| File | Action |
|------|--------|
| `app/gm/creation.py` | Modify — 2 flags, advance, to_dict/from_dict |
| `app/gm/orchestrator.py` | Modify — gates, chain, present flags, execute guards |
| `app/tests/test_creation_flow.py` | **New** — primary integration test |
| `app/tests/conftest.py` | **No change** (default) |

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 (primary gate) | `python -m pytest app/tests/test_creation_flow.py -q` | exit 0, ≥1 test collected |
| 2 (regression) | `python -m pytest app/tests/test_smoke.py -q` | exit 0 |
| 3 (regression) | `python -m pytest play/tomb_gm/tests/test_creation_gating.py -q` | exit 0 |
| 4 (manual trace) | Replay 8 inputs in PyGame optional | Roster shows Dumpy, phase preparation |

Run from repo root; pytest discovers `app/tests` via existing package layout (APP-049).

---

## Rollback / flags

- New `CreationState` fields default `False` — backward compatible with `from_dict` missing keys.
- No feature flags. Revert orchestrator + creation changes restores pre-APP-057 behavior (broken integration path).

---

## Open questions

_None — QA spec PASS round 2; research-brief pre-fix RACE routing is superseded by spec R6._
