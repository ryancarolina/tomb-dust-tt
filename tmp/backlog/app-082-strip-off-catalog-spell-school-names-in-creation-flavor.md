# APP-082: Strip off-catalog spell picks from creation flavor (schools + spells steps)

| Field | Value |
|-------|-------|
| **ID** | APP-082 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | cancelled |
| **Superseded by** | [APP-083](app-083-creation-flavor-verification-gate.md) (game-wide narration gate; creation Phase 1) |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-21 |

## Summary

During **`SPELL_SCHOOLS`** and **`SPELLS`**, thin LLM flavor above code-owned `format_schools_table()` / `format_spells_table()` bodies invents **off-catalog school names**, **fake spell groupings**, and **duplicate markdown pick tables**. Players see conflicting lists above the authoritative table and may type invalid choices.

Add creation-flavor sanitizers (mirroring `strip_flavor_equipment_claims` / APP-073 table strippers) that strip invented spell/school pick content when the code body already supplies the step table.

## Problem (observed)

**Session:** `app/logs/session-2026-05-21.jsonl` — real play, character **Sumpty** (Undead Novice; schools **Divine + Ward**).

### `SPELL_SCHOOLS` — prose school catalog drift

| When | What happened |
|------|---------------|
| `2026-05-21T16:43:15` (L4743) | LLM flavor: *"eight known schools: **Restoration, Transmutation, Divination, Evocation, Abjuration, Conjuration, Necromancy, Enchantment.**"* |
| Same turn (code body) | Correct table: Pyromancy, Ward, Biomancy, Necromancy, Ether, Divine (`Choose **Divine** plus **1 other school**`) |

**Invalid names in flavor (7/8):** Restoration, Transmutation, Divination, Evocation, Abjuration, Conjuration, Enchantment.  
**Only overlap:** Necromancy (still wrong framing — "eight schools" vs Novice rule).

Player later picked **`Divine, Ward`** (valid) @ `16:46:44` — validation worked despite bad flavor.

### `SPELLS` — invented school groupings + duplicate spell table

| When | What happened |
|------|---------------|
| `2026-05-21T16:46:47` (L4748–4749) | LLM `finish_reason: length`; flavor embeds fake `\| School \| Spells \|` table |
| Flavor content | **Restoration** → mend-light, cleanse-wound · **Communion** → detect-undead, sense-vitality · **Warding** → consecrate-ground, … (truncated) |
| Code body | Correct `\| Spell \| School \| MP \| Effect \|` table: Mend Light, Consecrate Ground (divine), Aegis Spark (ward) |

**Invalid school labels in flavor:** Restoration, Communion, Warding (none are Tomb Dust school ids).  
**Spell id drift:** `cleanse-wound`, `detect-undead`, `sense-vitality` are not in the code table; `mend-light` / `consecrate-ground` appear under wrong invented school headers.

### Root cause

`_compose_creation_narration` strips race/stats markdown tables and (target) generic markdown tables (APP-078), but has **no guard** for:

1. **Prose school enumerations** on `SPELL_SCHOOLS`.
2. **Alternate spell-pick markdown tables** and **off-catalog school groupings** on `SPELLS`.

Both `_auto_present_schools` and `_auto_present_spells` call `_creation_table_flavor(...)` with no negative constraint and no post-sanitize pass keyed to `eligible_schools_for_class()` / `tier1_spells_for_schools()`.

**Scope note:** APP-078 covers duplicate markdown tables that **mirror the code header fingerprint**. This ticket additionally covers **prose school lists**, **non-matching table schemas** (e.g. `\| School \| Spells \|`), and **off-catalog tokens** — implement as step-aware strippers; APP-078 remains a useful backstop for exact-header duplicates.

## Acceptance criteria

### Decision (document in domain spec)

- [ ] On `SPELL_SCHOOLS`, when `body` contains `\| School \| Tradition \| Themes \|`, flavor must **not** name any spell school outside `eligible_schools_for_class(chosen_class)`.
- [ ] On `SPELLS`, when `body` contains `\| Spell \| School \| MP \| Effect \|`, flavor must **not** contain alternate spell-pick tables, invented school→spell groupings, or spell ids not in `tier1_spells_for_schools(chosen_school_ids)`.
- [ ] Flavor may retain clerk banter that does **not** enumerate picks (e.g. *"Which traditions call to you?"*). Removing flavor that is only an invented catalog/table is acceptable.
- [ ] Code `body` and `format_creation_status()` footer unchanged; sanitizers run on **flavor only**.

### Code

#### Schools step

- [ ] Add `strip_flavor_school_claims(text: str, *, allowed_display_names: set[str], allowed_ids: set[str]) -> str` in `app/gm/creation.py`:
  - Remove sentences/clauses that enumerate schools (`**Name, Name, …**`, *"listing the N known schools"*, etc.).
  - Strip off-catalog tokens from a denylist seeded with session repro: Restoration, Transmutation, Divination, Evocation, Abjuration, Conjuration, Enchantment, Communion, Warding (extensible).
  - Collapse blank lines; empty → `""`.

#### Spells step

- [ ] Add `strip_flavor_spell_pick_claims(text: str, *, allowed_spell_ids: set[str], allowed_school_ids: set[str]) -> str` in `app/gm/creation.py`:
  - Remove markdown blocks with spell-pick schemas not owned by code (e.g. `\| School \| Spells \|`, grouped spell lists under invented school headers).
  - Strip `\| Spell \|`-style table blocks from flavor when `body` already supplies the code spell table (including truncated tables with no separator row — mirror APP-072).
  - Remove or neutralize off-catalog spell ids in flavor when not in `allowed_spell_ids`.
  - Collapse blank lines; empty → `""`.

#### Wiring

- [ ] Wire both into `_compose_creation_narration` **after** `strip_flavor_stats_table`, **before** `_sanitize_creation_flavor`:
  - `SPELL_SCHOOLS`: `strip_flavor_school_claims` with `eligible_schools_for_class(chosen_class)`.
  - `SPELLS`: `strip_flavor_spell_pick_claims` with `creation.chosen_school_ids` + `tier1_spells_for_schools(...)`.
- [ ] Optional hardening: tighten `_creation_flavor_messages` for both steps — *"Do not list school or spell names; the Registry table below is authoritative."*
- [ ] Do **not** change `format_schools_table()`, `format_spells_table()`, or validation helpers.

### Tests

- [ ] Unit (schools): session repro L4743 flavor → no Restoration/Evocation/Abjuration/etc.; non-enumerating clerk prose retained.
- [ ] Unit (spells): session repro L4749 flavor → no `\| School \| Spells \|`, no Restoration/Communion/Warding, no `cleanse-wound`/`detect-undead`; clerk grimoire line may remain.
- [ ] Unit: benign flavor without lists/tables unchanged on both steps.
- [ ] Unit: truncated spell table in flavor (no separator row) fully stripped.
- [ ] Integration: golden path Novice to `SPELL_SCHOOLS` then `SPELLS` — exactly one school table and one spell table in full narration (from code body); no off-catalog school name or alternate spell-pick table in flavor portions.

## Expected files

- `app/gm/creation.py`
- `app/gm/orchestrator.py`
- `app/tests/test_creation_flavor_sanitize.py` (or extend existing APP-073 sanitize tests)
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add § **`strip_flavor_school_claims`** and § **`strip_flavor_spell_pick_claims`** to flavor sanitization pipeline in [`app-character-creation-spec.md`](../app-character-creation-spec.md); update compose-order diagram.
3. Add session repro to spec evidence / regression table (Sumpty @ `16:43:15` schools, `16:46:47` spells).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-073 | compose pipeline hook point; flavor-only sanitizer pattern |
| APP-078 | soft hint — backstop for exact-header duplicate tables; safe in either order |
| APP-059 | equipment GP strip pattern — mirror for spell pick claims |
| APP-079 | soft hint — `finish_reason: length` truncated spell table on L4748 |

## Notes

### Compose order (target)

```
strip_llm_status_tags
→ strip_flavor_race_table
→ strip_flavor_stats_table
→ strip_flavor_school_claims (SPELL_SCHOOLS body)        # APP-082
→ strip_flavor_spell_pick_claims (SPELLS body)          # APP-082
→ strip_flavor_markdown_tables (body=body)               # APP-078
→ strip_flavor_equipment_claims                          # APP-059
→ _sanitize_creation_flavor
→ sanitize_premature_completion_flavor
→ body + footer
```

### Non-goals

- Expanding the spell school or spell catalog (APP-061).
- Changing LLM model or removing creation flavor entirely (APP-012 decision stands).
- Sanitizing spell/school names in exploration or combat narration.

### Repro excerpts

**L4743 — `SPELL_SCHOOLS` flavor leaked:**

> She slides a reference sheet across the desk listing the eight known schools: **Restoration, Transmutation, Divination, Evocation, Abjuration, Conjuration, Necromancy, Enchantment.**

**L4749 — `SPELLS` flavor leaked:**

> Here are your options:
>
> | School | Spells |
> | **Restoration** | mend-light, cleanse-wound |
> | **Communion** | detect-undead, sense-vitality |
> | **Warding** | consecrate-ground, …

**Code bodies (authoritative):** school table with Pyromancy…Divine; spell table with Mend Light, Consecrate Ground, Aegis Spark.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-082 --task strip-off-catalog-spell-picks-in-creation-flavor
python tmp/backlog/claim_ticket.py release APP-082 --done
```
