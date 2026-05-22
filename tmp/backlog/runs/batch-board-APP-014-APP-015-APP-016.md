# Batch board

**Updated:** 2026-05-20
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-014 | P1 | tmp/backlog/runs/app-014-setupnewgame-session-lifecycle | complete | — |
| APP-015 | P1 | tmp/backlog/runs/app-015-clear-creation-block-on-new-game | complete | — |
| APP-016 | P1 | tmp/backlog/runs/app-016-snapshot-engine-status-on-save | complete | — |

## Implementation waves (from schedule)

1. Parallel: APP-014, APP-015, APP-016

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
