# APP-012: Decision: LLM flavor during creation

| Field | Value |
|-------|-------|
| **ID** | APP-012 |
| **Type** | decision |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Open: thin LLM wrapper during creation vs zero LLM until WORLD_INTRO.

## Acceptance criteria

- [x] Document chosen approach in app-character-creation-spec.md.
- [x] Implement consistently in orchestrator.
- [x] Update APP-006/007/008 if zero-LLM path chosen.

## Expected files

- `app/gm/orchestrator.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
