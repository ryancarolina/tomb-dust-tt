# APP-033: SQLite threading policy

| Field | Value |
|-------|-------|
| **ID** | APP-033 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Multi-thread access to GameBridge may corrupt SQLite.

## Acceptance criteria

- [ ] Single connection per process OR thread-local GameBridge documented and enforced.

## Expected files

- `app/gm/bridge.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
