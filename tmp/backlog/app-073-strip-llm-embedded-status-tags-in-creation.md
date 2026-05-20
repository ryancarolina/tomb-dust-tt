# APP-073: Strip LLM-embedded status tags and mechanical tables during creation

| Field | Value |
|-------|-------|
| **ID** | APP-073 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

APP-007 added code-owned footers and a partial `strip_llm_status_tags()`, but GM **flavor** during creation still leaks machine status and **code-owned mechanical output** into player-facing narration:

1. **Status tags** — `[Location: … | Phase: …]` blocks and wrong `Awaiting:` labels (`SKILL_INPUT`, `MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION`) confuse UI chips (APP-065) and `creation_drift` logs.
2. **Duplicate stat tables (ROLL_STATS → CLASS)** — `_auto_roll_stats()` rolls in code and appends `format_roll_stats_table()`, but the LLM flavor call still invents attribute tables (`### Your Attributes`, compact `\| STR \| AGI \| … \|`) with **wrong numbers**. Same class of bug as APP-072 (duplicate race tables); model swap (Gemini 2.5 Flash → 3.1 Flash Lite) does **not** fix it.

**Root cause:** `_compose_creation_narration(flavor, body)` concatenates flavor + code body; stripper is too narrow (line-anchored `Awaiting:` only; no stat-table strip). Flavor cap is 120 tokens — models often hit `finish_reason: length` mid-table anyway.

**Goal:** Flavor is prose only; **one** code-owned footer (`format_creation_status`) and **one** mechanical table per step (stats, races, classes, etc.) from `format_*` helpers.

## Evidence (session log)

**Status tags (historical):**

- Early Dumpy: full bracket status in every line (~14:06–14:10).
- Supa `16:13:11`: `Awaiting: SKILL_INPUT` (should be `SKILLS_INPUT` per `CREATION_STATUS_LABELS`).
- Bumpy: `MAGIC_SCHOOLS_INPUT` vs code `SPELL_SCHOOLS_INPUT`; `EQUIPMENT_CONFIRMATION` vs `EQUIPMENT_GOLD_CONFIRMATION`.
- Later code path: footer-only `Awaiting: NAME_INPUT` but `narrated_phase: null` in drift — tags partially stripped.

**Duplicate stat tables (repro — `session-2026-05-20.jsonl`):**

- Spluffy / Undead @ 18:50 (`gemini-2.5-flash`): LLM `### Your Attributes` (STR 11, STA 16, …) + code breakdown (STR 9, STA 2, …); `finish_reason: length`.
- Tuffy / Undead @ 19:02 (`gemini-3.1-flash-lite`): LLM compact stat row (STR 14, STA 16, …) + fragment `` `roll_attributes(race `` + code breakdown (STR 9, STA 8, …); tool_call `roll_attributes` is authoritative.

## Acceptance criteria

### Status tags (complete APP-007)

- [x] `strip_llm_status_tags()` removes bracket `[Location:…]` and `[Phase:…]` anywhere in flavor (including combined bracket blocks).
- [x] Remove **any** `Awaiting:` in flavor text (not only whole-line `^\s*Awaiting:…$` matches); player-facing narration has **exactly one** `Awaiting:` from `format_creation_status()` at the end.
- [x] `_compose_creation_narration` remains the sole composer of footer + mechanical **body**; flavor after sanitizers is prose-only (no status lines, no duplicate tables).
- [x] Prompts / flavor instructions do not teach non-canonical labels (`SKILL_INPUT`, `MAGIC_SCHOOLS_*`, `EQUIPMENT_CONFIRMATION`); canon is `CREATION_STATUS_LABELS` in `creation.py`.

### Stat / mechanical table leak (ROLL_STATS and similar)

- [x] Add `strip_flavor_stats_table()` (or equivalent) in `creation.py`, mirroring APP-072 `strip_flavor_race_table()`: strip from flavor markdown stat blocks including `### Your Attributes`, `\| Attr \| Base \|`, compact attribute header rows (`\| STR \| AGI \| STA \| … \|`), and truncated tool-call fragments (e.g. `` `roll_attributes( ``).
- [x] Wire sanitizer in `_compose_creation_narration` after `strip_flavor_race_table` (flavor path only; never strip code **body**).
- [x] **ROLL_STATS → CLASS** narration shows **one** attribute breakdown (from `format_roll_stats_table`) and numbers match `roll_attributes` / `creation.roll_result`.
- [x] Acceptable alternative for ROLL_STATS: skip LLM flavor entirely for that step (code-only intro line + tables) — if chosen, document in spec and test. _(Default path: thin flavor + stats strip — implemented.)_

### Tests

- [x] Test: mocked flavor with embedded `[Phase:…]`, inline `Awaiting: SKILL_INPUT`, and fake stat table → composed output has single canonical footer, no duplicate `\| Attr \|` / `\| STR \|` blocks in flavor region.
- [x] Test: ROLL_STATS compose path with stat-table flavor fixture → only code table values appear in final narration.

## Expected files

- `app/gm/creation.py` — `strip_llm_status_tags`, new `strip_flavor_stats_table`, tests import surface
- `app/gm/orchestrator.py` — `_compose_creation_narration` pipeline; optional `_auto_roll_stats` flavor prompt tighten
- `app/tests/test_creation_flavor_sanitize.py` _(new)_ or extend existing creation test module
- `tmp/app-character-creation-spec.md` — compose pipeline + changelog; close APP-007 note

**Out of scope (separate tickets):** APP-065 chip source-of-truth / stale clear (`app/ui/app.py`); APP-059 table standardization.

## Implementation notes (for Dev)

**Compose order (flavor, after change):**

`strip_llm_status_tags` → `strip_flavor_race_table` (APP-072) → **`strip_flavor_stats_table` (APP-073)** → `_sanitize_creation_flavor` (APP-069) → `sanitize_premature_completion_flavor` (APP-070) → append code `body` + `format_creation_status` footer.

**`_auto_roll_stats` prompt:** Flavor instruction must say clerk reaction only — **do not** present numbers, HP, or markdown tables (code appends roll readout).

**Trust model:** Engine `roll_attributes` + `format_roll_stats_table` only; never merge LLM-invented scores.

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update [`app-character-creation-spec.md`](../app-character-creation-spec.md): compose pipeline, ROLL_STATS flavor policy, changelog — note APP-007 footer/strip behavior **completed** by APP-073.
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Related:** APP-007 (incomplete strip), APP-065 (chips), APP-066 (engine vs app awaiting), APP-070 (premature completion prose), APP-072 (race table strip — template for stats).  
**Implement before or with APP-065** so narration is clean before chip hardening.  
**Session:** `app/logs/session-2026-05-20.jsonl` (Spluffy 18:50, Tuffy 19:02).
