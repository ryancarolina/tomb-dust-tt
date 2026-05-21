# Batch board

**Updated:** 2026-05-21
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-024 | P1 | tmp/backlog/runs/app-024-block-site-fiction | research | — |
| APP-028 | P1 | tmp/backlog/runs/app-028-combat-failure-narration | research | — |
| APP-080 | P1 | tmp/backlog/runs/app-080-normalize-tool-args | research | — |

## Implementation waves (from schedule)

1. Parallel: APP-024, APP-028, APP-080 (no cross-ticket deps)

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
