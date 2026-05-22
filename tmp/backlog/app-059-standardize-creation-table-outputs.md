# APP-059: Standardize creation table outputs

| Field | Value |
|-------|-------|
| **ID** | APP-059 |
| **Type** | decision |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Character creation tables are **inconsistent**: race selection recently surfaced a **Description** column with long prose that **truncates the Race / Adjustments columns** in the PyGame narration panel (`render_table` fixed-width cells). Skills, schools, and spells use code `format_*_table()` helpers; **race and class** still mix LLM prompts with embedded markdown or prose lists. We need a **canonical table catalog** (columns + max content per step), documented in the domain spec, then **enforced in code** so every step emits the same shape every time.

## Problem (observed)

- **RACE step:** `get_step_prompt()` builds `| Race | Adjustments | Description |` inline from `RACES` — descriptions like *"Graceful and wise, excelling in arcane arts."* blow column widths; UI shows `..` truncation on race names.
- **CLASS step:** eligible classes as **prose bullets** (requirement + full description + kit) — not a table; inconsistent with SKILLS/SCHOOLS/SPELLS.
- **SKILLS / SCHOOLS / SPELLS:** have `format_*_table()` but no shared column-length contract or tests.
- **EQUIPMENT_GOLD:** `format_equipment_summary()` owns kit/GP in the code **body**, but LLM **flavor** still invents contradictory economics. Session 2026-05-20 (Fatty / Undead Novice): flavor said *"Standard delver's kit and **fifty gold pieces**"* while the code block showed **`Starting gold: 5 gp`** (engine correct: `(15 base − 10 Severe Injury) × gold_roll 1`; kit cost 39 gp → 0 gp after finalize). Root cause: `_auto_present_equipment` prompt invites *"coin pouch"* talk; no equipment-specific sanitizer (unlike APP-072 race tables / APP-073 stats tables).
- **UI:** `app/ui/rich_text.py` `render_table()` scales columns to panel width and **truncates** overflow — table authors must design for narrow narration column (~70% window).

## Acceptance criteria

### Decision (document in domain spec § Creation tables)

- [ ] **Table catalog** added to `app-character-creation-spec.md` — one subsection per gated step listing: formatter name, columns, what belongs in-table vs clerk flavor prose, max cell length guidance.
- [ ] **RACE table decision recorded** — recommended: **Race + Adjustments only** (no Description column); lore/flavor stays in optional LLM intro (≤2 sentences), not in cells. Alternative (if chosen): one-line description cap (e.g. ≤40 chars) documented.
- [ ] **CLASS table decision recorded** — recommended: markdown table `Class | Req | Key skills` (kit/GP deferred to EQUIPMENT step).
- [ ] **SPELLS Effect column** — cap or abbreviate long effect text so MP/School columns stay readable.
- [ ] **EQUIPMENT_GOLD flavor contract** documented in domain spec § Creation tables — flavor banter only; GP/kit authoritative in `format_equipment_summary` body; `strip_flavor_equipment_claims` sanitizer contract.

### Code enforcement

- [ ] `format_races_table()` in `creation.py` — sole source for race step body (remove inline table from `get_step_prompt`).
- [ ] `format_classes_table(eligible_classes, attrs)` — sole source for class step body.
- [ ] `format_equipment_summary(state)` — kit name + starting GP + confirm instruction (align with APP-006). Body already code-owned; ticket closes the **flavor leak** below.
- [ ] **EQUIPMENT_GOLD flavor contract** — `_auto_present_equipment` instruction: clerk banter only; **do not** mention kit contents, coin pouches, GP amounts, or item lists (code appends `format_equipment_summary`).
- [ ] **EQUIPMENT_GOLD flavor contract** — verify via APP-083 `gold_mismatch` + optional `strip_flavor_equipment_claims` defense-in-depth (not required if verify green in tests).
- [ ] Shared helper or constants for **column validation** (max lengths, optional `assert_table_contract()` in tests).
- [ ] Orchestrator `_auto_present_*` / `_creation_turn` append **code tables only** for RACE and CLASS (same pattern as SKILLS/SCHOOLS/SPELLS).
- [ ] Optional: `validate_table_cell_lengths()` logs/warns in dev if a formatter exceeds spec caps.

### UI / display

- [ ] Manual check: race + class tables readable at 1280×800 without truncating primary pick column (Race name / Class name).
- [ ] If catalog requires wider tables, document minimum narration width or adjust `render_table` column priority (primary column gets weight) — change scoped in ticket **Expected files**.

### Tests

- [ ] `app/tests/test_creation_tables.py` (or extend `test_creation_flow.py`) — golden snapshots per `format_*_table()` output: header row, column count, no Description column on race (per decision), cell length limits.
- [ ] `test_strip_flavor_equipment_claims_unit` — flavor with *"fifty gold pieces"*, *"5 gp pouch"*, kit item lists stripped; benign clerk banter retained.
- [ ] Integration: equipment step composed narration — flavor region has no `\d+\s*(gp|gold|coin)` when body contains `**Starting gold:**`; body GP matches `creation.starting_gold`.

## Expected files

- `app/gm/creation.py`
- `app/gm/orchestrator.py`
- `app/ui/rich_text.py` _(only if column priority / wrap behavior changes)_
- `app/tests/test_creation_tables.py`
- `app/tests/test_creation_flavor_sanitize.py` _(extend with equipment-claim strip tests)_
- `tmp/app-character-creation-spec.md`
- `tmp/app-pygame-ui-spec.md` _(optional: § Table rendering constraints)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add **§ Creation tables** to [`app-character-creation-spec.md`](../app-character-creation-spec.md) with final catalog + changelog.
3. Cross-link from [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) if render rules change.

## Notes

### Proposed catalog (starting point for PM/decision — not final until spec updated)

| Step | Formatter | In-table columns | Out of table (flavor / later steps) |
|------|-----------|------------------|--------------------------------------|
| RACE | `format_races_table()` | Race, Adjustments | Race lore, Registry clerk banter |
| CLASS | `format_classes_table()` | Class, Requirement, Key skills | Class fantasy blurb, kit detail → equipment |
| SKILLS | `format_skills_table()` | Category, Skill, Key? | Pick rules in intro lines (existing) |
| SPELL_SCHOOLS | `format_schools_table()` | School, Tradition, Themes | Pick rules in intro lines |
| SPELLS | `format_spells_table()` | Spell, School, MP, Effect (short) | Full spell text in canon docs only |
| EQUIPMENT_GOLD | `format_equipment_summary()` | Kit, Starting GP, Confirm prompt | Clerk color commentary **only** — no GP/kit prose |

### EQUIPMENT_GOLD flavor must not duplicate code summary (APP-059)

Observed failure: LLM flavor invents GP (*"fifty gold pieces"*) while `format_equipment_summary` shows authoritative `**Starting gold:** N gp`.

**Defense in depth** (same pattern as APP-072 RACE / APP-073 ROLL_STATS):

| Layer | Locus | Behavior |
|-------|-------|----------|
| Prompt | `_auto_present_equipment` instruction | “Brief clerk banter only — do not mention kit contents, gold amounts, or GP; code appends the Registry kit summary.” |
| Global prompt | `_creation_flavor_messages` | “Do NOT include … mechanical numbers” (existing; insufficient alone) |
| Post-sanitize | `_compose_creation_narration` | `strip_flavor_equipment_claims(cleaned)` on **flavor only** before body append |

**Composed EQUIPMENT_GOLD contract:** exactly **one** kit/GP block — from `format_equipment_summary` body, never from flavor. Flavor may ask for confirmation in prose (*"sign here?"*) but must not state amounts or enumerate gear.

**`strip_flavor_equipment_claims` sketch:** drop lines/sentences matching GP/gold/coin/pouch/kit-list patterns (e.g. `\bfifty gold\b`, `\d+\s*gp\b`, `\bgold pieces\b`, `\bcoin pouch\b`, `\bRegistry kit\b` in flavor); collapse blank lines; empty → `""`.

### Related tickets

| Ticket | Relationship |
|--------|--------------|
| [APP-006](app-006-deterministic-creation-tables-from-code.md) | Overlaps — APP-006 owns wiring code-first tables; APP-059 owns **schema + column contract**. Implement together or APP-059 immediately after APP-006. |
| [APP-007](app-007-code-owned-creation-status-line.md) | Same presentation pattern (code body, LLM flavor only). |
| [APP-072](app-072-llm-truncation-race-tables.md) / [APP-073](app-073-strip-llm-embedded-status-tags-in-creation.md) | Prior art for step-specific flavor strippers (`strip_flavor_race_table`, `strip_flavor_stats_table`). |
| [APP-078](app-078-generic-creation-table-flavor-stripper.md) | **Cancelled** — APP-083 verify handles duplicate tables; optional strip only if verify gaps |
| [APP-083](app-083-creation-flavor-verification-gate.md) | Phase 1 verify covers `gold_mismatch`, `markdown_table`, off-catalog schools/spells — prefer verify over new strippers |
| [APP-079](app-079-finish-reason-length-recovery-policy.md) | Central `finish_reason: length` policy when truncated tables slip through |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-059 --task standardize-creation-tables
python tmp/backlog/claim_ticket.py release APP-059 --done
```
