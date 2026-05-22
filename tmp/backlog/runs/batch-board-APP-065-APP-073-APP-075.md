# Batch board

**Updated:** 2026-05-20
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-073 | P1 | tmp/backlog/runs/app-073-strip-llm-embedded-status-tags-in-creation | research | — |
| APP-065 | P1 | tmp/backlog/runs/app-065-suggestion-chips-no-stale-tokens | research | — |
| APP-075 | P1 | tmp/backlog/runs/app-075-skills-parse-aliases-and-error-flavor | research | — |

## Implementation waves (from schedule)

1. Parallel: APP-065, APP-073, APP-075 (prefer APP-073 before APP-065 at impl if both touch creation UX)

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
