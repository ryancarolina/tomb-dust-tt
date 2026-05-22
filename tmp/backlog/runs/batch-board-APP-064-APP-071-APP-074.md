# Batch board

**Updated:** 2026-05-20  
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-064 | P1 | `tmp/backlog/runs/app-064-startup-save-prompt/` | **done** · commit `c8852f8` | — |
| APP-071 | P1 | `tmp/backlog/runs/app-071-friendly-load-no-save/` | **done** · commit `c8852f8` | — |
| APP-074 | P2 | `tmp/backlog/runs/app-074-remove-dead-step-prompt/` | **done** · commit `c8852f8` | — |

## Implementation waves (from schedule)

1. Parallel: APP-064, APP-071, APP-074 (no hard deps)

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
