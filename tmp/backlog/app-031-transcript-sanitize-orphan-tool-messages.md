# APP-031: Transcript sanitize orphan tool messages

| Field | Value |
|-------|-------|
| **ID** | APP-031 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Orphan tool messages without preceding tool_calls cause API 400.

## Acceptance criteria

- [x] Sanitize transcript: no orphan tool messages without preceding tool_calls.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_transcript_sanitize.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Grooming 2026-05-20:** Bumped P1 — session `2026-05-20` showed fragile multi-tool turns (e.g. corrupted `remember_fact` args leaving orphan tool messages). Pair with APP-032.
