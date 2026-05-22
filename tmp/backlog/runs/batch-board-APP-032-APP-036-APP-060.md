# Batch board

**Updated:** 2026-05-22
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-032 | P1 | tmp/backlog/runs/app-032-400-retry-malformed-transcript | spec | — | — |
| APP-036 | P1 | tmp/backlog/runs/app-036-creation-step-badge | spec | — | — |
| APP-060 | P1 | tmp/backlog/runs/app-060-auto-scroll-narration | spec | — | — |

## Implementation waves (from schedule)

1. Parallel: APP-032, APP-036, APP-060

## Same-file note

APP-036 and APP-060 both touch `app/ui/app.py` — close lanes sequentially through Stage 7a.

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
