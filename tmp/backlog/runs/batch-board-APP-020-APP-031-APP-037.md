# Batch board

**Updated:** 2026-05-22
**Max parallel:** 3
**Status:** COMPLETE

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-020 | P1 | tmp/backlog/runs/app-020-document-stuck-creation-recovery | **complete** | — | `1b45332` |
| APP-031 | P1 | tmp/backlog/runs/app-031-transcript-sanitize-orphan-tool-messages | **complete** | — | `1d390bf` |
| APP-037 | P1 | tmp/backlog/runs/app-037-block-map-travel-during-creation | **complete** | — | `70599c3` |

## Implementation waves (from schedule)

1. Parallel: APP-020, APP-031, APP-037

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
