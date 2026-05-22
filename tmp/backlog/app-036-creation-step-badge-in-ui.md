# APP-036: Creation step badge in UI

| Field | Value |
|-------|-------|
| **ID** | APP-036 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

During `creation.active`, the player cannot see the current FSM step in the UI except via code-owned `Awaiting:` footer in narration. Add a **creation step badge** sourced from **`creation_state` / engine** — not LLM tags.

## Acceptance criteria

- [x] Visible badge (or sidebar label) while `creation.active` showing current step (e.g. `RACE`, `SKILLS`) using human label from `CREATION_STATUS_LABELS` or equivalent.
- [x] Badge hidden after creation completes / roster live.
- [x] Data from orchestrator session / `engine_status` — never scraped from narration (APP-065 chip policy).
- [x] Placement works with [APP-062](app-062-left-character-panel-inventory-spells-tabs.md) three-column layout (suggest: right sidebar above stats, or narration header strip).

## Expected files

- `app/gm/creation.py` — `CREATION_STEP_DISPLAY` (step-keyed human labels; not footer tokens)
- `app/gm/orchestrator.py` — `get_creation_step_badge()`
- `app/ui/panels/stats.py` — Registry badge at top of stats region
- `app/ui/panels/sidebar.py` — cache + re-apply badge on `_do_layout` resize (APP-037 mirror)
- `app/ui/app.py` — extend `_enrich_status_for_ui`
- `app/tests/test_ui_creation_badge.py`
- `app/tests/test_ui_map_creation_gate.py` — mock `get_creation_step_badge.return_value = None` in enrich regression test
- `tmp/app-pygame-ui-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update domain spec + changelog.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-062 | layout — implement after or with left panel so badge position is stable |
| APP-035 | related — both panels must read engine, not LLM |
| APP-066 | related — engine `awaiting` vs app creation step sync |

## Notes

- Footer `Awaiting:` in narration remains code-owned (APP-007); badge is **duplicate signal for UI clarity**, not a second source of truth.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-036 --task creation-step-badge
python tmp/backlog/claim_ticket.py release APP-036 --done
```
