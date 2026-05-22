# APP-008: Hard gate exploration during creation

| Field | Value |
|-------|-------|
| **ID** | APP-008 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

Orchestrator ran _llm_loop / exploration tools while creation.active, causing drift.

## Acceptance criteria

- [x] No _llm_loop or exploration tools while creation.active (except FINALIZE/WORLD_INTRO).
- [x] Cross-ref app-llm-orchestrator-spec.md.

## Expected files

- `app/gm/orchestrator.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
