# APP-016: Snapshot engine status on save

| Field | Value |
|-------|-------|
| **ID** | APP-016 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-20 |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |

## Summary

App save should include engine truth for reconcile on load.

## Acceptance criteria

- [x] On save, snapshot engine status() alongside app state.

## Expected files

- `app/ui/app.py` — `_save_session()` / `engine_status` snapshot
- `app/tests/` — T4a–d (save includes `engine_status`; legacy load; failure omit)
- `tmp/app-session-persistence-spec.md` — § Engine status snapshot on save (APP-016)

**Batch (not APP-016 impl):** `app/gm/orchestrator.py` — stale `engine_status` clear on **`new game`** is **APP-015** (C2 / T-015d).

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-session-persistence-spec.md`](../app-session-persistence-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-016-snapshot-engine-status-on-save`

_Add implementation notes, blockers, or PR links here._
