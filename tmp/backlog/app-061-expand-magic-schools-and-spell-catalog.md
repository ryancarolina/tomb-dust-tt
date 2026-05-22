# APP-061: Expand magic schools and spell catalog

| Field | Value |
|-------|-------|
| **ID** | APP-061 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`build/systems/magic/schools.md`](../../build/systems/magic/schools.md) |
| **Created** | 2026-05-20 |

## Summary

The spell catalog is **thin and uneven**: **6 schools**, **41 spells** in [`build/data/spells/spells.json`](../../build/data/spells/spells.json), with **only 1 tier-1 spell** each for Pyromancy and Ward (others have 2). Character creation and delver progression need **more schools** and **more spells per school** across tiers so casters have meaningful picks at creation and as class tier rises. Canon lives in **`build/systems/magic/`** + JSON data — not app code alone.

## Current baseline (2026-05-20)

| School | Spells (total) | Tier 1 |
|--------|----------------|--------|
| pyromancy | 7 | 1 |
| ward | 6 | 1 |
| biomancy | 7 | 2 |
| necromancy | 7 | 2 |
| ether | 7 | 2 |
| divine | 7 | 2 |

**Data:** `build/data/spells/schools.json`, `spells.json` · **Rules:** `build/systems/magic/schools.md`, `spells.md` · **Validation:** `python build/tools/validate_content.py` · **Creation:** `build/data/character/starting-spells.json`, [`tmp/app-character-creation-spec.md`](../app-character-creation-spec.md).

## Acceptance criteria

### Design (document in canon before bulk authoring)

- [ ] **Target school list** approved in `schools.md` — which **new schools** to add (names, ids, tradition arcane/divine, themes, typical AV-GRID/site ties).
- [ ] **Per-school spell targets** documented — e.g. minimum **3 tier-1**, **2+ tier-2**, **1+ tier-3** per school (adjust in spec if product wants different bands up to tier 6).
- [ ] Spells follow **d20 canon**: spell attack vs AC, save DC per [`build/systems/combat/calculations.md`](../../build/systems/combat/calculations.md), MP/tier gating per [`build/systems/magic/README.md`](../../build/systems/magic/README.md).
- [ ] No orphan spells — every `school` id in `spells.json` exists in `schools.json`.

### Data + docs

- [ ] New/updated entries in `build/data/spells/schools.json` (schema: `build/data/schemas/school.schema.json`).
- [ ] New/updated entries in `build/data/spells/spells.json` (schema: `build/data/schemas/spell.schema.json`).
- [ ] [`build/systems/magic/schools.md`](../../build/systems/magic/schools.md) — school table + arcane/divine rules updated.
- [ ] [`build/systems/magic/spells.md`](../../build/systems/magic/spells.md) — full catalog tables synced with JSON (tier 1–3 minimum; higher tiers as scoped).
- [ ] [`build/systems/magic/README.md`](../../build/systems/magic/README.md) — spell count / changelog note.

### Validation + play integration

- [ ] `python build/tools/validate_content.py` exits 0.
- [ ] `python -m pytest play/tomb_gm/tests` green (spell/school references in tests, if any).
- [ ] Creation spell/school pick tables (`format_schools_table`, `format_spells_table` in `app/gm/creation.py`) still work with expanded catalog — update if new schools need creation filters in `starting-spells.json`.
- [ ] Tier-1 pool large enough that Apprentice/Novice **2-spell pick** feels varied (no school with only one tier-1 option after expansion).

## Expected files

- `build/data/spells/schools.json`
- `build/data/spells/spells.json`
- `build/data/character/starting-spells.json` _(if school pick rules change)_
- `build/systems/magic/schools.md`
- `build/systems/magic/spells.md`
- `build/systems/magic/README.md`
- `build/tools/validate_content.py` _(only if new school ids / enums need validator updates)_
- `tmp/app-character-creation-spec.md` _(if creation pick rules or table copy changes)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update magic canon docs + dated note in `schools.md` or `README.md` changelog.
3. If creation behavior changes, update [`tmp/app-character-creation-spec.md`](../app-character-creation-spec.md).

## Notes

### Candidate new schools _(decision — not canon until approved)_

Examples to evaluate against setting (Ether, Registry, extraction tone):

- **Cryomancy** / **Geomancy** / **Illusion** / **Transmutation** / **Conjuration** — pick ids, traditions, and site ties that do not duplicate existing six themes.
- Or ** deepen existing six** first (more spells per school) before adding schools — PM/design choice recorded in ticket close notes.

### Authoring rules

- Use existing spell entries in `spells.json` as templates (`effectType`, `attack`, `save`, `heal`, etc.).
- Prefer terse **effect** strings for creation UI tables ([APP-059](app-059-standardize-creation-table-outputs.md)).
- Divine tradition only for `divine` school unless a class feature says otherwise (`schools.md`).

### Related tickets

| Ticket | Relationship |
|--------|--------------|
| APP-059 | Table display — keep spell Effect column short |
| APP-006 | Creation tables pull from this catalog |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-061 --task expand-magic-schools-spells
python tmp/backlog/claim_ticket.py release APP-061 --done
```
