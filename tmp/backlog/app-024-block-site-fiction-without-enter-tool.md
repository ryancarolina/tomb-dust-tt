# APP-024: Block site fiction without enter tool

| Field | Value |
|-------|-------|
| **ID** | APP-024 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-21 |

## Summary

LLM narrates site entry without successful enter_dungeon.

## Acceptance criteria

- [x] Block site-entry fiction on surface unless the **current turn's tool chain** includes a successful (`ok: true`) `enter_dungeon` or `site_enter`.
- [x] Entry commit is **not** revoked by a later failed retry of the same entry tool or other failed tools in the same turn (sticky per-turn flag or full-chain scan — not final `_last_tool_results` slot).

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_exploration_site_entry_gate.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-024-block-site-fiction`

_Add implementation notes, blockers, or PR links here._
