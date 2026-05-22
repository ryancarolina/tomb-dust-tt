# Batch board

**Updated:** 2026-05-22
**Max parallel:** 3
**Status:** COMPLETE

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-032 | P1 | tmp/backlog/runs/app-032-400-retry-malformed-transcript | **complete** | — | `edc0617` |
| APP-036 | P1 | tmp/backlog/runs/app-036-creation-step-badge | **complete** | — | `b93ea71` |
| APP-060 | P1 | tmp/backlog/runs/app-060-auto-scroll-narration | **complete** | — | `da8772d` |

## Implementation waves (from schedule)

1. Parallel: APP-032, APP-036, APP-060

## Same-file note

APP-036 and APP-060 both touch `app/ui/app.py` — scroll wiring committed with APP-036; narration panel in APP-060 commit.

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
