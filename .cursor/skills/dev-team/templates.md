# Dev Team — Artifact Templates

Copy sections into **`tmp/backlog/runs/<APP-XXX>-<task-name>/`** files. Replace placeholders.

**Stage 0:** run `python tmp/backlog/claim_ticket.py APP-XXX --task <task-name>` before creating artifacts.

**Paths:** write only under `tmp/backlog/runs/<APP-XXX>-<task-name>/`. Never `.dev-team/` or out-of-tree pointers.

**Subagents:** each role is a Task dispatch from the orchestrator; every subagent writes a `reflection-*.md` before returning ([agents.md](agents.md)).

---

## batch-board

Orchestrator writes after `schedule` + `claim-batch` (one copy; link from each ticket `status.md`).

**Filename (required):** `tmp/backlog/runs/batch-board-<sorted-ticket-ids>.md`

- Include every ticket in the batch: `batch-board-APP-064-APP-071-APP-074.md`
- Sort IDs ascending (`APP-064` before `APP-071`)
- Single ticket: `batch-board-APP-066.md`
- Do **not** use dates or `-b` suffixes — ticket IDs are the batch identity
- After `claim-batch`, use the `batch_board` path from CLI JSON output

```markdown
# Batch board

**Updated:** <date>
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-001 | P0 | tmp/backlog/runs/... | research | — | — |
| APP-002 | P0 | tmp/backlog/runs/... | spec | — | — |
| APP-004 | P0 | tmp/backlog/runs/... | claim | APP-002 | — |

_Update **Pipeline stage** as each lane advances. Set **Commit** to hash after Stage 7a (one commit per row). Mark **complete** only when commit + `human-test-plan.md` exist for that ID._

## Implementation waves (from schedule)

1. Parallel: APP-001, APP-002
2. Parallel: APP-004 (after APP-002 done)

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
```

---

## reflection

Every Research / PM / Dev / QA subagent writes one reflection file **before returning**.

Naming: `reflection-<role>.md` · revisions: `reflection-pm-r2.md` · streams: `reflection-dev-impl-ws1.md` · QA: `reflection-qa-spec.md`, `reflection-qa-plan-r2.md`, etc.

```markdown
# Reflection: <Role> — <APP-XXX> <stage>

**Agent:** Research | PM | Dev | QA
**Round:** 1 | 2 | 3 (if applicable)
**Deliverables:** <files written>

## Completed

- …

## Self-critique

- What might be wrong or thin in my work?
- What did I assume without verifying?

## Did I miss anything?

- [ ] Ticket scope / Expected files
- [ ] Domain spec / registry_gap / AGENTS.md
- [ ] Code paths not traced
- [ ] Tests or AC not mapped
- [ ] …

## Handoff

**Ready for:** <next role / gate>
**Escalate human if:** <condition or none>
```

---

## status.md

```markdown
# Pipeline: <APP-XXX>-<task-name>

**Goal:** <one line>
**Backlog ticket:** [APP-XXX](../../app-xxx-slug.md)
**Domain spec:** [app-example-spec.md](../../app-example-spec.md)
**Run folder:** tmp/backlog/runs/<APP-XXX>-<task-name>/
**Batch board:** [batch-board-APP-XXX-APP-YYY.md](../batch-board-APP-XXX-APP-YYY.md)
**Started:** <date>
**Current stage:** claim | research | spec | plan | implement | impl-qa | drift | commit | playtest | complete | blocked

## Checklist

- [ ] Stage 0 — ticket claimed (`tmp/.active-ticket.json`, ticket `in_progress`)
- [ ] Research → research-brief.md + reflection-research.md (dispatched)
- [ ] PM spec draft + reflection-pm.md (dispatched)
- [ ] QA spec PASS (round __/3) + reflection-qa-spec.md (dispatched)
- [ ] Dev plan + reflection-dev-plan.md (dispatched)
- [ ] QA plan PASS (round __/3) + reflection-qa-plan.md (dispatched)
- [ ] workstreams + parallel impl (each stream: reflection-dev-impl-*)
- [ ] QA implementation PASS + reflection-qa-impl.md (dispatched)
- [ ] Stage 6 — drift check + ticket release (`claim_ticket.py release APP-XXX --done`)
- [ ] Stage 6 — drift + release `--done` (this ticket only)
- [ ] Stage 7 — git commit **this APP-XXX only** (hash: ______)
- [ ] Stage 7 — human-test-plan.md (this run folder only)
- [ ] Batch board row updated (if multi-ticket)

## Blockers

_None._

## Links

- Ticket: ../../app-xxx-slug.md
- research-brief.md
- spec.md
- plan.md
- human-test-plan.md
```

---

## research-brief.md

```markdown
# Research Brief: <APP-XXX>-<task-name>

**Date:** <date>
**Question:** <what we need to answer>

**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**domain_spec:** tmp/app-example-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false | true

## Registry gap justification

<If false: cite ticket domain spec + app-master-spec registry row.>
<If true: why no row fits; proposed domain spec path.>

## Summary

<3–6 sentences>

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| | | |

## Code-path traces

### <flow name>

1. Entry: `path:symbol`
2. …
3. Exit / persistence: …

## Existing specs & docs

- Ticket domain spec: …
- …

## Tests & commands

```bash
# commands that exercise this area
```

## Risks & unknowns

- …

## Raw notes

<grep hits, edge cases, links>
```

---

## spec.md (run-local)

```markdown
# Spec: <APP-XXX>-<task-name>

**Status:** draft | qa-review | approved
**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**domain_spec:** tmp/app-example-spec.md
**registry_gap:** <echo from research-brief; PM may correct with note>
**Domain specs touched:** <paths or none>

## Proposed domain spec

_Fill only when `registry_gap: true`. Delete section when false._

| Field | Value |
|-------|--------|
| Proposed file | `tmp/app-<domain>-spec.md` or `build/docs/engine-integration.md` (canon only) |
| Registry row | <domain name — added to app-master-spec on create> |
| Owns | <code paths — must ⊆ ticket Expected files> |
| Why not existing owner | <which rows were ruled out> |

## Problem

…

## Goals

- …

## Non-goals

- …

## Requirements

### R1: …

**Acceptance criteria**

- [ ] …

## Test plan

```bash
pytest …
```

## Human playtest hints (for Stage 7)

_Bullet list of in-game scenarios QA will expand into `human-test-plan.md` (PyGame client, not headless only)._

- …

## Affected paths

_Must match or subset of ticket **Expected files**._

- …

## Changelog

| Date | Change |
|------|--------|
| | Initial draft |
```

---

## qa-spec-report-N.md / qa-plan-report-N.md

```markdown
# QA Report: <spec|plan> — round <N>

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** …
- **Issue:** …
- **Implementation gap:** …
- **Suggested fix:** …

### TICKET-001 — blocker _(spec/plan stages)_

- **Issue:** Missing/invalid backlog ticket, wrong domain spec, or plan file not in ticket Expected files
- **Suggested fix:** …

## Summary

<what must change before PASS>

## Re-review focus

- …
```

---

## qa-spec-pass.md / qa-plan-pass.md

```markdown
# QA PASS: <spec|plan>

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**Round:** <N>
**domain_spec_creation:** approved | not_needed | rejected

**Verified:**

- [ ] Backlog ticket valid; status `open` or `in_progress`
- [ ] Ticket domain spec matches spec updates
- [ ] Acceptance criteria testable
- [ ] Code traces match repo (plan only)
- [ ] AGENTS.md / canon compliance
- [ ] Tests/commands listed
- [ ] Plan files ⊆ ticket Expected files (plan only)
- [ ] registry_gap matches reality (spec only)
- [ ] If registry_gap true: domain spec exists or approved § Proposed domain spec (spec only)

**Notes:** <optional>
```

---

## New domain spec (after QA approved)

Create `tmp/app-<domain>-spec.md` with sections from [app-master-spec.md](../../tmp/app-master-spec.md) § Domain spec template, then add registry row:

```markdown
| <Domain name> | [`app-<domain>-spec.md`](app-<domain>-spec.md) | `<owned app paths>` | `<engine/canon links>` |
```

Also create matching backlog ticket if ongoing work remains.

---

## plan.md

```markdown
# Implementation Plan: <APP-XXX>-<task-name>

**Status:** draft | qa-review | approved
**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**domain_spec:** tmp/app-example-spec.md
**Spec:** spec.md (+ links)

## Approach

<short architecture>

## Code-path traces (planned)

### Change: <title>

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | | |

## Task breakdown

1. …

## Files (must ⊆ ticket Expected files)

- …

## Tests

| Step | Command | Expected |
|------|---------|----------|
| | | |

## Rollback / flags

…

## Open questions

- …
```

---

## workstreams.md

```markdown
# Workstreams: <APP-XXX>-<task-name>

**backlog_ticket:** APP-XXX

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | | — | | tests green |
| WS2 | | WS1? | | |

## WS1 — <name>

**Scope:** …
**Prompt seed for Task subagent:** Must include `backlog_ticket: APP-XXX`, ticket path, run-folder paths, AGENTS.md constraints …
```

---

## qa-implementation-report.md

```markdown
# QA Report: Implementation

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**Verdict:** FAIL

## Findings

### IMPL-001 — blocker

- **Location:** `file:line`
- **Issue:** …
- **Spec/plan/ticket reference:** …
- **Suggested fix:** …

## Tests run

| Command | Result |
|---------|--------|
| | pass/fail |
```

---

## qa-implementation-pass.md

```markdown
# QA PASS: Implementation

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**Tests run:** …
**Diff scope reviewed:** …
**Ticket AC:** all checked / noted exceptions
```

---

## drift-check.md

```markdown
# Drift Check: <APP-XXX>-<task-name>

**backlog_ticket:** APP-XXX
**Verdict:** PASS | UPDATED

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| | no | — |
| | yes | updated §… changelog entry |

## Ticket close

- [ ] Ticket acceptance criteria checked in ticket file
- [ ] `python tmp/backlog/claim_ticket.py release APP-XXX --done`
- [ ] `tmp/.active-ticket.json` cleared

## Notes

…
```

---

## human-test-plan.md

_Manual playtest for the human after Stage 7 commit. Not a substitute for pytest — both matter._

```markdown
# Human Playtest Plan: <APP-XXX>-<task-name>

**backlog_ticket:** APP-XXX
**Commit:** `<git rev or "pending">`
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] API keys / config the feature needs (or document "mock/offline OK")
- [ ] Fresh or known save state (e.g. `new game` vs Continue)
- [ ] Any log path to watch: `app/logs/session-YYYY-MM-DD.jsonl`

## Test cases

### TC-1: <short name> (maps to AC / R1)

**Goal:** <what behavior this proves>

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch app (`python main.py`) | Window opens, no traceback | [ ] |
| 2 | … | … | [ ] |

**Failure signals:** <wrong UI, silent no-op, wrong log event, crash>

### TC-2: <edge or regression case>

…

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

<flaky steps, known limitations>
```
