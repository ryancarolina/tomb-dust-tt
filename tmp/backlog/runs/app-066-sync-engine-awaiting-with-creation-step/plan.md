# Implementation Plan: APP-066-sync-engine-awaiting-with-creation-step

**Status:** draft  
**backlog_ticket:** APP-066  
**ticket_path:** tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Fix is **drift-comparator only** in `app/gm/orchestrator.py`. Engine `awaiting` stays coarse `CHARACTER_CREATION` (`play/tomb_gm/cli/cmd_core.py` ~178–180); granular footers stay in `format_creation_status()` / `CREATION_STATUS_LABELS`. When `creation.active`, compare narrated `Awaiting:` to the **same label map** as the footer formatter, not to `status["awaiting"]`. Domain/logging specs already draft the contract (PM pass); Dev adds implementation changelog lines on ticket close.

**Out of scope:** `app/gm/bridge.py`, `play/tomb_gm/`, edits to `creation.py` body (import only from orchestrator).

---

## Code-path traces

### Trace A: Granular footer (healthy path — today triggers false drift)

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `orchestrator.py:647` | `_creation_turn_body` returns narration → `_emit_narration(narration)` |
| 2 | `orchestrator.py:507–524` | `_compose_creation_narration` → default `footer=None` → `format_creation_status(self.creation)` |
| 3 | `creation.py:538–541` | `label = CREATION_STATUS_LABELS.get(state.step, f"{state.step}_INPUT")` → `"Awaiting: {label}"` |
| 4 | `orchestrator.py:247–249` | `_emit_narration` → `_check_creation_drift(narration)` |
| 5 | `logger.py:65–77` | `parse_narration_status_line` → `narrated_awaiting` e.g. `SKILLS_INPUT` |
| 6 | `bridge.py:36–37` → `cmd_core.py:178–180` | `status["awaiting"]` = `CHARACTER_CREATION` (empty roster) |
| 7 | `orchestrator.py:202–203` **(bug)** | `narrated_awaiting != engine_awaiting` → `awaiting_mismatch` every turn |

**After fix (step 7):** when `creation.active`, compare to `CREATION_STATUS_LABELS[step]` (uppercase); steps 1–6 unchanged.

### Trace B: Drift scope (unchanged per R4)

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `orchestrator.py:172–174` | `creation.active` → scope `True` |
| 2 | `orchestrator.py:175–182` | else: `awaiting == CHARACTER_CREATION` and empty `roster` → scope `True` (resume edge) |
| 3 | `orchestrator.py:185–186` | scope false → return (no log) |
| 4 | `orchestrator.py:188–189` | no `Phase:` and no `Awaiting:` in narration → return (no log) |

**Planned:** no edits to `_creation_drift_scope` (L172–182).

### Trace C: Phase drift during desk creation

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `creation.py:538–541` | Desk footers: **no** `Phase:` (only `Awaiting:`) |
| 2 | `orchestrator.py:204–205` | `phase_mismatch` only if **both** `narrated_phase` and `engine_phase` present and differ |
| 3 | `orchestrator.py:206–207` | `premature_exploration_phase` if `creation.active` and narrated phase in `_PREMATURE_EXPLORE_PHASES` (L63) |

**Planned:** keep L204–207 logic; no change required for R3 (benign omission already satisfied). Optional tighten (recommended in spec): wrap L204–205 so `phase_mismatch` does not run when `creation.active` and `narrated_phase` absent — redundant with current `and narrated_phase` guard; **no code change** unless QA finds LLM-only phase leaks without `awaiting` line.

### Trace D: Post-finalize `WORLD_INTRO` (out of desk contract)

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `orchestrator.py:1050–1058` | Custom footer: `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` |
| 2 | After finalize | `creation.active` = `False`; roster non-empty |
| 3 | `orchestrator.py:172–182` | Scope false (roster non-empty) → **no** `_check_creation_drift` for reception footer vs `PLAYER_ACTIONS` |

No change needed for post-finalize false positives.

### Trace E: Resume edge (`creation.active` false, scope true)

| Condition | Planned awaiting compare |
|-----------|-------------------------|
| `creation.active` + `narrated_awaiting` | Expected = `CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()` |
| not `creation.active` + scope true | **Skip** awaiting compare (R4) — avoid stale/missing `creation.step` |
| not `creation.active` + scope false | N/A |

---

## Exact code changes

### 1. Import `CREATION_STATUS_LABELS` — `app/gm/orchestrator.py`

**File:line:** L16–42 (`from gm.creation import (...)`)

Add `CREATION_STATUS_LABELS` to the existing import tuple (alphabetize with other symbols or place after `CreationState`).

```python
from gm.creation import (
    CreationState,
    CREATION_STATUS_LABELS,
    ...
)
```

### 2. Helper for expected awaiting (optional inline) — `app/gm/orchestrator.py`

**Placement:** immediately before `_creation_drift_scope` (~L171) or inside `_check_creation_drift`.

**Logic (must mirror `creation.py:540`):**

```python
def _expected_creation_awaiting_label(self) -> str:
    label = CREATION_STATUS_LABELS.get(
        self.creation.step, f"{self.creation.step}_INPUT"
    )
    return label.upper()
```

### 3. Rewrite awaiting/phase branch — `app/gm/orchestrator.py` L184–221

**Replace** L201–207 `reasons` block with:

| Branch | Condition | Action |
|--------|-----------|--------|
| Awaiting (active) | `creation.active` and `narrated_awaiting` | `expected = _expected_creation_awaiting_label()`; if `narrated_awaiting != expected` → `awaiting_mismatch` |
| Awaiting (resume edge) | not `creation.active` and `narrated_awaiting` | **no** awaiting compare (R4) |
| Phase | `narrated_phase` and `engine_phase` and differ | `phase_mismatch` (unchanged) |
| Premature explore | `creation.active` and `narrated_phase in _PREMATURE_EXPLORE_PHASES` | `premature_exploration_phase` (unchanged) |

**Remove** comparison of `narrated_awaiting` to `engine_awaiting` when `creation.active` (current L202–203).

**Keep** L187–199 parse/status fetch; L209–210 early return; L212–221 `log_creation_drift` payload.

### 4. Optional payload field (R5) — `app/gm/orchestrator.py` L212–221

When logging `awaiting_mismatch` and `creation.active`, add to dict:

```python
"expected_awaiting": expected_awaiting,  # only when computed
```

Keep `"awaiting": status.get("awaiting")` as engine value for grep.

### 5. Domain spec changelog — `tmp/app-character-creation-spec.md`

**On ticket close:** append changelog row (L296+ table): `APP-066: drift check uses CREATION_STATUS_LABELS when creation.active; engine CHARACTER_CREATION documented as coarse layer`.

§ Awaiting contract (L150–163) already matches spec — verify no wording drift after code lands.

### 6. Logging spec changelog — `tmp/app-logging-qa-spec.md`

**On ticket close:** append changelog (L151+ table): `APP-066: creation_drift awaiting compare uses expected label from creation.step`.

§ `creation_drift` (L25–48) already updated in PM pass — confirm implementation matches table.

### 7. Optional test — `app/tests/test_creation_flow.py`

**Gate:** add `app/tests/test_creation_flow.py` to ticket **Expected files** before edit (per qa-spec-pass note).

**In `test_full_creation_apprentice_caster`:**

```python
drift_events: list[dict] = []
monkeypatch.setattr(
    "gm.orchestrator.log_creation_drift",
    lambda data: drift_events.append(data),
)
# ... existing INPUTS loop ...
assert drift_events == [], f"unexpected creation_drift: {drift_events}"
```

**Optional unit probe** (same file, new test):

```python
def test_check_creation_drift_healthy_skills_step(orchestrator):
    orchestrator.creation.active = True
    orchestrator.creation.step = "SKILLS"
    orchestrator._check_creation_drift("Flavor\n\nAwaiting: SKILLS_INPUT")
    # assert log_creation_drift not called (monkeypatch collector)
```

**Negative probe:**

```python
orchestrator.creation.step = "SKILLS"
orchestrator._check_creation_drift("Awaiting: CLASS_INPUT")
# assert "awaiting_mismatch" in reasons
```

---

## Label reference (`CREATION_STATUS_LABELS`)

Source: `creation.py:69–80` (imported by orchestrator).

| `creation.step` | Expected `narrated_awaiting` |
|-----------------|------------------------------|
| NAME | NAME_INPUT |
| RACE | RACE_INPUT |
| ROLL_STATS | STATS_REVIEW |
| CLASS | CLASS_INPUT |
| SKILLS | SKILLS_INPUT |
| SPELL_SCHOOLS | SPELL_SCHOOLS_INPUT |
| SPELLS | SPELLS_INPUT |
| EQUIPMENT_GOLD | EQUIPMENT_GOLD_CONFIRMATION |
| FINALIZE | FINALIZE |
| WORLD_INTRO | RECEPTION_CHOICE |

Unknown step: `{step}_INPUT` (`creation.py:540`).

---

## Test plan

### Automated

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
```

| Test | Assert |
|------|--------|
| `test_full_creation_apprentice_caster` | Stays green; optional `drift_events == []` |
| `test_check_creation_drift_*` (if added) | Match/mismatch vs `CREATION_STATUS_LABELS` only when `creation.active` |

### Manual / JSONL (Stage 7 human-test-plan)

1. `cd app && python main.py` → new game → complete creation.
2. Grep `app/logs/session-*.jsonl` for `creation_drift` — **no** lines with `awaiting_mismatch` on turns where footer matches step.
3. `creation_step` events still present each turn (APP-003 unaffected).
4. Debug: force wrong footer (if harness) — `awaiting_mismatch` with `expected_awaiting` in payload (if R5 implemented).

### Regression targets

| Scenario | Must not regress |
|----------|------------------|
| Golden-path creation | No per-turn `creation_drift` noise |
| Real drift | LLM `Awaiting: CLASS_INPUT` on `SKILLS` step still logs |
| LLM `Phase: delve` during creation | `premature_exploration_phase` still fires |
| Post-finalize reception | No drift spam (`scope` off) |
| Engine tests | `test_campaign_session.py` green (no engine change) |

---

## Files touched (implementation)

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | Import `CREATION_STATUS_LABELS`; rewrite `_check_creation_drift` L201–221; optional helper ~L171 |
| `tmp/app-character-creation-spec.md` | Changelog on close (§ already drafted) |
| `tmp/app-logging-qa-spec.md` | Changelog on close (§ already drafted) |
| `app/tests/test_creation_flow.py` | **Optional** — drift collector assert (+ ticket Expected files update) |

**Explicitly not edited:** `app/gm/bridge.py`, `app/gm/creation.py` (logic), `play/tomb_gm/**`, `app/gm/logger.py` (parse unchanged).

---

## Acceptance criteria mapping

| Ticket AC | Plan task |
|-----------|-----------|
| Engine awaiting reflects step **or** label drift compare | Task 3 — label compare path; engine unchanged |
| No `creation_drift` every healthy turn | Task 3 — removes false `awaiting_mismatch` |
| Domain spec documents contract | Tasks 5–6 changelog; § already in spec |
| Optional APP-057 drift assert | Task 7 |

---

## Implementation order

1. Import + `_check_creation_drift` rewrite (`orchestrator.py`).
2. Run pytest commands above.
3. Optional test + ticket Expected files line.
4. Spec changelogs + `claim_ticket.py release APP-066 --done`.

**Estimated diff:** ~25–40 lines in `orchestrator.py`; 0–15 lines in test file.
