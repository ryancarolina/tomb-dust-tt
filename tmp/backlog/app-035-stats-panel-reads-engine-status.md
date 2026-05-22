# APP-035: Stats panel reads engine status

| Field | Value |
|-------|-------|
| **ID** | APP-035 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Right-sidebar stats panel trusts LLM `[Phase: …]` / narration tags instead of **`GameBridge.status()`**. After [APP-062](app-062-left-character-panel-inventory-spells-tabs.md) adds a left column, stats must still reflect **engine truth** on every turn refresh.

## Acceptance criteria

- [x] Stats panel (HP, phase badge, location, gold, etc.) reads from engine `status()` each turn — not parsed from narration text.
- [x] Ignore LLM-emitted `[Phase: …]` / `[Location: …]` for stats display (narration panel may still show raw footers until APP-077).
- [x] Refresh cadence matches existing `status` UI queue event (same as APP-062 panel refresh).
- [x] Window layout compatible with three-column shell (APP-062 left panel + narration + right sidebar).

## Expected files

- `app/ui/panels/stats.py`
- `app/ui/panels/sidebar.py`
- `app/ui/app.py`
- `tmp/app-pygame-ui-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update domain spec + changelog.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-062 | **Schedule together** — left panel changes window geometry; stats stay on right sidebar |
| APP-077 | related — exploration footer still LLM until code-owned; stats must not follow LLM footer |
| APP-036 | related — creation step badge uses `creation_state`, not narration |

## Notes

- `StatsPanel.update_from_status()` in `app/ui/panels/stats.py`; fed via `("status", …)` UI queue from `app/ui/app.py` after each turn.
- Spell list footnote in stats remains until APP-062 Spells tab ships (see APP-062 AC).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-035 --task stats-engine-status
python tmp/backlog/claim_ticket.py release APP-035 --done
```
