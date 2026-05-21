# Batch board

**Updated:** 2026-05-20
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-017 | P1 | tmp/backlog/runs/app-017-reconcile-empty-roster | research | — |
| APP-018 | P1 | tmp/backlog/runs/app-018-continue-creation-state | research | — |
| APP-019 | P1 | tmp/backlog/runs/app-019-surface-new-game-errors | research | — |

## Implementation waves (from schedule)

1. Parallel: APP-017, APP-018, APP-019

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
