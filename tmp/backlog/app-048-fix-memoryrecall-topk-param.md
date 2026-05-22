# APP-048: Fix memory_recall top_k param

| Field | Value |
|-------|-------|
| **ID** | APP-048 |
| **Type** | bug |
| **Priority** | P2 |
| **Status** | done |
| **Domain spec** | [`app-gamebridge-spec.md`](../app-gamebridge-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

memory_recall param names may not match engine (top_k broken).

## Acceptance criteria

- [x] memory_recall uses top_k matching engine contract.

## Expected files

- `app/gm/bridge.py`
- `app/gm/tools.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-gamebridge-spec.md`](../app-gamebridge-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Implemented:** `bridge.memory_recall(query, top_k=5)` passes `top=top_k` to `recall_facts()`. Tool schema exposes `top_k` in `tools.py`.
