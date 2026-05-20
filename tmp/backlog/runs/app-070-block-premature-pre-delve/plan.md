# Implementation Plan: APP-070-block-premature-pre-delve

**Status:** draft (Dev plan)  
**backlog_ticket:** APP-070  
**ticket_path:** tmp/backlog/app-070-block-premature-pre-delve-narration.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Inputs:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Narration-only false completion: FSM and engine stay on desk steps with empty roster, but thin-LLM **flavor** can invent `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver”. **APP-009** already gates `_auto_finalize()` (~1018–1026); APP-070 hardens the **flavor layer** only.

| Layer | Mechanism | Owner |
|-------|-----------|-------|
| **P0 player** | Compose-time sanitizer on flavor (C1–C5) | `creation.py` helper + `_compose_creation_narration` |
| **P0 telemetry** | Extend `_check_creation_drift` D1a–D1c (+ optional D2) | `orchestrator.py` |
| **P0 regression** | `test_skills_turn_rejects_premature_completion_flavor` | `test_creation_flow.py` |

**Defense order:** sanitizer (player never sees leak) → drift logging (QA dashboards).

**Non-goals:** APP-069 body/FSM alignment, APP-073 bracket tag strip, APP-072 duplicate tables, reopen APP-009 finalize gate.

---

## Code-path traces (current → planned)

### Flow A — Dumpy failure vector (skills commit → false completion prose)

| # | File:lines | Current behavior | Planned |
|---|------------|------------------|---------|
| 1 | `orchestrator.py:468–469` | `process_turn` → `_creation_turn` when `creation.active` | unchanged |
| 2 | `orchestrator.py:586–658` | `_creation_turn_body` branches on `creation.step` | unchanged |
| 3 | `orchestrator.py:617–623` | `SKILLS` + `skills_table_shown` → `_handle_creation_response` or `_auto_present_skills` | unchanged |
| 4 | `orchestrator.py:768–794` | SKILLS: `is_equipment_confirm("yes")` → error re-show; else `parse_player_skills` → `_execute_creation_choice` → `_chain_after_creation_choice` | unchanged — FSM does not reach `FINALIZE` |
| 5 | `orchestrator.py:854–866` | After SKILLS advance: `step == SPELL_SCHOOLS` → `_auto_present_schools` same turn | unchanged |
| 6 | `orchestrator.py:558–575` | `_narrate_flavor` → stub/live LLM may return completion copy | test injects bad content here |
| 7 | `orchestrator.py:520–537` | `_compose_creation_narration` — see trace below | **+ sanitizer after tag strip** |
| 8 | `orchestrator.py:260–262` | `_emit_narration` → `_check_creation_drift` | drift extended (D1/D2) |
| 9 | `creation.py:532–535` | `strip_llm_status_tags` — bracket `[Phase:…]` removed; prose remains | unchanged; C5 re-run after sanitizer |
| 10 | `creation.py:538–541` | `format_creation_status` → desk footer `Awaiting: SPELL_SCHOOLS_INPUT` (no `Phase:`) | unchanged |
| 11 | `orchestrator.py:1018–1055` | `_auto_finalize` roster gate + legitimate `footer=` with `Phase: preparation` | **do not regress** — sanitizer skips `footer=` path body |

### Trace — `_compose_creation_narration` (`orchestrator.py:520–537`)

**Current (all `_auto_present_*` and `_auto_finalize` success call this):**

```520:537:app/gm/orchestrator.py
    def _compose_creation_narration(
        self,
        flavor: str,
        body: str = "",
        *,
        footer: str | None = None,
    ) -> str:
        """Thin LLM flavor + code body + code-owned status footer."""
        parts: list[str] = []
        cleaned = strip_llm_status_tags(flavor)
        if cleaned:
            parts.append(cleaned)
        if body.strip():
            parts.append(body.strip())
        status_line = footer if footer is not None else format_creation_status(self.creation)
        if status_line:
            parts.append(status_line)
        return "\n\n".join(parts)
```

**Call sites (flavor path — sanitizer applies):**

| Symbol | Lines | Notes |
|--------|-------|-------|
| `_auto_present_name` | 683–692 | |
| `_auto_present_race` | 694–704 | |
| `_auto_present_class` | 706–719 | |
| `_auto_roll_stats` | ~936–953 | |
| `_auto_present_skills` | 881–892 | **T1 test turn** |
| `_auto_present_schools` | 894–908 | chained after SKILLS commit |
| `_auto_present_spells` | 910–921 | |
| `_auto_present_equipment` | 923–934 | |
| `_auto_finalize` | 1040–1055 | `footer=` override — sanitizer on flavor only (C2) |

**Planned compose sequence:**

1. `cleaned = strip_llm_status_tags(flavor)` — `creation.py:532–535`
2. **NEW:** `roster_len = len(self.bridge.status().get("roster") or [])` (try/except → 0)
3. **NEW:** if `self.creation.active or roster_len == 0`: `cleaned = sanitize_premature_completion_flavor(cleaned, active=..., step=..., roster_len=...)` — `creation.py` (see §1.1)
4. **NEW (C5):** if sanitizer mutated string: `cleaned = strip_llm_status_tags(cleaned)`
5. Append `cleaned` / `body` / `footer` as today

**Guard (C2):** Never run sanitizer on `body` or `footer`. `_auto_finalize` success body `**{name}** is registered —` at `1054` and footer `Phase: preparation` at `1054` remain untouched.

### Trace — `_check_creation_drift` (`orchestrator.py:180–234`)

**Scope gate (unchanged):**

```180:190:app/gm/orchestrator.py
    def _creation_drift_scope(self) -> bool:
        if self.creation.active:
            return True
        ...
        return (
            status.get("awaiting") == "CHARACTER_CREATION"
            and not (status.get("roster") or [])
        )
```

**Parse + reasons (current):**

```192:234:app/gm/orchestrator.py
    def _check_creation_drift(self, narration: str) -> None:
        if not self._creation_drift_scope():
            return
        narrated = parse_narration_status_line(narration)  # logger.py:65–77
        ...
        roster = status.get("roster") or []
        ...
        if self.creation.active and narrated_awaiting:
            expected_awaiting = self._expected_creation_awaiting_label()  # 174–178
            if narrated_awaiting != expected_awaiting:
                reasons.append("awaiting_mismatch")
        if narrated_phase and engine_phase and narrated_phase != engine_phase:
            reasons.append("phase_mismatch")
        if self.creation.active and narrated_phase in _PREMATURE_EXPLORE_PHASES:  # 65: delve|ingress|extract|aftermath
            reasons.append("premature_exploration_phase")
        ...
        log_creation_drift(payload)  # roster_len at 224
```

**Invoked from:** `_emit_narration` `260–262` after every creation narration.

**Planned additions (module level ~65):**

```python
_PREMATURE_EXPLORE_PHASES = frozenset({"delve", "ingress", "extract", "aftermath"})  # existing :65
_PRE_DELVE_PHASES = frozenset({"pre_delve", "pre-delve"})  # NEW
```

**Inside `_check_creation_drift`, after existing reason logic, when `len(roster) == 0`:**

| ID | Condition | Reason |
|----|-----------|--------|
| **D1a** | `narrated_phase in _PRE_DELVE_PHASES` | `premature_exploration_phase` |
| **D1b** | `creation.active` and `narrated_awaiting == "RECEPTION_CHOICE"` | `premature_exploration_phase` |
| **D1c** | `creation.active` and `narrated_phase == "preparation"` and `creation.step != "WORLD_INTRO"` | `premature_exploration_phase` |

**Optional D2:** If `roster_len == 0` and narration (substring scan on full string, or flavor+body slice before footer) matches `registered delver` / `you are now a registered` → append `premature_completion_copy`. Ship D1-only if sanitizer is total; QA notes drift optional for T1.

**Exclusions:** When `not creation.active` and `roster_len > 0` and `step == WORLD_INTRO`, D1b/D1c must **not** fire (legitimate footer at `1054`).

### Trace — sanitizer helper (new, `creation.py`)

**Planned symbol:** `sanitize_premature_completion_flavor(flavor: str, *, active: bool, step: str, roster_len: int) -> str`

**Placement:** After `strip_llm_status_tags` (`creation.py:532–535`), before `format_creation_status` (`538–541`). Export from `creation.py`; import in `orchestrator.py` alongside `strip_llm_status_tags` (line 29).

**Apply gate (C1):** Caller only invokes when `active or roster_len == 0`.

**Removal rules (C3–C4) — flavor string only:**

| Pattern | Action |
|---------|--------|
| `PRE_DELVE`, `pre-delve` (case-insensitive) | Remove line or blank entire flavor if only completion copy |
| `Awaiting: RECEPTION_CHOICE` (unbracketed in flavor) | Strip |
| `registered Delver`, `registered delver`, `you are now a registered`, `is now a registered` | Strip phrase / blank flavor |
| `Phase: preparation` when `active` and `step != "WORLD_INTRO"` | Strip from flavor (C4) |

**Implementation sketch:** Compile case-insensitive regexes; on any match return `""` (simplest, matches domain “blank flavor” option) or line-filter — prefer **blank whole flavor** when any C3 marker hit to avoid partial leaks.

**Do not match:** `_auto_finalize` body patterns after finalize (`is registered` in code body at `1048` — sanitizer never sees body).

### Trace — `test_skills_turn_rejects_premature_completion_flavor` (`test_creation_flow.py`)

**Golden-path indices (`INPUTS` lines 26–35):**

| Turn # | Input | Expected step after |
|--------|-------|---------------------|
| 1 | `new game` | `NAME` |
| 2 | `Dumpy` | `RACE` |
| 3 | `human` | `CLASS` (roll chain) |
| 4 | `apprentice` | `SKILLS` |
| 5 | `Lore, Spellcasting, Arcana` | `SPELL_SCHOOLS` ← **inject bad flavor on this turn** |

**Test flow:**

1. Reuse `orchestrator` + `FIXED_ROLL` monkeypatch (same as `test_full_creation_apprentice_caster` lines 38–48).
2. `monkeypatch.setattr(orchestrator, "_narrate_flavor", lambda _msgs: BAD_FLAVOR)` where:

   ```text
   BAD_FLAVOR = (
       "You are now a registered Delver. "
       "Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE"
   )
   ```

   (Alternative: patch `mock_openrouter_client` return for one call — `_narrate_flavor` patch is narrower and matches domain spec T1.)

3. Run turns 1–4 unchanged from `INPUTS`.
4. `last = orchestrator.process_turn("Lore, Spellcasting, Arcana")`.
5. **Assert FSM:** `orchestrator.creation.step == "SPELL_SCHOOLS"`; `orchestrator.creation.active is True`.
6. **Assert roster:** `len(orchestrator.bridge.status()["roster"]) == 0`.
7. **Assert narration (case-insensitive where noted):**
   - `"PRE_DELVE" not in last`
   - `"registered Delver" not in last` (and/or `registered delver`)
   - `"RECEPTION_CHOICE" not in last` — safe because desk footer must be `Awaiting: SPELL_SCHOOLS_INPUT` (`creation.py:75`)
   - ` "Awaiting: SPELL_SCHOOLS_INPUT" in last`
8. **Optional:** `drift_events` capture via monkeypatch on `log_creation_drift` — not required if sanitizer is total (domain spec § Tests APP-070).

**Contrast:** `test_full_creation_apprentice_caster` lines 92–94 — turn 8 (`yes`) **allows** `RECEPTION_CHOICE` + `Phase: preparation` with non-empty roster; `PRE_DELVE not in last`.

---

## Task breakdown

### 1. Compose sanitizer (C1–C5)

#### 1.1 `sanitize_premature_completion_flavor` — `app/gm/creation.py`

- Add module-level compiled patterns for C3/C4 markers.
- Function returns stripped/empty string; no bridge import (roster gate in caller).
- Unit-testable in isolation (optional inline asserts in integration test only per ticket).

#### 1.2 Wire into `_compose_creation_narration` — `app/gm/orchestrator.py:520–537`

- Import `sanitize_premature_completion_flavor`.
- Query `roster_len` once per compose.
- Apply sanitizer between lines 529–530 (after first `strip_llm_status_tags`, before `parts.append`).
- C5: second `strip_llm_status_tags` when sanitizer returned different string.

### 2. Drift extension (D1, optional D2)

#### 2.1 Constants — `app/gm/orchestrator.py:65`

- Add `_PRE_DELVE_PHASES`.

#### 2.2 `_check_creation_drift` — `app/gm/orchestrator.py:192–234`

- After line 217 (existing explore-phase check), add D1a–D1c blocks gated on `len(roster) == 0`.
- Keep `awaiting_mismatch` / `phase_mismatch` unchanged.
- Optional D2: regex on narration for registration phrases when `roster_len == 0`.

### 3. Regression test (T1)

#### 3.1 `test_skills_turn_rejects_premature_completion_flavor` — `app/tests/test_creation_flow.py`

- New function after `test_full_creation_apprentice_caster` (~line 95).
- Follow trace in § Flow — test above.

### 4. Domain spec sync (on ticket close)

#### 4.1 `tmp/app-character-creation-spec.md`

- § Block premature completion copy (APP-070): mark implemented; add dated changelog entry cross-linking APP-009.
- No behavior drift — spec already drafts C1–D2/T1.

---

## Verification

```bash
python -m pytest app/tests/test_creation_flow.py::test_skills_turn_rejects_premature_completion_flavor -q
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

**Manual (spec § Stage 7):** `new game` → desk through skills with live model; no “registered Delver” / `PRE_DELVE` until equipment `yes` and roster populated.

---

## Regression guards

| Guard | Location | Check |
|-------|----------|-------|
| APP-009 roster gate | `orchestrator.py:1018–1026` | Do not modify finalize failure path |
| Legitimate reception footer | `orchestrator.py:1054–1055` | `RECEPTION_CHOICE` + `Phase: preparation` only with `footer=` after non-empty roster |
| Golden path | `test_creation_flow.py:92–94` | Still passes after sanitizer |
| Desk footers | `creation.py:69–80` | `RECEPTION_CHOICE` only in `WORLD_INTRO` label map |

---

## File touch list (expected files only)

| File | Change |
|------|--------|
| `app/gm/creation.py` | `sanitize_premature_completion_flavor` + patterns |
| `app/gm/orchestrator.py` | `_compose_creation_narration`, `_check_creation_drift`, `_PRE_DELVE_PHASES` |
| `app/tests/test_creation_flow.py` | `test_skills_turn_rejects_premature_completion_flavor` |
| `tmp/app-character-creation-spec.md` | Changelog on close (not in impl PR unless same commit as release) |
