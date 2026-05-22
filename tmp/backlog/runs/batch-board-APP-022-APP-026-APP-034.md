# Batch board

**Updated:** 2026-05-22
**Max parallel:** 3
**Status:** COMPLETE

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-022 | P1 | tmp/backlog/runs/app-022-hint-enterdungeon-on-failed-setphasedelve | **complete** | — | `e8f6cc5` |
| APP-026 | P1 | tmp/backlog/runs/app-026-combat-attack-gating | **complete** | — | `9227064` |
| APP-034 | P2 | tmp/backlog/runs/app-034-log-tool-chain-on-api-errors | **complete** | — | `8606d5d` |

## Implementation waves

1. Parallel: APP-022, APP-026, APP-034

## Same-file note

All three touched `app/gm/orchestrator.py` — orchestrator changes committed under APP-022; APP-026/034 commits are tests + logger + specs.

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
