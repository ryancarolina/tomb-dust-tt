# Batch board

**Updated:** 2026-05-20  
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-069 | P0 | `tmp/backlog/runs/app-069-creation-narration-match-fsm/` | Dev plan ✅ · QA plan ✅ | — |
| APP-070 | P0 | `tmp/backlog/runs/app-070-block-premature-pre-delve/` | Dev plan | — |
| APP-072 | P1 | `tmp/backlog/runs/app-072-llm-truncation-race-tables/` | Dev plan | — |

## Implementation waves (from schedule)

1. Parallel: APP-069, APP-070, APP-072 (no hard deps)

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
