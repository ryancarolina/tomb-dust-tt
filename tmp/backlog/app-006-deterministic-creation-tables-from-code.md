# APP-006: Deterministic creation tables from code

| Field | Value |
|-------|-------|
| **ID** | APP-006 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

LLM-generated skill/school/spell tables drift from canon.

## Acceptance criteria

- [x] Code appends format_skills_table(), format_schools_table(), format_spells_table().
- [x] Kit/GP from ensure_equipment_gold(); not LLM prose.

## Expected files

- `app/gm/creation.py`
- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-006-creation-hardening-006-012`

_Add implementation notes, blockers, or PR links here._
