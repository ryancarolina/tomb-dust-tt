# Batch board

**Updated:** 2026-05-21
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by |
|----|----------|------------|----------------|------------|
| APP-083 | P0 | tmp/backlog/runs/app-083-mechanical-truth-narration-gate | claim | — |
| APP-079 | P1 | tmp/backlog/runs/app-079-finish-reason-length-recovery | claim | — |
| APP-041 | P2 | tmp/backlog/runs/app-041-strip-status-tags-before-tts | claim | — |

## Implementation waves (from schedule)

1. Parallel: APP-083, APP-079, APP-041 (no hard deps)

## Notes

- APP-083 supersedes APP-078/082 flavor strips; Phase 1 creation first, phases 2–4 exploration/combat/economy.
- APP-079 coordinates with APP-083 retry loop (length failures trigger verify fail → retry).
- APP-041 downstream of narration compose (TTS payload).

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
