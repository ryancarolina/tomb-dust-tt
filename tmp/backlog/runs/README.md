# Dev-team pipeline runs

Each **claimed** backlog ticket may have a run folder here:

```text
tmp/backlog/runs/APP-006-deterministic-creation-tables/
  status.md
  research-brief.md
  spec.md
  plan.md
  qa-*.md
  drift-check.md
```

## Create a run folder

```bash
python tmp/backlog/claim_ticket.py APP-006 --task deterministic-creation-tables
```

This sets `tmp/.active-ticket.json`, marks the ticket `in_progress`, and creates the run directory.

## Rules

- One ticket → one active run folder (linked in ticket **Notes**).
- All dev-team artifacts live **inside** the run folder — not loose under `tmp/`.
- **Never** `.dev-team/` at repo root — use this run folder only (see dev-team SKILL § Forbidden artifact paths).
- On pipeline **COMPLETE**, release the ticket: `python tmp/backlog/claim_ticket.py release APP-006 --done`

See [`.cursor/skills/dev-team/SKILL.md`](../../.cursor/skills/dev-team/SKILL.md) Stage 0.

**Agents:** orchestrator dispatches Research / PM / Dev / QA as Task subagents; each writes `reflection-*.md` before returning.

**Batch board:** `batch-board-APP-XXX-APP-YYY.md` at `runs/` root (ticket IDs in filename, sorted) — not date-only names.

**Parallel batch:** Stages 1–3 may run in parallel (one subagent per ticket). Stage 4 by `impl_waves`. Stages 6–7 **per ticket** — **one commit per APP-XXX**, never a combined batch commit.
