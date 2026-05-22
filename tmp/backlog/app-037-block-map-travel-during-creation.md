# APP-037: Block map travel during creation

| Field | Value |
|-------|-------|
| **ID** | APP-037 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Map panel in the right sidebar allows travel clicks during **character creation**, conflicting with APP-008 (exploration hard-gated in orchestrator). UI should disable map travel while `creation.active`.

## Acceptance criteria

- [x] Map travel input disabled (greyed / no-op) when `creation.active` or engine `awaiting` is creation-scoped.
- [x] Tooltip or label: *"Finish Registry intake first"* (or similar).
- [x] Re-enable after creation finalize / live delver on surface.
- [x] Map still **displays** current hub cell if useful — only **travel actions** blocked.
- [x] Compatible with [APP-062](app-062-left-character-panel-inventory-spells-tabs.md) narrowed map column width.

## Expected files

- `app/gm/orchestrator.py`
- `app/ui/panels/map_view.py`
- `app/ui/panels/sidebar.py`
- `app/ui/app.py`
- `app/tests/test_ui_map_creation_gate.py`
- `tmp/app-pygame-ui-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update domain spec + changelog.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-008 | engine gate — UI must mirror (defense in depth) |
| APP-062 | layout — map lives in right sidebar; test resize |
| APP-063 | soft — map UX redesign may follow; travel block still required during creation |

## Notes

- Orchestrator already rejects exploration during creation; this ticket prevents confusing UI affordances.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-037 --task block-map-during-creation
python tmp/backlog/claim_ticket.py release APP-037 --done
```
