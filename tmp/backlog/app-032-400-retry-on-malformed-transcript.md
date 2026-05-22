# APP-032: 400 retry on malformed transcript

| Field | Value |
|-------|-------|
| **ID** | APP-032 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Single malformed transcript kills session.

## Acceptance criteria

- [x] On malformed transcript 400, repair/truncate history and retry once.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_transcript_400_retry.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Grooming 2026-05-20:** Bumped P1 — single malformed transcript currently kills the turn loop with no repair. Pair with APP-031 and APP-080 (arg normalization).
