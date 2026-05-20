# APP-007: Code-owned creation status line

| Field | Value |
|-------|-------|
| **ID** | APP-007 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

LLM [Location: ...] tags mislead UI during creation.

## Acceptance criteria

- [x] format_creation_status(creation) drives status line.
- [x] Strip LLM [Location: ...] blocks from player-facing output.

## Expected files

- `app/gm/creation.py`
- `app/ui/`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
