# Batch board

**Updated:** 2026-05-22
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-022 | P1 | tmp/backlog/runs/app-022-hint-enterdungeon-on-failed-setphasedelve | claim | — | — |
| APP-026 | P1 | tmp/backlog/runs/app-026-combat-attack-gating | claim | — | — |
| APP-034 | P2 | tmp/backlog/runs/app-034-log-tool-chain-on-api-errors | claim | — | — |

## Implementation waves

1. Parallel: APP-022, APP-026, APP-034

## Same-file note

All three touch `app/gm/orchestrator.py` — close lanes sequentially through Stage 7a.

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
