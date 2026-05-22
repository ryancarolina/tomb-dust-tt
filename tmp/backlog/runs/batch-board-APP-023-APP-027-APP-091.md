# Batch board

**Updated:** 2026-05-22
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-023 | P1 | tmp/backlog/runs/app-023-friendly-travel-av-grid | spec | — | — |
| APP-027 | P1 | tmp/backlog/runs/app-027-validate-monster-id-combat | spec | — | — |
| APP-091 | P1 | tmp/backlog/runs/app-091-map-hint-overlap-fix | spec | — | — |

## Implementation waves (from schedule)

1. Parallel: APP-023, APP-027, APP-091

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
