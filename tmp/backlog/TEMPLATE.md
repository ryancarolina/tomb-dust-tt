# APP-XXX: Short imperative title

| Field | Value |
|-------|-------|
| **ID** | APP-XXX |
| **Type** | bug \| feature \| chore \| decision |
| **Priority** | P0 \| P1 \| P2 |
| **Status** | open \| in_progress \| done \| cancelled |
| **Domain spec** | [`app-example-spec.md`](../app-example-spec.md) |
| **Created** | YYYY-MM-DD |
| **Closed** | _(set when done)_ |

## Summary

One or two sentences: what is broken or what capability is missing, and why it matters.

## Acceptance criteria

- [ ] Observable outcome 1 (testable)
- [ ] Observable outcome 2
- [ ] Domain spec updated if behavior changed

## Expected files

Paths you expect to touch (add rows before editing if scope grows):

- `app/...`
- `tmp/app-...-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update the domain spec checklist / changelog in the linked spec.
3. If priority or cross-domain behavior changed, update [`app-master-spec.md`](../app-master-spec.md).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-XXX --task <kebab-name>
python tmp/backlog/claim_ticket.py release APP-XXX --done
```

Creates `tmp/.active-ticket.json` and optional `tmp/backlog/runs/APP-XXX-<task>/`.

## Notes

_Blockers, dependencies (e.g. APP-013 before APP-001), design choices, PR links._

## Dependencies _(optional)_

Hard block (Stage 4 impl cannot start until dependency ticket is **done**):

| Ticket | Relationship |
|--------|--------------|
| APP-002 | blocks this ticket |

Soft hint (orchestrator warning only):

| Ticket | Relationship |
|--------|--------------|
| APP-049 | may block (tests package) |

Dev-team `schedule` / `impl-check` read this table. Example: working `APP-001`, `APP-002`, `APP-004` together — if `APP-004` is blocked by `APP-002`, wave 1 implements 001+002; wave 2 implements 004 after 002 is released `done`.
