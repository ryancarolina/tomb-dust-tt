# Research Brief: APP-067-code-owned-roll-stats-table

**Date:** 2026-05-20  
**Question:** How should `format_roll_stats_table(roll_result)` be built from the `roll_attributes` payload, and what orchestrator/test changes replace LLM-invented stat math in `_auto_roll_stats()`?

**backlog_ticket:** APP-067  
**ticket_path:** tmp/backlog/app-067-code-owned-roll-stats-table.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md), which owns `app/gm/creation.py` and the creation branch of `app/gm/orchestrator.py`. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** maps to that spec and those paths. No new domain spec is required.

## Summary

`ROLL_STATS` is the only gated creation step that still uses `_narrate_only()` with a system prompt asking the LLM to render the attribute breakdown table (`Attr | Base | Genetic | Life Evt | Racial | Final`). That contradicts APP-006/012/057: other steps use `_narrate_flavor()` + `format_*_table()` + `_compose_creation_narration()`. The roll itself is already deterministic via `GameBridge.roll_attributes()`; the bug is **presentation**, not roll logic.

Fix: add `format_roll_stats_table(roll_result)` in `creation.py` that derives every column from the bridge payload, refactor `_auto_roll_stats()` to the thin-flavor + code-body pattern (including HP `10 + STA×5` and `format_classes_table(eligible)` per ticket AC), and assert table cells in `test_creation_flow.py` (or a small table unit test) against a monkeypatched `FIXED_ROLL` shaped like production `roll_attributes` output.

After a race pick, `_chain_after_creation_choice` calls `_auto_roll_stats` then `_auto_present_class`; today the chain shows a one-line `**Final attributes:**` summary in `_auto_present_class` while the LLM may have already emitted a wrong full table. Dev must avoid **duplicate class tables** and align `classes_table_shown` with whichever path emits `format_classes_table()`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| FSM / state | `app/gm/creation.py` | `CREATION_STEPS`, `CreationState.roll_result`, `format_*_table`, `format_creation_status` |
| Roll + narrate | `app/gm/orchestrator.py` | `_auto_roll_stats`, `_chain_after_creation_choice`, `_auto_present_class`, `_compose_creation_narration` |
| Roll engine (app) | `app/gm/bridge.py` | `GameBridge.roll_attributes` — sole app roll implementation (not `tomb_gm` CLI) |
| Canon HP | `build/systems/core/derived-stats.md`, `play/tomb_gm/domain/character.py` | `HP = 10 + (STA × 5)`; `compute_hp(sta, base_hp=10)` |
| Tests | `app/tests/test_creation_flow.py`, `app/tests/conftest.py` | `FIXED_ROLL` monkeypatch; mock LLM returns `"Test narration."` |
| Stale prompts | `app/gm/creation.py` `get_step_prompt`, `app/gm/system_prompt.py` | ROLL_STATS prompt empty; system prompt still mentions LLM `roll_attributes` table |

## Code-path traces

### Player picks race → roll + class table (canonical path)

1. **Entry:** `_handle_creation_response` RACE branch → `_execute_creation_choice("RACE", …)` (`orchestrator.py` ~726–738).
2. **Advance:** `_execute_creation_choice` calls `creation.advance()` → step `ROLL_STATS` (`orchestrator.py` ~1280–1286).
3. **Chain:** `_chain_after_creation_choice` sees `step == "ROLL_STATS"` → `_auto_roll_stats` then, if step is `CLASS`, `_auto_present_class` (`orchestrator.py` ~846–850).
4. **Roll:** `_auto_roll_stats` calls `bridge.roll_attributes(self.creation.race)`, stores `self.creation.roll_result`, `advance()` to `CLASS`, `_remember_creation_step("ROLL_STATS")` (`orchestrator.py` ~924–930).
5. **Bug — LLM table:** Builds `context` with full `roll_result` JSON and column instructions, then `return self._narrate_only(messages)` (`orchestrator.py` ~937–956) — **not** `_narrate_flavor` / `_compose_creation_narration`.
6. **Chain class body:** `_auto_present_class` adds `stat_bits` one-liner + `format_classes_table(eligible)` (`orchestrator.py` ~693–706).

### Direct `ROLL_STATS` step (resume / edge)

1. **Entry:** `_creation_turn_body` when `creation.step == "ROLL_STATS"` → `_auto_roll_stats` only (`orchestrator.py` ~579–580).
2. **No class chain** unless caller is `_chain_after_creation_choice` — class table may be missing unless roll path includes it (ticket AC wants class table in `_auto_roll_stats`).

### Reference pattern (APP-006) — skills present

1. `_auto_present_skills`: `_narrate_flavor` → `body = err + format_skills_table(...)` → `_compose_creation_narration(flavor, body)` (`orchestrator.py` ~869–880).
2. Footer: `format_creation_status` via `_compose_creation_narration` unless custom footer (`orchestrator.py` ~507–524).

## `roll_attributes` payload shape

**Producer:** `GameBridge.roll_attributes` in `app/gm/bridge.py` (~48–163). App tests/engine CLI `handle_attributes` / `roll_attribute_scores` use a **different** 1d10-only path — **not** what creation uses.

### Top-level keys

| Key | Type | Role |
|-----|------|------|
| `ok` | bool | Always `True` on success |
| `race` | str | Normalized race id |
| `racial_adjustments` | `dict[str, int]` | Per-attr racial mods (human: random +1 to two attrs) |
| `base_rolls` | `dict[str, int]` | 1d10 per **STR, AGI, STA, INT, SPI** only |
| `genetic_factors` | `dict[str, {"roll": int, "mod": int}]` | 1d4 → mod from `{1:-1, 2:0, 3:1, 4:2}` per STR–SPI |
| `life_event` | `{"roll": int, "name": str, "mods": dict[str, int]}` | 2d20 sum → event mods |
| `final_attributes` | `dict[str, int]` | **STR, AGI, STA, INT, SPI, LUC** after clamp `max(1, …)` |
| `eligible_classes` | `list[str]` | Tier-1 gates from final attrs |

### Per-column derivation (STR–SPI) for `format_roll_stats_table`

For each attr in `("STR", "AGI", "STA", "INT", "SPI")`:

| Column | Source |
|--------|--------|
| **Base** | `base_rolls[attr]` |
| **Genetic** | `genetic_factors[attr]["mod"]` |
| **Life Evt** | `life_event["mods"].get(attr, 0)` |
| **Racial** | `racial_adjustments.get(attr, 0)` |
| **Final** | `final_attributes[attr]` (authoritative; may differ from sum if clamp applied) |

### LUC row (special)

- **Final:** `final_attributes["LUC"]` — rolled as `max(1, 1d10 + genetic_mod)` in bridge (~139); **not** in `base_rolls` / `genetic_factors` dicts.
- Formatter should either show LUC with sparse intermediate columns (e.g. `—` for Base/Genetic/Life/Racial) or a documented single “rolled” column — PM/Dev should pick one row shape for APP-059 catalog.

### HP (not in roll payload)

- Computed at narrate time: `hp = 10 + final_attributes["STA"] * 5` — already in `_auto_roll_stats` (`orchestrator.py` ~934–935) and `_auto_finalize` (~1035–1036), `choice_memory` ROLL_STATS (~31–32).
- Canon: `build/systems/core/derived-stats.md` and `compute_hp()` in `play/tomb_gm/domain/character.py` (~108–110).

### Example return (structure)

```154:163:app/gm/bridge.py
        return {
            "ok": True,
            "race": race_key,
            "racial_adjustments": racial_mods,
            "base_rolls": base_rolls,
            "genetic_factors": genetic_rolls,
            "life_event": {"roll": life_roll, "name": life_name, "mods": life_mods},
            "final_attributes": attrs,
            "eligible_classes": eligible_classes,
        }
```

## Existing `format_*_table` patterns to mirror (APP-006)

All live in `app/gm/creation.py`: intro lines (rules), blank line, markdown header, aligned rows, `"\n".join(lines)`.

| Formatter | Lines | Columns |
|-----------|-------|---------|
| `format_races_table` | 544–555 | Race, Adjustments, Description |
| `format_classes_table` | 558–573 | Class, Requirement, Key skills, Starting GP |
| `format_skills_table` | 588–603 | Category, Skill, Class key? |
| `format_schools_table` | 361–381 | School, Tradition, Themes |
| `format_spells_table` | 384–404 | Spell, School, MP, Effect |

**Target `format_roll_stats_table`:** match ticket/LLM prompt headers: `Attr | Base | Genetic | Life Evt | Racial | Final`; prepend life event name from `life_event["name"]`; append HP line `**HP:** {hp} (10 + STA {sta} × 5)` using same formula as orchestrator.

**Presentation assembly (target):**

```507:524:app/gm/orchestrator.py
    def _compose_creation_narration(
        self,
        flavor: str,
        body: str = "",
        *,
        footer: str | None = None,
    ) -> str:
        """Thin LLM flavor + code body + code-owned status footer."""
        ...
```

Replace `_auto_roll_stats` tail (`orchestrator.py` ~937–956) with:

- `_narrate_flavor(_creation_flavor_messages("Present attribute roll results briefly…", player_input))`
- `body = format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)` (per ticket AC)
- `return self._compose_creation_narration(flavor, body)` with `creation.step` already `CLASS` → footer `CLASS_INPUT` via `format_creation_status`
- Set `classes_table_shown = True` when embedding class table (required for `_execute_creation_choice` CLASS guard ~1211–1213)

**Chain dedup:** `_chain_after_creation_choice` currently appends `_auto_present_class` after roll (`orchestrator.py` ~847–850). If `_auto_roll_stats` includes `format_classes_table`, dev should skip or slim `_auto_present_class` in that chain to avoid two class tables.

## HP formula `10 + STA×5` location

| Location | Reference |
|----------|-----------|
| Canon doc | `build/systems/core/derived-stats.md` — “HP = Base HP + (STA × 5)”, Base HP = 10 |
| Engine helper | `play/tomb_gm/domain/character.py` — `compute_hp(sta, *, base_hp=10)` |
| App roll narrate | `app/gm/orchestrator.py` ~934–935 (`_auto_roll_stats`), ~1035–1036 (`_auto_finalize`) |
| Memory blurbs | `app/gm/choice_memory.py` ~31–32 |
| System prompt | `app/gm/system_prompt.py` ~48 — table documents formula for LLM (flavor only after fix) |

## Test hooks in `test_creation_flow.py`

**File:** `app/tests/test_creation_flow.py`

| Hook | Detail |
|------|--------|
| `FIXED_ROLL` | Static dict (~5–21) — **shape drift:** `genetic_factors` uses `0` ints, not `{"roll", "mod"}` objects; `base_rolls` includes `LUC` though bridge does not |
| Monkeypatch | `orchestrator.bridge.roll_attributes` → lambda returning `{**FIXED_ROLL, "race": race}` (~35–40) |
| Turn 3 | Input `"human"` → expect `creation.step == "CLASS"` after roll chain (~26, ~44–47) |
| Mock LLM | `conftest.mock_openrouter_client` always `"Test narration."` — integration test does **not** catch wrong stat tables today |
| Gap (APP-067 AC) | After `"human"`, assert narration contains table cells from `FIXED_ROLL` (e.g. `| STR | 9 |` … `| 10 |` final) and HP `60` for STA 10; optional dedicated `test_format_roll_stats_table` |

**Suggested assertion targets (once formatter exists):**

- Header row `Attr | Base | Genetic | Life Evt | Racial | Final`
- Per-attr finals match `FIXED_ROLL["final_attributes"]`
- `**HP:**` or `HP` line with `10 + 10×5 = 60`
- `format_classes_table` eligible rows present once
- Update `FIXED_ROLL` to production `genetic_factors` shape before cell-level tests

**Commands:**

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
```

## Risks & unknowns

1. **Duplicate class table** — AC puts `format_classes_table` in `_auto_roll_stats` while chain still calls `_auto_present_class` (~847–850).
2. **LUC columns** — payload lacks per-step LUC breakdown; table row may look asymmetric.
3. **Column sum vs Final** — clamp `max(1, …)` in bridge (~136–137) can make Base+Genetic+Life+Racial ≠ Final; tests must assert **Final** from `final_attributes`, not recomputed sum.
4. **`FIXED_ROLL` shape** — test fixture does not match bridge; formatter tests need fixture update.
5. **Bridge vs engine duplication** — `GameBridge.roll_attributes` duplicates tables in `bridge.py`; `tomb_gm.domain.creation.run_creation_pipeline` is separate; unifying is out of ticket scope but long-term drift risk.
6. **Session evidence** — ticket cites `app/logs/session-2026-05-20.jsonl` (Bumpy STR 6 → narrated 7); file not grep-matchable in workspace during research — treat as anecdotal unless log restored.
7. **`get_step_prompt` / `system_prompt`** — still describe LLM-owned roll table; spec sync should note flavor-only after APP-067.
8. **`classes_table_shown`** — must be set when class table ships inside roll response or CLASS commits fail guard.

## Raw notes

- `_auto_roll_stats` docstring says “code rolls, LLM narrates the table” (`orchestrator.py` ~925) — misleading after fix.
- `get_step_prompt` for `ROLL_STATS` returns `""` (`creation.py` ~679–680) — dead for current code-first path.
- `tools.py` comment: `roll_attributes` removed from LLM tools (~65).
- APP-059 catalog has no `ROLL_STATS` row yet — ticket requires adding on close.
- Human playtest: Registry race pick → verify table math matches tool log / no STR off-by-one.
